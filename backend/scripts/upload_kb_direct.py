"""
Direct upload script - uploads knowledge base files directly using database and services.
No JWT token required - uses database directly.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import SessionLocal
from app.models import Framework, KnowledgeBaseDocument, KnowledgeSourceType
from app.utils.text_extraction import extract_text_from_file
from app.services.pinecone_service import get_index, chunk_text
from app.services.ai_service import get_embedding
import shutil

# Configuration
SOURCE_DIRECTORY = r"C:\Users\vikas\OneDrive\Desktop\Doc"
UPLOAD_DIR = Path("backend/uploads/knowledge_base")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Framework mapping
FRAMEWORK_MAPPING = {
    "iso 27001": 3,  # ISO 27001
    "iso27001": 3,
    "iso 14000": 3,  # Use ISO 27001 for ISO 14000
    "nist": 3,  # Use ISO 27001 for NIST
    "cobit": 3,
    "sox": 3,
    "pci": 3,
    "soc": 6,  # SOC 2 Type II
    "swift": 3,
    "gdpr": 4,  # GDPR
    "aadhaar": 3,
    "dpdp": 2,  # DPDP
}

SOURCE_TYPE_MAPPING = {
    "iso": "ISO",
    "nist": "NIST",
    "gdpr": "CUSTOM",
    "soc": "CUSTOM",
    "sox": "CUSTOM",
    "pci": "CUSTOM",
    "cobit": "CUSTOM",
    "swift": "CUSTOM",
    "aadhaar": "CUSTOM",
    "dpdp": "CUSTOM",
}


def get_framework_id_from_filename(filename: str, db) -> int:
    """Determine framework ID from filename."""
    filename_lower = filename.lower()
    
    for key, framework_id in FRAMEWORK_MAPPING.items():
        if key in filename_lower:
            return framework_id
    
    # Default to ISO 27001 (ID: 3)
    return 3


def get_source_type_from_filename(filename: str) -> str:
    """Determine source type from filename."""
    filename_lower = filename.lower()
    
    for key, source_type in SOURCE_TYPE_MAPPING.items():
        if key in filename_lower:
            return source_type
    
    return "CUSTOM"


def upload_file_direct(file_path: Path, db) -> dict:
    """Upload file directly to knowledge base using database."""
    filename = file_path.name
    print(f"\n{'='*60}")
    print(f"Processing: {filename}")
    print(f"{'='*60}")
    
    # Determine framework and source type
    framework_id = get_framework_id_from_filename(filename, db)
    source_type_str = get_source_type_from_filename(filename)
    
    # Get framework
    framework = db.query(Framework).filter(Framework.id == framework_id).first()
    if not framework:
        print(f"❌ Framework {framework_id} not found!")
        return {"error": f"Framework {framework_id} not found"}
    
    print(f"Framework: {framework.name} (ID: {framework_id})")
    
    # Validate source type
    try:
        source_type_enum = KnowledgeSourceType(source_type_str.upper())
    except ValueError:
        source_type_enum = KnowledgeSourceType.CUSTOM
        print(f"⚠️ Invalid source_type '{source_type_str}', using CUSTOM")
    
    print(f"Source Type: {source_type_enum.value}")
    
    # Clean title
    title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ').title()
    print(f"Title: {title}")
    
    # Extract text
    try:
        print(f"Extracting text from: {file_path}")
        raw_text = extract_text_from_file(str(file_path))
        print(f"✅ Text extracted: {len(raw_text)} characters")
    except Exception as e:
        print(f"❌ Error extracting text: {str(e)}")
        return {"error": f"Text extraction failed: {str(e)}"}
    
    # Copy file to knowledge base directory
    kb_file_path = UPLOAD_DIR / f"kb_{framework_id}_{filename}"
    try:
        shutil.copy2(file_path, kb_file_path)
        print(f"✅ File copied to: {kb_file_path}")
    except Exception as e:
        print(f"⚠️ Warning: Could not copy file: {str(e)}")
        kb_file_path = file_path
    
    # Create database record
    kb_doc = KnowledgeBaseDocument(
        framework_id=framework_id,
        title=title,
        source_type=source_type_enum,
        raw_text=raw_text,
        file_path=str(kb_file_path),
        is_active=True
    )
    db.add(kb_doc)
    db.commit()
    db.refresh(kb_doc)
    
    print(f"✅ Document saved to DB: ID={kb_doc.id}")
    
    # Chunk text (900 chars, 150 overlap)
    chunks = chunk_text(raw_text, chunk_size=900, overlap=150)
    print(f"✅ Text chunked into {len(chunks)} chunks")
    
    # Embed and index in Pinecone
    try:
        index = get_index()
        namespace = f"kb-{framework_id}"
        
        vectors_to_upsert = []
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding
                embedding = get_embedding(chunk)
                if not embedding:
                    print(f"⚠️ Skipping chunk {i} - embedding generation failed")
                    continue
                
                # Create vector ID
                vector_id = f"kb-{kb_doc.id}-{i}"
                
                # Metadata
                metadata = {
                    "kb_doc_id": kb_doc.id,
                    "framework_id": framework_id,
                    "title": title,
                    "source_type": source_type_enum.value,
                    "chunk_index": i,
                    "text": chunk[:1000]  # Store first 1000 chars in metadata
                }
                
                vectors_to_upsert.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
                
            except Exception as e:
                print(f"⚠️ Error processing chunk {i}: {str(e)}")
                continue
        
        # Upsert to Pinecone in batches
        if vectors_to_upsert:
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                index.upsert(vectors=batch, namespace=namespace)
                print(f"✅ Upserted batch {i//batch_size + 1} ({len(batch)} vectors) to namespace '{namespace}'")
            
            print(f"✅✅✅ Successfully indexed {len(vectors_to_upsert)} chunks in Pinecone namespace '{namespace}'")
        else:
            print(f"⚠️ No vectors to upsert")
        
        return {
            "success": True,
            "document_id": kb_doc.id,
            "title": title,
            "framework_id": framework_id,
            "chunks_indexed": len(vectors_to_upsert),
            "namespace": namespace
        }
        
    except Exception as e:
        print(f"❌ Error indexing in Pinecone: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": f"Pinecone indexing failed: {str(e)}"}


def main():
    """Main function to process all files in directory."""
    source_dir = Path(SOURCE_DIRECTORY)
    
    if not source_dir.exists():
        print(f"❌ Directory not found: {SOURCE_DIRECTORY}")
        return
    
    if not source_dir.is_dir():
        print(f"❌ Path is not a directory: {SOURCE_DIRECTORY}")
        return
    
    print(f"📁 Source Directory: {source_dir}")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Find all PDF files
        pdf_files = list(source_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"❌ No PDF files found in {source_dir}")
            return
        
        print(f"\n📄 Found {len(pdf_files)} PDF file(s)\n")
        
        # Process each file
        results = []
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
            result = upload_file_direct(pdf_file, db)
            results.append({
                "file": pdf_file.name,
                "result": result
            })
        
        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        successful = sum(1 for r in results if r["result"].get("success"))
        failed = len(results) - successful
        
        print(f"Total files: {len(results)}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        
        if successful > 0:
            print("\n✅ Successfully uploaded:")
            for r in results:
                if r["result"].get("success"):
                    print(f"  - {r['file']}: {r['result'].get('chunks_indexed', 0)} chunks indexed")
        
        if failed > 0:
            print("\n❌ Failed files:")
            for r in results:
                if not r["result"].get("success"):
                    print(f"  - {r['file']}: {r['result'].get('error', 'Unknown error')}")
    
    finally:
        db.close()
        print("\n✅ Done!")


if __name__ == "__main__":
    main()

