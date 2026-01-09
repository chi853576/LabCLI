"""
Reset Demo - Recreate clean backup for demos
This script removes old store and creates a fresh backup
"""

import os
import sys
import shutil


def reset_demo(store_path="store", dataset_path="dataset"):
    """Reset demo by recreating clean backup"""
    
    print("\n" + "=" * 70)
    print("  RESET DEMO - Recreate Clean Backup")
    print("=" * 70)
    
    # 1. Remove old store
    if os.path.exists(store_path):
        print(f"\n🗑️  Removing old store: {store_path}/")
        try:
            shutil.rmtree(store_path)
            print(f"   ✓ Removed")
        except Exception as e:
            print(f"   ❌ Error removing store: {e}")
            return False
    else:
        print(f"\n⚠️  Store not found: {store_path}/ (will create new)")
    
    # 2. Check dataset exists
    if not os.path.exists(dataset_path):
        print(f"\n❌ Error: Dataset not found: {dataset_path}/")
        print(f"\nPlease create dataset first:")
        print(f"  python scripts/generate_test_data.py")
        return False
    
    # 3. Initialize new store
    print(f"\n🔧 Initializing new store...")
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from src.cli.commands import cmd_init
        cmd_init(store_path)
        print(f"   ✓ Store initialized at {store_path}/")
    except Exception as e:
        print(f"   ❌ Error initializing store: {e}")
        return False
    
    # 4. Create new backup
    print(f"\n📦 Creating new backup from {dataset_path}/...")
    try:
        from src.cli.commands import cmd_backup
        from src.core.snapshot import list_snapshots
        
        cmd_backup(store_path, dataset_path, "Clean backup")
        
        # Get the snapshot ID from list_snapshots
        snapshots = list_snapshots(store_path)
        if not snapshots:
            print(f"   ❌ Error: No snapshots found after backup")
            return False
        
        snapshot_id = snapshots[-1].id  # Get latest snapshot
        print(f"   ✓ Backup created: {snapshot_id}")
    except Exception as e:
        print(f"   ❌ Error creating backup: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Verify backup
    print(f"\n🔍 Verifying backup...")
    try:
        from src.cli.commands import cmd_verify
        cmd_verify(store_path, snapshot_id)
        print(f"   ✓ Verification: PASSED")
    except Exception as e:
        print(f"   ❌ Verification: FAILED - {e}")
        return False
    
    # 6. Show result
    print("\n" + "=" * 70)
    print("  ✅ RESET COMPLETE")
    print("=" * 70)
    print(f"\nStore: {store_path}/")
    print(f"Snapshot ID: {snapshot_id}")
    print(f"\nYou can now run demos:")
    print(f"  Demo 2: python scripts/corrupt_chunk.py {store_path}/")
    print(f"  Demo 3: python scripts/corrupt_manifest.py {store_path}/")
    print(f"  Then verify: python -m src.cli.main verify {snapshot_id} --store {store_path}/")
    print("=" * 70)
    
    return True


def main():
    """Main function"""
    # Get paths from command line or use defaults
    store_path = sys.argv[1] if len(sys.argv) > 1 else "store"
    dataset_path = sys.argv[2] if len(sys.argv) > 2 else "dataset"
    
    print(f"Store path: {store_path}")
    print(f"Dataset path: {dataset_path}")
    
    # Reset demo
    success = reset_demo(store_path, dataset_path)
    
    if success:
        print(f"\n✅ Reset successful!")
        return 0
    else:
        print(f"\n❌ Reset failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
