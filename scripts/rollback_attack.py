"""
Script to simulate rollback attack for Demo 4
Replaces newer snapshot with older snapshot's data
"""

import os
import sys
import json
from pathlib import Path


def find_snapshots(store_path):
    """Find all snapshots in the store, sorted by timestamp"""
    snapshots_dir = os.path.join(store_path, "snapshots")
    
    if not os.path.exists(snapshots_dir):
        print(f"❌ Snapshots directory not found: {snapshots_dir}")
        return []
    
    # Find all snapshot files
    snapshot_files = sorted(Path(snapshots_dir).glob("*.json"))
    
    if len(snapshot_files) < 2:
        print(f"❌ Need at least 2 snapshots for rollback attack")
        print(f"   Found: {len(snapshot_files)} snapshot(s)")
        return []
    
    return snapshot_files


def rollback_attack(store_path, snapshot_files):
    """
    Simulate rollback attack by replacing newer snapshot with older snapshot's data
    
    Args:
        store_path: Path to store
        snapshot_files: List of snapshot files (sorted by time)
    """
    print("\n" + "=" * 70)
    print("  ROLLBACK ATTACK SIMULATION - Demo 4")
    print("=" * 70)
    
    # Get older and newer snapshots
    snapshot_a_file = snapshot_files[0]  # Older
    snapshot_b_file = snapshot_files[-1]  # Newer
    
    # Load snapshots
    with open(snapshot_a_file, 'r', encoding='utf-8') as f:
        snapshot_a = json.load(f)
    
    with open(snapshot_b_file, 'r', encoding='utf-8') as f:
        snapshot_b = json.load(f)
    
    # Show snapshot chain
    print(f"\n📊 Snapshot Chain:")
    print(f"   Snapshot A (older):")
    print(f"     ID: {snapshot_a.get('id')}")
    print(f"     Merkle root: {snapshot_a.get('merkle_root')}")
    print(f"     Prev root: {snapshot_a.get('prev_root', '(none)')}")
    
    print(f"\n   Snapshot B (newer):")
    print(f"     ID: {snapshot_b.get('id')}")
    print(f"     Merkle root: {snapshot_b.get('merkle_root')}")
    print(f"     Prev root: {snapshot_b.get('prev_root', '(none)')}")
    
    # Simulate rollback attack
    print(f"\n⚠️  Simulating rollback attack...")
    print(f"   Target: Replace snapshot B with snapshot A's data")
    
    original_merkle_b = snapshot_b.get('merkle_root')
    merkle_a = snapshot_a.get('merkle_root')
    
    print(f"\n   Action: Changing snapshot B's merkle_root")
    print(f"     From: {original_merkle_b} (B's original root)")
    print(f"     To:   {merkle_a} (A's root - ROLLBACK!)")
    
    # Modify snapshot B
    snapshot_b['merkle_root'] = merkle_a
    snapshot_b['manifest_hash'] = snapshot_a.get('manifest_hash')
    
    # Write back
    with open(snapshot_b_file, 'w', encoding='utf-8') as f:
        json.dump(snapshot_b, f, indent=2)
    
    print(f"\n   ✓ Snapshot B file modified")
    
    # Show result
    print(f"\n" + "=" * 70)
    print(f"  ATTACK RESULT")
    print(f"=" * 70)
    print(f"  Snapshot B now has:")
    print(f"    Merkle root: {snapshot_b.get('merkle_root')}")
    print(f"    Prev root:   {snapshot_b.get('prev_root')}")
    
    # Check if rollback is detectable
    if snapshot_b.get('merkle_root') == snapshot_b.get('prev_root'):
        print(f"\n  ⚠️  PROBLEM: merkle_root == prev_root (INVALID!)")
        print(f"\n  This is a rollback attack indicator!")
    else:
        print(f"\n  ⚠️  Merkle root changed, but prev_root unchanged")
        print(f"  Verify will detect mismatch between snapshot and manifest")
    
    print(f"\n✅ Rollback attack simulated successfully.")
    print(f"=" * 70)
    
    return True


def main():
    """Main function"""
    # Get store path from command line or use default
    if len(sys.argv) > 1:
        store_path = sys.argv[1]
    else:
        store_path = "store"
    
    print(f"Store path: {store_path}")
    
    # Find snapshots
    print(f"\n🔍 Searching for snapshots...")
    snapshot_files = find_snapshots(store_path)
    
    if len(snapshot_files) < 2:
        print(f"\nPlease create at least 2 snapshots first:")
        print(f"  1. python -m src.cli.main backup dataset/ --label 'A' --store {store_path}/")
        print(f"  2. Modify dataset")
        print(f"  3. python -m src.cli.main backup dataset/ --label 'B' --store {store_path}/")
        return 1
    
    print(f"✓ Found {len(snapshot_files)} snapshots")
    
    # Simulate rollback attack
    success = rollback_attack(store_path, snapshot_files)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
