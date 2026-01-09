"""
Demo 2: Chunk Corruption Detection

Kịch bản:
1. Tạo backup
2. Sửa 1 byte trong một chunk file
3. Chạy verify → phải FAIL (phát hiện corruption)

Kết quả mong đợi: Verify phát hiện chunk bị corrupt
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli.commands import cmd_init, cmd_backup, cmd_verify
from src.core.snapshot import list_snapshots


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print("=" * 80)
    print("DEMO 2: Chunk Corruption Detection")
    print("=" * 80)
    
    store_path = "store"
    dataset_path = "dataset"
    
    # Check prerequisites
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found at {dataset_path}")
        print("Please run: python scripts/generate_test_data.py")
        return 1
    
    if not os.path.exists(store_path):
        print(f"❌ Store not found at {store_path}")
        print("Please run: python -m src.cli.main init --store {store_path}")
        return 1
    
    try:
        # Step 1: Create backup if needed
        print_section("STEP 1: Ensure Backup Exists")
        
        snapshots = list_snapshots(store_path)
        if not snapshots:
            print("No snapshots found. Creating backup...")
            cmd_backup(store_path, dataset_path, "Demo 2: Chunk corruption test")
            snapshots = list_snapshots(store_path)
        
        snapshot_id = snapshots[-1].id
        print(f"✅ Using snapshot: {snapshot_id}")
        
        # Step 2: Verify snapshot is OK before corruption
        print_section("STEP 2: Verify Snapshot (Before Corruption)")
        
        print("Running verify...")
        try:
            cmd_verify(store_path, snapshot_id)
            print("✅ Snapshot is valid (before corruption)")
        except Exception as e:
            print(f"❌ Unexpected: Snapshot verification failed before corruption: {e}")
            return 1
        
        # Step 3: Corrupt a chunk
        print_section("STEP 3: Corrupt a Chunk File")
        
        chunks_dir = os.path.join(store_path, "chunks")
        chunk_file = None
        
        # Find first chunk file
        for root, dirs, files in os.walk(chunks_dir):
            if files:
                chunk_file = os.path.join(root, files[0])
                break
        
        if not chunk_file:
            print("❌ No chunk files found!")
            return 1
        
        chunk_name = os.path.basename(chunk_file)
        print(f"📁 Target chunk: {chunk_name}")
        
        # Read original
        with open(chunk_file, 'rb') as f:
            original_data = f.read()
        
        print(f"   Original size: {len(original_data)} bytes")
        print(f"   First 16 bytes: {original_data[:16].hex()}")
        
        # Corrupt the chunk (flip first bit of first byte)
        corrupted_data = bytes([original_data[0] ^ 1]) + original_data[1:]
        
        with open(chunk_file, 'wb') as f:
            f.write(corrupted_data)
        
        print(f"✅ Corrupted chunk: flipped 1 bit in first byte")
        print(f"   Corrupted first 16 bytes: {corrupted_data[:16].hex()}")
        
        # Step 4: Verify should FAIL
        print_section("STEP 4: Verify Snapshot (After Corruption)")
        
        print("Running verify...")
        print("Expected: Verification should FAIL due to chunk corruption")
        
        try:
            cmd_verify(store_path, snapshot_id)
            print("❌ UNEXPECTED: Verification passed! Corruption was not detected!")
            
            # Restore chunk
            with open(chunk_file, 'wb') as f:
                f.write(original_data)
            
            return 1
            
        except Exception as e:
            error_msg = str(e)
            if "integrity" in error_msg.lower() or "hash" in error_msg.lower() or "mismatch" in error_msg.lower():
                print(f"✅ Verification FAILED as expected!")
                print(f"   Error: {error_msg}")
            else:
                print(f"⚠️  Verification failed, but with unexpected error:")
                print(f"   Error: {error_msg}")
        
        # Step 5: Restore chunk and verify again
        print_section("STEP 5: Restore Chunk and Re-verify")
        
        print("Restoring original chunk...")
        with open(chunk_file, 'wb') as f:
            f.write(original_data)
        
        print("✅ Chunk restored")
        
        print("\nRunning verify again...")
        try:
            cmd_verify(store_path, snapshot_id)
            print("✅ Verification passed after restoration!")
        except Exception as e:
            print(f"❌ Unexpected: Verification still fails: {e}")
            return 1
        
        # Success
        print_section("DEMO 2 COMPLETE - SUCCESS")
        print(f"✅ Snapshot verified successfully (before corruption)")
        print(f"✅ Chunk corrupted (1 bit flipped)")
        print(f"✅ Verification detected corruption (FAIL)")
        print(f"✅ Chunk restored")
        print(f"✅ Verification passed again")
        print("\n🎉 Chunk corruption detection working correctly!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
