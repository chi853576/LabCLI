"""
Demo 1: Restore Integrity Test

Kịch bản:
1. Tạo dataset với nhiều files
2. Backup dataset
3. Xóa một số file từ source
4. Restore từ snapshot
5. So sánh kết quả (cây thư mục + nội dung file)

Kết quả mong đợi: Restored dataset giống hệt original
"""

import os
import sys
import shutil

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli.commands import cmd_init, cmd_backup, cmd_restore, scan_directory
from src.core.snapshot import list_snapshots


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def compare_directories(dir1, dir2):
    """Compare two directories and return differences"""
    files1 = sorted(scan_directory(dir1))
    files2 = sorted(scan_directory(dir2))
    
    # Get relative paths
    rel_files1 = {os.path.relpath(f, dir1): f for f in files1}
    rel_files2 = {os.path.relpath(f, dir2): f for f in files2}
    
    # Check file count
    if len(rel_files1) != len(rel_files2):
        print(f"❌ File count mismatch: {len(rel_files1)} vs {len(rel_files2)}")
        return False
    
    # Check file paths
    if set(rel_files1.keys()) != set(rel_files2.keys()):
        print(f"❌ Different files:")
        print(f"   Only in dir1: {set(rel_files1.keys()) - set(rel_files2.keys())}")
        print(f"   Only in dir2: {set(rel_files2.keys()) - set(rel_files1.keys())}")
        return False
    
    # Check file contents
    mismatches = 0
    for rel_path in rel_files1.keys():
        with open(rel_files1[rel_path], 'rb') as f1:
            with open(rel_files2[rel_path], 'rb') as f2:
                if f1.read() != f2.read():
                    print(f"❌ Content mismatch: {rel_path}")
                    mismatches += 1
    
    if mismatches > 0:
        return False
    
    return True


def main():
    print("=" * 80)
    print("DEMO 1: Restore Integrity Test")
    print("=" * 80)
    
    # Setup paths
    store_path = "store"
    dataset_path = "dataset"
    restore_path = "restored_dataset"
    
    # Check dataset exists
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found at {dataset_path}")
        print("Please run: python scripts/generate_test_data.py")
        return 1
    
    # Clean up previous restore
    if os.path.exists(restore_path):
        print(f"🧹 Cleaning up previous restore...")
        shutil.rmtree(restore_path)
    
    try:
        # Step 1: Show original dataset
        print_section("STEP 1: Original Dataset")
        original_files = scan_directory(dataset_path)
        print(f"📁 Total files: {len(original_files)}")
        
        # Save original file list and contents
        original_data = {}
        for file_path in original_files:
            rel_path = os.path.relpath(file_path, dataset_path)
            with open(file_path, 'rb') as f:
                original_data[rel_path] = f.read()
        
        print(f"📋 Sample files:")
        for i, rel_path in enumerate(sorted(original_data.keys())[:5]):
            size = len(original_data[rel_path])
            print(f"   {i+1}. {rel_path} ({size} bytes)")
        if len(original_data) > 5:
            print(f"   ... and {len(original_data) - 5} more files")
        
        # Step 2: Create backup
        print_section("STEP 2: Create Backup")
        
        if not os.path.exists(store_path):
            print("Initializing store...")
            cmd_init(store_path)
        
        print("Creating backup...")
        cmd_backup(store_path, dataset_path, "Demo 1: Restore integrity test")
        
        # Get snapshot ID
        snapshots = list_snapshots(store_path)
        snapshot_id = snapshots[-1].id  # Get latest
        print(f"✅ Backup created: {snapshot_id}")
        
        # Step 3: Simulate data loss (delete some files)
        print_section("STEP 3: Simulate Data Loss")
        
        print("⚠️  Simulating data loss by deleting entire dataset...")
        print(f"   (In real scenario, you might delete specific files)")
        
        # Actually delete the dataset
        shutil.rmtree(dataset_path)
        print(f"✅ Dataset deleted: {dataset_path}")
        
        # Step 4: Restore from backup
        print_section("STEP 4: Restore from Backup")
        
        print(f"Restoring snapshot: {snapshot_id}")
        cmd_restore(store_path, snapshot_id, restore_path)
        print(f"✅ Restored to: {restore_path}")
        
        # Step 5: Compare restored with original
        print_section("STEP 5: Verify Restored Data")
        
        restored_files = scan_directory(restore_path)
        print(f"📁 Restored files: {len(restored_files)}")
        
        # Load restored data
        restored_data = {}
        for file_path in restored_files:
            rel_path = os.path.relpath(file_path, restore_path)
            with open(file_path, 'rb') as f:
                restored_data[rel_path] = f.read()
        
        # Compare
        print("\n🔍 Comparing original vs restored...")
        
        # Check file count
        if len(original_data) != len(restored_data):
            print(f"❌ File count mismatch!")
            print(f"   Original: {len(original_data)} files")
            print(f"   Restored: {len(restored_data)} files")
            return 1
        
        print(f"✅ File count matches: {len(original_data)} files")
        
        # Check file paths
        if set(original_data.keys()) != set(restored_data.keys()):
            print(f"❌ File paths don't match!")
            only_original = set(original_data.keys()) - set(restored_data.keys())
            only_restored = set(restored_data.keys()) - set(original_data.keys())
            if only_original:
                print(f"   Only in original: {only_original}")
            if only_restored:
                print(f"   Only in restored: {only_restored}")
            return 1
        
        print(f"✅ File paths match")
        
        # Check file contents
        mismatches = 0
        for rel_path in original_data.keys():
            if original_data[rel_path] != restored_data[rel_path]:
                print(f"❌ Content mismatch: {rel_path}")
                mismatches += 1
        
        if mismatches > 0:
            print(f"❌ {mismatches} file(s) have different content!")
            return 1
        
        print(f"✅ All file contents match perfectly!")
        
        # Success
        print_section("DEMO 1 COMPLETE - SUCCESS")
        print(f"✅ Original dataset: {len(original_data)} files")
        print(f"✅ Backup created successfully")
        print(f"✅ Dataset deleted (simulated data loss)")
        print(f"✅ Restored from backup")
        print(f"✅ Restored data matches original 100%")
        print("\n🎉 Restore integrity verified!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
