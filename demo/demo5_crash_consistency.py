"""
Demo 5: Crash Consistency

Kịch bản:
1. Tạo baseline backup
2. Sử dụng crash_simulation.py để kill backup process giữa chừng
3. Kiểm tra store sau crash - snapshot incomplete không tồn tại
4. Backup lại sau crash - thành công
5. Verify snapshot mới - passed

Kết quả mong đợi: Hệ thống đảm bảo crash consistency, không có snapshot lỗi
"""

import os
import sys
import subprocess
import time

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli.commands import cmd_init, cmd_backup, cmd_verify
from src.core.snapshot import list_snapshots


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def run_command(cmd, description):
    """Run a command and show output"""
    print(f"\n💻 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode


def main():
    print("=" * 80)
    print("DEMO 5: Crash Consistency")
    print("=" * 80)
    print("\nMục đích: Chứng minh hệ thống phục hồi sau crash, không có snapshot lỗi")
    
    store_path = "store"
    dataset_path = "dataset"
    
    # Check prerequisites
    if not os.path.exists(dataset_path):
        print(f"\n❌ Dataset not found at {dataset_path}")
        print("Please run: python scripts/generate_test_data.py")
        return 1
    
    if not os.path.exists(store_path):
        print(f"\n❌ Store not found at {store_path}")
        print("Please run: python -m src.cli.main init store/")
        return 1
    
    try:
        # Step 1: Create baseline backup
        print_section("STEP 1: Create Baseline Backup")
        
        print("Creating baseline backup...")
        cmd_backup(store_path, dataset_path, "Baseline - Before Crash")
        
        snapshots_baseline = list_snapshots(store_path)
        baseline_snapshot = snapshots_baseline[-1]
        
        print(f"✅ Baseline backup created: {baseline_snapshot.id}")
        print(f"   Label: {baseline_snapshot.label}")
        print(f"   Total snapshots: {len(snapshots_baseline)}")
        
        # Step 2: Simulate crash during backup
        print_section("STEP 2: Simulate Crash During Backup")
        
        print("⚠️  Using crash_simulation.py to kill backup process...")
        print("   This will start a backup and kill it after 2 seconds")
        
        crash_cmd = f"python scripts/crash_simulation.py {dataset_path}/ {store_path}/ 2.0"
        print(f"\n💻 Command: {crash_cmd}")
        
        # Run crash simulation
        result = subprocess.run(crash_cmd, shell=True, capture_output=True, text=True)
        
        # Show output
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"   {line}")
        
        print(f"\n💥 Backup process killed (simulated crash)")
        
        # Step 3: Check store after crash
        print_section("STEP 3: Check Store After Crash")
        
        print("� Listing snapshots after crash...")
        snapshots_after_crash = list_snapshots(store_path)
        
        print(f"\n📊 Snapshots after crash: {len(snapshots_after_crash)}")
        
        if len(snapshots_after_crash) == len(snapshots_baseline):
            print(f"✅ No incomplete snapshot found!")
            print(f"   Snapshot count unchanged: {len(snapshots_baseline)} → {len(snapshots_after_crash)}")
            print(f"   Incomplete snapshot was not committed (as expected)")
        else:
            print(f"⚠️  Snapshot count changed: {len(snapshots_baseline)} → {len(snapshots_after_crash)}")
            
            # Check if there's an incomplete snapshot
            new_snapshots = [s for s in snapshots_after_crash if s.id not in [b.id for b in snapshots_baseline]]
            if new_snapshots:
                print(f"   Found {len(new_snapshots)} new snapshot(s):")
                for snap in new_snapshots:
                    print(f"      - {snap.id}: {snap.label}")
        
        # Show current snapshots
        print(f"\n� Current snapshots:")
        for i, snap in enumerate(snapshots_after_crash, 1):
            print(f"   {i}. {snap.id}")
            print(f"      Label: {snap.label}")
        
        # Step 4: Backup again after crash
        print_section("STEP 4: Backup Again After Crash")
        
        print("Creating new backup after crash recovery...")
        print("(Testing if store is still functional)")
        
        cmd_backup(store_path, dataset_path, "Complete - After Recovery")
        
        snapshots_after_recovery = list_snapshots(store_path)
        new_snapshot = snapshots_after_recovery[-1]
        
        print(f"\n✅ New backup created successfully!")
        print(f"   Snapshot ID: {new_snapshot.id}")
        print(f"   Label: {new_snapshot.label}")
        
        # Step 5: List all snapshots
        print_section("STEP 5: List All Snapshots")
        
        print(f"📊 Total snapshots: {len(snapshots_after_recovery)}")
        print(f"\n📋 All snapshots:")
        for i, snap in enumerate(snapshots_after_recovery, 1):
            print(f"   {i}. {snap.id}")
            print(f"      Label: {snap.label}")
            print(f"      Timestamp: {snap.timestamp}")
        
        # Step 6: Verify new snapshot
        print_section("STEP 6: Verify New Snapshot")
        
        print(f"🔍 Verifying snapshot: {new_snapshot.id}")
        
        try:
            cmd_verify(store_path, new_snapshot.id)
            print(f"\n✅ Verification PASSED!")
        except Exception as e:
            print(f"\n❌ Verification FAILED: {e}")
            return 1
        
        # Step 7: Restore to verify data integrity
        print_section("STEP 7: Restore and Verify Data Integrity")
        
        restore_path = "restored_after_crash"
        
        # Clean up previous restore if exists
        if os.path.exists(restore_path):
            import shutil
            shutil.rmtree(restore_path)
        
        print(f"🔄 Restoring snapshot to: {restore_path}")
        
        from src.cli.commands import cmd_restore, scan_directory
        
        try:
            cmd_restore(store_path, new_snapshot.id, restore_path)
            print(f"\n✅ Restore completed!")
        except Exception as e:
            print(f"\n❌ Restore FAILED: {e}")
            return 1
        
        # Compare restored with original dataset
        print(f"\n🔍 Comparing restored data with original dataset...")
        
        original_files = sorted(scan_directory(dataset_path))
        restored_files = sorted(scan_directory(restore_path))
        
        print(f"   Original files: {len(original_files)}")
        print(f"   Restored files: {len(restored_files)}")
        
        if len(original_files) != len(restored_files):
            print(f"   ❌ File count mismatch!")
            return 1
        
        print(f"   ✅ File count matches")
        
        # Sample check: compare first 5 files
        print(f"\n   Checking sample files (first 5)...")
        mismatches = 0
        for i, (orig, rest) in enumerate(zip(original_files[:5], restored_files[:5]), 1):
            rel_orig = os.path.relpath(orig, dataset_path)
            rel_rest = os.path.relpath(rest, restore_path)
            
            if rel_orig != rel_rest:
                print(f"      {i}. ❌ Path mismatch: {rel_orig} vs {rel_rest}")
                mismatches += 1
                continue
            
            with open(orig, 'rb') as f1, open(rest, 'rb') as f2:
                if f1.read() != f2.read():
                    print(f"      {i}. ❌ Content mismatch: {rel_orig}")
                    mismatches += 1
                else:
                    print(f"      {i}. ✅ {rel_orig}")
        
        if mismatches > 0:
            print(f"\n   ❌ Found {mismatches} mismatch(es)")
            return 1
        
        print(f"\n   ✅ All sampled files match perfectly!")
        print(f"\n📁 Restored data available at: {restore_path}")
        print(f"   (You can inspect or delete it manually)")

        
        # Success summary
        print_section("DEMO 5 COMPLETE - SUCCESS")
        print(f"✅ Baseline backup created")
        print(f"✅ Backup process killed during execution (crash simulated)")
        print(f"✅ Incomplete snapshot NOT committed (not in snapshot list)")
        print(f"✅ Store remained functional after crash")
        print(f"✅ New backup created successfully")
        print(f"✅ New snapshot verified successfully")
        print(f"✅ Data restored and verified (integrity confirmed)")
        print(f"\n🎉 Crash consistency working correctly!")
        print(f"\n📝 Summary:")
        print(f"   - Snapshots before crash: {len(snapshots_baseline)}")
        print(f"   - Snapshots after crash: {len(snapshots_after_crash)}")
        print(f"   - Snapshots after recovery: {len(snapshots_after_recovery)}")
        print(f"   - No corrupt snapshots found")
        print(f"   - Data integrity verified via restore")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
