"""
Demo 3: Manifest Corruption Detection

Kịch bản:
1. Tạo backup
2. Sửa manifest file (thay đổi chunk hash)
3. Chạy verify → phải FAIL (Merkle root mismatch)

Kết quả mong đợi: Verify phát hiện manifest bị corrupt
"""

import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli.commands import cmd_init, cmd_backup, cmd_verify
from src.core.snapshot import list_snapshots, load_snapshot


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print("=" * 80)
    print("DEMO 3: Manifest Corruption Detection")
    print("=" * 80)
    
    store_path = "store"
    dataset_path = "dataset"
    
    # Check prerequisites
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found at {dataset_path}")
        return 1
    
    if not os.path.exists(store_path):
        print(f"❌ Store not found at {store_path}")
        return 1
    
    try:
        # Step 1: Ensure backup exists
        print_section("STEP 1: Ensure Backup Exists")
        
        snapshots = list_snapshots(store_path)
        if not snapshots:
            print("Creating backup...")
            cmd_backup(store_path, dataset_path, "Demo 3: Manifest corruption test")
            snapshots = list_snapshots(store_path)
        
        snapshot = snapshots[-1]
        print(f"✅ Using snapshot: {snapshot.id}")
        print(f"   Manifest hash: {snapshot.manifest_hash[:16]}...")
        print(f"   Merkle root: {snapshot.merkle_root[:16]}...")
        
        # Step 2: Verify before corruption
        print_section("STEP 2: Verify Snapshot (Before Corruption)")
        
        try:
            cmd_verify(store_path, snapshot.id)
            print("✅ Snapshot is valid (before corruption)")
        except Exception as e:
            print(f"❌ Unexpected: Verification failed before corruption: {e}")
            return 1
        
        # Step 3: Corrupt manifest
        print_section("STEP 3: Corrupt Manifest File")
        
        manifest_path = os.path.join(store_path, "manifests", f"{snapshot.manifest_hash}.json")
        
        if not os.path.exists(manifest_path):
            print(f"❌ Manifest file not found: {manifest_path}")
            return 1
        
        print(f"📁 Manifest file: {os.path.basename(manifest_path)}")
        
        # Read original manifest
        with open(manifest_path, 'r', encoding='utf-8') as f:
            original_manifest = f.read()
            manifest_data = json.loads(original_manifest)
        
        print(f"   Files in manifest: {len(manifest_data['files'])}")
        
        if not manifest_data['files'] or not manifest_data['files'][0]['chunks']:
            print("❌ No chunks in manifest to corrupt!")
            return 1
        
        original_hash = manifest_data['files'][0]['chunks'][0]
        print(f"   Original first chunk hash: {original_hash[:16]}...")
        
        # Corrupt: flip last character of first chunk hash
        corrupted_hash = original_hash[:-1] + ('0' if original_hash[-1] != '0' else '1')
        manifest_data['files'][0]['chunks'][0] = corrupted_hash
        
        print(f"   Corrupted first chunk hash: {corrupted_hash[:16]}...")
        
        # Write corrupted manifest
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f)
        
        print(f"✅ Manifest corrupted: changed 1 character in chunk hash")
        
        # Step 4: Verify should FAIL
        print_section("STEP 4: Verify Snapshot (After Corruption)")
        
        print("Running verify...")
        print("Expected: Verification should FAIL due to Merkle root mismatch")
        
        try:
            cmd_verify(store_path, snapshot.id)
            print("❌ UNEXPECTED: Verification passed! Corruption was not detected!")
            
            # Restore manifest
            with open(manifest_path, 'w', encoding='utf-8') as f:
                f.write(original_manifest)
            
            return 1
            
        except Exception as e:
            error_msg = str(e)
            print(f"✅ Verification FAILED as expected!")
            print(f"   Error: {error_msg}")
        
        # Step 5: Restore manifest and verify again
        print_section("STEP 5: Restore Manifest and Re-verify")
        
        print("Restoring original manifest...")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            f.write(original_manifest)
        
        print("✅ Manifest restored")
        
        print("\nRunning verify again...")
        try:
            cmd_verify(store_path, snapshot.id)
            print("✅ Verification passed after restoration!")
        except Exception as e:
            print(f"❌ Unexpected: Verification still fails: {e}")
            return 1
        
        # Success
        print_section("DEMO 3 COMPLETE - SUCCESS")
        print(f"✅ Snapshot verified successfully (before corruption)")
        print(f"✅ Manifest corrupted (chunk hash modified)")
        print(f"✅ Verification detected corruption (Merkle root mismatch)")
        print(f"✅ Manifest restored")
        print(f"✅ Verification passed again")
        print("\n🎉 Manifest corruption detection working correctly!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
