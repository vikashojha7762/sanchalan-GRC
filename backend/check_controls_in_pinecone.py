"""
Script to check if ISO 27001 controls are indexed in Pinecone knowledge base.

Usage:
    python check_controls_in_pinecone.py
"""
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.db import SessionLocal
from app.models import Control, Framework, ControlGroup
from app.services.pinecone_service import get_index, query_similar_policies


def check_controls_in_pinecone():
    """
    Check if controls are indexed in Pinecone by:
    1. Querying Pinecone for control-type vectors
    2. Testing a sample query
    3. Comparing database controls with Pinecone
    """
    db = SessionLocal()
    
    try:
        print(f"\n{'='*60}")
        print(f"Checking Controls in Pinecone Knowledge Base")
        print(f"{'='*60}\n")
        
        # Step 1: Get framework and controls from database
        framework = db.query(Framework).filter(
            Framework.name.ilike("%ISO 27001%")
        ).first()
        
        if not framework:
            print("✗ ISO 27001 framework not found in database")
            return
        
        print(f"✓ Framework found: {framework.name} (ID: {framework.id})\n")
        
        # Get all controls from database
        controls = db.query(Control).join(
            ControlGroup, Control.control_group_id == ControlGroup.id
        ).filter(
            ControlGroup.framework_id == framework.id,
            Control.is_active == True
        ).all()
        
        print(f"Database Controls:")
        print(f"  Total controls in database: {len(controls)}")
        
        # Group by control group
        control_groups = {}
        for control in controls:
            group_code = control.control_group.code if control.control_group else "Unknown"
            if group_code not in control_groups:
                control_groups[group_code] = []
            control_groups[group_code].append(control)
        
        print(f"  Control groups: {list(control_groups.keys())}")
        for group_code, group_controls in control_groups.items():
            print(f"    - {group_code}: {len(group_controls)} controls")
        
        print(f"\n{'='*60}")
        print(f"Checking Pinecone Index")
        print(f"{'='*60}\n")
        
        # Step 2: Get Pinecone index stats
        try:
            index = get_index()
            stats = index.describe_index_stats()
            
            print(f"Pinecone Index Stats:")
            print(f"  Total vectors: {stats.total_vector_count}")
            print(f"  Dimension: {stats.dimension}")
            print(f"  Namespaces: {list(stats.namespaces.keys()) if stats.namespaces else ['default']}")
            
        except Exception as e:
            print(f"✗ Error connecting to Pinecone: {str(e)}")
            return
        
        # Step 3: Test querying for controls
        print(f"\n{'='*60}")
        print(f"Testing Control Queries")
        print(f"{'='*60}\n")
        
        # Test with a sample control query
        test_queries = [
            "A.5.1 Policies for information security",
            "A.6.1 Screening",
            "A.7.1 Physical security perimeters",
            "A.8.1 User endpoint devices"
        ]
        
        controls_found = 0
        controls_not_found = []
        
        for test_query in test_queries:
            print(f"Testing query: '{test_query}'")
            try:
                # Query without company filter to find controls (controls don't have company_id)
                results = query_similar_policies(
                    query_text=test_query,
                    top_k=5,
                    filter_metadata=None,  # No filter to find controls
                    similarity_threshold=0.5  # Lower threshold for testing
                )
                
                # Check if any result is a control
                control_results = [r for r in results if r.get("type") == "control"]
                
                if control_results:
                    controls_found += 1
                    print(f"  ✓ Found {len(control_results)} control(s)")
                    for result in control_results[:2]:  # Show first 2
                        print(f"    - {result.get('control_code')}: {result.get('title')} (score: {result.get('score', 0):.3f})")
                else:
                    controls_not_found.append(test_query)
                    print(f"  ✗ No controls found")
                    
            except Exception as e:
                print(f"  ✗ Error querying: {str(e)}")
                controls_not_found.append(test_query)
        
        # Step 4: Try to fetch control vectors directly by ID pattern
        print(f"\n{'='*60}")
        print(f"Checking Control Vectors by ID Pattern")
        print(f"{'='*60}\n")
        
        # Sample a few controls and check if their vectors exist
        sample_controls = controls[:10]  # Check first 10 controls
        vectors_found = 0
        vectors_missing = []
        
        for control in sample_controls:
            vector_id = f"control_{control.id}"
            try:
                # Try to fetch the vector (Pinecone fetch API)
                fetch_result = index.fetch(ids=[vector_id])
                if vector_id in fetch_result.vectors:
                    vectors_found += 1
                    metadata = fetch_result.vectors[vector_id].metadata
                    control_type = metadata.get("type", "unknown") if metadata else "unknown"
                    print(f"  ✓ Control {control.code} (ID: {control.id}) - Vector exists (type: {control_type})")
                else:
                    vectors_missing.append(control.code)
                    print(f"  ✗ Control {control.code} (ID: {control.id}) - Vector NOT found")
            except Exception as e:
                vectors_missing.append(control.code)
                print(f"  ✗ Control {control.code} (ID: {control.id}) - Error: {str(e)}")
        
        # Step 5: Summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")
        print(f"Database:")
        print(f"  Total controls: {len(controls)}")
        print(f"  Control groups: {len(control_groups)}")
        
        print(f"\nPinecone:")
        print(f"  Total vectors: {stats.total_vector_count}")
        print(f"  Control queries successful: {controls_found}/{len(test_queries)}")
        print(f"  Sample vectors found: {vectors_found}/{len(sample_controls)}")
        
        if vectors_found == 0 and controls_found == 0:
            print(f"\n⚠️  WARNING: No controls found in Pinecone!")
            print(f"   Controls are NOT indexed. Run: python seed_controls_to_pinecone.py")
        elif vectors_found < len(sample_controls):
            print(f"\n⚠️  PARTIAL: Some controls are indexed, but not all.")
            print(f"   Missing controls: {vectors_missing[:5]}")
            print(f"   Run: python seed_controls_to_pinecone.py to index all controls")
        else:
            print(f"\n✓ Controls appear to be indexed in Pinecone!")
            print(f"   You can test with the AI chat assistant.")
        
        print(f"{'='*60}\n")
        
    except Exception as e:
        import traceback
        print(f"\n✗✗✗ ERROR: {str(e)}")
        print(f"Traceback:\n{traceback.format_exc()}")
    finally:
        db.close()


if __name__ == "__main__":
    check_controls_in_pinecone()

