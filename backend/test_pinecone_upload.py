"""
Test script to manually upload a vector to Pinecone to verify it works.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.pinecone_service import get_index, index_policy_embedding
from app.services.ai_service import get_embedding

def test_manual_upload():
    """Manually upload a test vector to Pinecone."""
    print("\n" + "="*80)
    print("TEST: Manual Pinecone Upload")
    print("="*80 + "\n")
    
    try:
        # Get index
        index = get_index()
        print("✓ Index retrieved\n")
        
        # Create a test embedding
        test_text = "This is a test policy document for Pinecone vector database storage verification."
        print(f"Test text: {test_text}")
        embedding = get_embedding(test_text)
        print(f"✓ Embedding generated: {len(embedding)} dimensions\n")
        
        # Prepare metadata
        test_metadata = {
            "policy_id": 9999,
            "title": "Test Policy",
            "content": test_text,
            "test": True
        }
        
        # Upsert directly
        vector_id = "test_policy_9999"
        print(f"Upserting vector ID: {vector_id}")
        print(f"Metadata: {list(test_metadata.keys())}\n")
        
        response = index.upsert(
            vectors=[{
                "id": vector_id,
                "values": embedding,
                "metadata": test_metadata
            }]
        )
        
        print(f"🔵 Pinecone Upsert Response: {response}")
        print(f"Response type: {type(response)}")
        print(f"Response attributes: {dir(response)}\n")
        
        # Check if it has upserted_count
        if hasattr(response, 'upserted_count'):
            print(f"✓ Upserted count: {response.upserted_count}")
        if hasattr(response, '__dict__'):
            print(f"Response dict: {response.__dict__}\n")
        
        # Verify by querying
        print("Verifying upload by querying...")
        query_result = index.query(
            vector=embedding,
            top_k=1,
            include_metadata=True,
            filter={"policy_id": {"$eq": 9999}}
        )
        
        print(f"Query results: {len(query_result.matches)} matches")
        if query_result.matches:
            match = query_result.matches[0]
            print(f"✓ Found vector: {match.id}")
            print(f"  Score: {match.score}")
            print(f"  Metadata: {match.metadata}\n")
        else:
            print("✗ No matches found - vector may not have been stored\n")
        
        # Get index stats
        print("Getting index stats...")
        stats = index.describe_index_stats()
        print(f"Total vectors: {stats.total_vector_count}")
        print(f"Dimension: {stats.dimension}\n")
        
        print("="*80)
        print("TEST COMPLETE")
        print("="*80 + "\n")
        
    except Exception as e:
        import traceback
        print(f"\n✗✗✗ ERROR: {str(e)} ✗✗✗")
        print(f"Traceback:\n{traceback.format_exc()}\n")

if __name__ == "__main__":
    test_manual_upload()

