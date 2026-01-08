"""
Script to corrupt a manifest file for Demo 3
Simulates manifest tampering / metadata corruption
"""

import os
import sys
import json
from pathlib import Path


def find_snapshot(store_path):
    """Find the first snapshot in the store"""
    snapshots_dir = os.path.join(store_path, "snapshots")
    
    if not os.path.exists(snapshots_dir):
        print(f"❌ Snapshots directory not found: {snapshots_dir}")
        return None
    
    # Find first snapshot file
    snapshot_files = list(Path(snapshots_dir).glob("*.json"))
    if not snapshot_files:
        print(f"❌ No snapshot files found in {snapshots_dir}")
        return None
    
    return snapshot_files[0]


def corrupt_manifest(store_path, snapshot_file):
    """
    Corrupt a manifest file by modifying chunk hash
    
    Args:
        store_path: Path to store
        snapshot_file: Path to snapshot file
    """
    print("\n" + "=" * 70)
    print("  MANIFEST CORRUPTION SCRIPT - Demo 3")
    print("=" * 70)
    
    # 1. Load snapshot
    print(f"\n🔍 Loading snapshot metadata...")
    with open(snapshot_file, 'r', encoding='utf-8') as f:
        snapshot = json.load(f)
    
    snapshot_id = snapshot.get("id", snapshot_file.stem)
    manifest_hash = snapshot.get("manifest_hash")
    original_merkle_root = snapshot.get("merkle_root")
    
    print(f"   Snapshot ID: {snapshot_id}")
    print(f"   Manifest hash: {manifest_hash}")
    print(f"   Merkle root: {original_merkle_root}")
    
    # 2. Load manifest
    print(f"\n📂 Loading manifest file...")
    manifest_path = os.path.join(store_path, "manifests", f"{manifest_hash}.json")
    
    if not os.path.exists(manifest_path):
        print(f"❌ Manifest file not found: {manifest_path}")
        return False
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    print(f"   Path: {manifest_path}")
    print(f"   Files in manifest: {len(manifest.get('files', []))}")
    
    # 3. Corrupt manifest (modify first file's first chunk hash)
    print(f"\n⚠️  Corrupting manifest...")
    
    if not manifest.get('files') or not manifest['files'][0].get('chunks'):
        print(f"❌ No files or chunks in manifest")
        return False
    
    # Get first file's first chunk
    first_file = manifest['files'][0]
    original_chunk_hash = first_file['chunks'][0]
    
    print(f"   Target: First file's first chunk hash")
    print(f"   File: {first_file.get('path', 'unknown')}")
    print(f"   Original chunk hash: {original_chunk_hash}")
    
    # Modify last 2 characters of chunk hash
    corrupted_chunk_hash = original_chunk_hash[:-2] + "XX"
    first_file['chunks'][0] = corrupted_chunk_hash
    
    print(f"   Modified chunk hash: {corrupted_chunk_hash}")
    
    # Write back corrupted manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"   ✓ Manifest file modified")
    
    # 4. Compute new Merkle root
    print(f"\n📊 Computing new Merkle root...")
    
    # Import merkle module to compute new root
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.core.merkle import compute_merkle_root
        
        new_merkle_root = compute_merkle_root(manifest)
        
        print(f"   Original Merkle root: {original_merkle_root}")
        print(f"   New Merkle root:      {new_merkle_root}")
    except Exception as e:
        print(f"   ⚠️ Could not compute Merkle root: {e}")
        new_merkle_root = "unknown"
    
    # 5. Show result
    print(f"\n" + "=" * 70)
    print(f"  CORRUPTION RESULT")
    print(f"=" * 70)
    
    if new_merkle_root != original_merkle_root and new_merkle_root != "unknown":
        print(f"  Merkle root changed: YES ❌")
        print(f"  Manifest file: CORRUPTED")
        print(f"\n✅ Corruption successful! Manifest has been modified.")
        print(f"=" * 70)
        return True
    else:
        print(f"  Merkle root changed: UNKNOWN ⚠️")
        print(f"  Manifest file: MODIFIED (but Merkle root not computed)")
        print(f"\n⚠️ Manifest modified, but could not verify Merkle root change")
        print(f"=" * 70)
        return True  # Still return True as manifest was modified


def main():
    """Main function"""
    # Get store path from command line or use default
    if len(sys.argv) > 1:
        store_path = sys.argv[1]
    else:
        store_path = "store"
    
    print(f"Store path: {store_path}")
    
    # Find a snapshot
    print(f"\n🔍 Searching for snapshots...")
    snapshot_file = find_snapshot(store_path)
    
    if not snapshot_file:
        print(f"\nPlease ensure you have created a backup first:")
        print(f"  python -m src.cli.main backup dataset/ --store {store_path}/")
        return 1
    
    print(f"✓ Found snapshot: {snapshot_file.stem}")
    
    # Corrupt the manifest
    success = corrupt_manifest(store_path, snapshot_file)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
