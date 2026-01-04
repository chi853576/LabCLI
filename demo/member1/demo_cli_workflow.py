"""
Demo CLI Workflow - Test Member 1 functions như CLI sẽ dùng

Mô phỏng các commands:
1. init <backup_store_path>
2. backup <source_path> --label "<text>"
3. restore <snapshot_id> <target_path>

Run: python demo_cli_workflow.py
"""

import os
import sys
import shutil
import tempfile
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.chunker import chunk_file, hash_chunk
from core.storage import init_storage, store_chunk, get_chunk, chunk_exists


def scan_directory(path):
    """Helper: Scan directory recursively for files"""
    file_paths = []
    for root, dirs, files in os.walk(path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


def demo_init(backup_store_path):
    """
    Mô phỏng: init <backup_store_path>
    """
    print("=" * 70)
    print(f"COMMAND: init {backup_store_path}")
    print("=" * 70)
    
    # Member 1: Initialize storage
    init_storage(backup_store_path)
    print(f"[Member 1] Created chunks directory: {backup_store_path}/chunks/")
    
    # Member 2, 3, 4 sẽ tạo các thư mục khác (chưa implement)
    # Tạm thời tạo thủ công
    os.makedirs(os.path.join(backup_store_path, "snapshots"), exist_ok=True)
    os.makedirs(os.path.join(backup_store_path, "manifests"), exist_ok=True)
    print(f"[Placeholder] Created snapshots and manifests directories")
    
    print(f"\nBackup store initialized at: {backup_store_path}\n")


def demo_backup(source_path, label, backup_store_path):
    """
    Mô phỏng: backup <source_path> --label "<text>"
    
    Workflow:
    1. Scan directory for files
    2. Chunk each file (Member 1)
    3. Store chunks (Member 1)
    4. Create manifest (Member 2 - tạm mock)
    5. Create snapshot (Member 2 - tạm mock)
    """
    print("=" * 70)
    print(f"COMMAND: backup {source_path} --label \"{label}\"")
    print("=" * 70)
    
    # Step 1: Scan directory
    print("\n[Step 1] Scanning source directory...")
    file_paths = scan_directory(source_path)
    print(f"Found {len(file_paths)} files")
    
    # Step 2 & 3: Chunk and store files
    print("\n[Step 2-3] Chunking and storing files...")
    file_entries = []
    total_chunks = 0
    total_bytes = 0
    
    for file_path in file_paths:
        # Get relative path
        relative_path = os.path.relpath(file_path, source_path)
        
        # Chunk file (Member 1)
        chunks = chunk_file(file_path, chunk_size=1024*1024)
        
        # Store chunks and collect hashes (Member 1)
        chunk_hashes = []
        for chunk_data in chunks:
            chunk_hash = store_chunk(backup_store_path, chunk_data)
            chunk_hashes.append(chunk_hash)
            total_bytes += len(chunk_data)
        
        total_chunks += len(chunks)
        
        # Create file entry for manifest
        file_entries.append({
            "path": relative_path,
            "chunks": chunk_hashes
        })
        
        print(f"  {relative_path}: {len(chunks)} chunks, {len(chunk_hashes)} hashes")
    
    # Step 4: Create manifest (Member 2 - mock version)
    print("\n[Step 4] Creating manifest...")
    manifest = {
        "files": file_entries,
        "created_at": datetime.now().isoformat()
    }
    
    # Save manifest (normally Member 2 does this)
    manifest_hash = hash_chunk(json.dumps(manifest, sort_keys=True).encode())
    manifest_path = os.path.join(backup_store_path, "manifests", f"{manifest_hash}.json")
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest saved: {manifest_hash[:16]}...")
    
    # Step 5: Create snapshot (Member 2 - mock version)
    print("\n[Step 5] Creating snapshot...")
    timestamp = int(datetime.now().timestamp())
    snapshot_id = f"snapshot_{timestamp}"
    
    snapshot_metadata = {
        "id": snapshot_id,
        "label": label,
        "timestamp": timestamp,
        "manifest_hash": manifest_hash,
        "merkle_root": "MOCK_MERKLE_ROOT",  # Member 2 will compute real one
        "prev_root": ""  # First snapshot
    }
    
    # Save snapshot metadata
    snapshot_path = os.path.join(backup_store_path, "snapshots", f"{snapshot_id}.json")
    with open(snapshot_path, 'w') as f:
        json.dump(snapshot_metadata, f, indent=2)
    
    print(f"\nSnapshot created: {snapshot_id}")
    print(f"  Label: {label}")
    print(f"  Files: {len(file_entries)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Total size: {total_bytes:,} bytes ({total_bytes/1024/1024:.2f} MiB)")
    print()
    
    return snapshot_id


def demo_list_snapshots(backup_store_path):
    """
    Mô phỏng: list-snapshots
    """
    print("=" * 70)
    print("COMMAND: list-snapshots")
    print("=" * 70)
    
    snapshots_dir = os.path.join(backup_store_path, "snapshots")
    
    if not os.path.exists(snapshots_dir):
        print("No snapshots found")
        return
    
    snapshot_files = [f for f in os.listdir(snapshots_dir) if f.endswith('.json')]
    
    if not snapshot_files:
        print("No snapshots found")
        return
    
    print(f"\nFound {len(snapshot_files)} snapshots:\n")
    
    for snapshot_file in sorted(snapshot_files):
        snapshot_path = os.path.join(snapshots_dir, snapshot_file)
        with open(snapshot_path, 'r') as f:
            snapshot = json.load(f)
        
        timestamp_str = datetime.fromtimestamp(snapshot['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  {snapshot['id']}")
        print(f"    Label: {snapshot['label']}")
        print(f"    Time:  {timestamp_str}")
        print()


def demo_verify(snapshot_id, backup_store_path):
    """
    Mô phỏng: verify <snapshot_id>
    
    Workflow:
    1. Load snapshot metadata
    2. Load manifest
    3. Verify all chunks exist (Member 1)
    4. Verify Merkle root (Member 2 - skip for now)
    """
    print("=" * 70)
    print(f"COMMAND: verify {snapshot_id}")
    print("=" * 70)
    
    # Load snapshot
    snapshot_path = os.path.join(backup_store_path, "snapshots", f"{snapshot_id}.json")
    
    if not os.path.exists(snapshot_path):
        print(f"ERROR: Snapshot not found: {snapshot_id}")
        return False
    
    with open(snapshot_path, 'r') as f:
        snapshot = json.load(f)
    
    print(f"\nVerifying snapshot: {snapshot['label']}")
    
    # Load manifest
    manifest_hash = snapshot['manifest_hash']
    manifest_path = os.path.join(backup_store_path, "manifests", f"{manifest_hash}.json")
    
    if not os.path.exists(manifest_path):
        print(f"ERROR: Manifest not found: {manifest_hash}")
        return False
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Verify all chunks exist (Member 1)
    print("\n[Step 1] Verifying chunks...")
    total_chunks = 0
    missing_chunks = 0
    
    for file_entry in manifest['files']:
        for chunk_hash in file_entry['chunks']:
            total_chunks += 1
            
            # Use Member 1's function
            if not chunk_exists(backup_store_path, chunk_hash):
                print(f"  ERROR: Missing chunk {chunk_hash[:16]}... in {file_entry['path']}")
                missing_chunks += 1
    
    print(f"Checked {total_chunks} chunks")
    
    if missing_chunks > 0:
        print(f"\nVERIFY FAILED: {missing_chunks} chunks missing")
        return False
    
    print(f"\nVERIFY OK: {snapshot_id}")
    print("  All chunks present")
    print("  (Merkle root verification skipped - Member 2 not implemented)")
    print()
    
    return True


def demo_restore(snapshot_id, target_path, backup_store_path):
    """
    Mô phỏng: restore <snapshot_id> <target_path>
    
    Workflow:
    1. Verify snapshot first
    2. Load manifest
    3. Retrieve chunks and reconstruct files (Member 1)
    """
    print("=" * 70)
    print(f"COMMAND: restore {snapshot_id} {target_path}")
    print("=" * 70)
    
    # Step 1: Verify first
    print("\n[Step 1] Verifying snapshot before restore...")
    if not demo_verify(snapshot_id, backup_store_path):
        print("RESTORE ABORTED: Verification failed")
        return False
    
    # Step 2: Load manifest
    print("[Step 2] Loading manifest...")
    snapshot_path = os.path.join(backup_store_path, "snapshots", f"{snapshot_id}.json")
    with open(snapshot_path, 'r') as f:
        snapshot = json.load(f)
    
    manifest_path = os.path.join(backup_store_path, "manifests", f"{snapshot['manifest_hash']}.json")
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Step 3: Restore files
    print(f"\n[Step 3] Restoring {len(manifest['files'])} files...")
    
    os.makedirs(target_path, exist_ok=True)
    
    for file_entry in manifest['files']:
        file_path = os.path.join(target_path, file_entry['path'])
        
        # Create parent directories
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Retrieve chunks and reconstruct file (Member 1)
        file_data = b""
        for chunk_hash in file_entry['chunks']:
            chunk_data = get_chunk(backup_store_path, chunk_hash)
            file_data += chunk_data
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        print(f"  Restored: {file_entry['path']} ({len(file_data):,} bytes)")
    
    print(f"\nRESTORE COMPLETE: {snapshot_id} -> {target_path}")
    print()
    
    return True


def create_test_dataset(dataset_path):
    """Create test dataset for demo"""
    print("Creating test dataset...")
    
    os.makedirs(dataset_path, exist_ok=True)
    
    # Create some test files
    files = [
        ("file1.txt", b"This is file 1 content. " * 1000),
        ("file2.txt", b"This is file 2 content. " * 2000),
        ("subdir/file3.txt", b"File in subdirectory. " * 1500),
        ("subdir/file4.bin", b"Binary data " * 3000),
    ]
    
    total_size = 0
    for filepath, content in files:
        full_path = os.path.join(dataset_path, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(content)
        total_size += len(content)
    
    print(f"Created {len(files)} test files ({total_size:,} bytes)\n")


def main():
    """Run complete CLI workflow demo"""
    print("\n" + "=" * 70)
    print(" CLI WORKFLOW DEMO - Testing Member 1 with store_path")
    print("=" * 70 + "\n")
    
    # Setup temporary directories
    test_dir = tempfile.mkdtemp(prefix="labcli_demo_")
    dataset_path = os.path.join(test_dir, "dataset")
    backup_store_path = os.path.join(test_dir, "store")
    restore_path = os.path.join(test_dir, "restored")
    
    print(f"Working directory: {test_dir}\n")
    
    try:
        # Create test dataset
        create_test_dataset(dataset_path)
        
        # 1. Init
        demo_init(backup_store_path)
        
        # 2. First backup
        snapshot1 = demo_backup(dataset_path, "Initial backup", backup_store_path)
        
        # 3. List snapshots
        demo_list_snapshots(backup_store_path)
        
        # 4. Modify dataset
        print("=" * 70)
        print("Modifying dataset...")
        print("=" * 70)
        os.remove(os.path.join(dataset_path, "file1.txt"))
        with open(os.path.join(dataset_path, "file2.txt"), 'ab') as f:
            f.write(b"APPENDED DATA " * 100)
        print("  Deleted: file1.txt")
        print("  Modified: file2.txt")
        print()
        
        # 5. Second backup
        snapshot2 = demo_backup(dataset_path, "After modifications", backup_store_path)
        
        # 6. List snapshots again
        demo_list_snapshots(backup_store_path)
        
        # 7. Verify first snapshot
        demo_verify(snapshot1, backup_store_path)
        
        # 8. Restore first snapshot
        demo_restore(snapshot1, restore_path, backup_store_path)
        
        # 9. Compare restored with original
        print("=" * 70)
        print("COMPARISON: Restored vs Current Dataset")
        print("=" * 70)
        print(f"\nRestored directory: {restore_path}")
        print(f"Current dataset:    {dataset_path}")
        
        restored_files = set(os.path.relpath(os.path.join(root, f), restore_path) 
                           for root, _, files in os.walk(restore_path) 
                           for f in files)
        
        current_files = set(os.path.relpath(os.path.join(root, f), dataset_path) 
                          for root, _, files in os.walk(dataset_path) 
                          for f in files)
        
        print(f"\nFiles in restored: {sorted(restored_files)}")
        print(f"Files in current:  {sorted(current_files)}")
        print(f"\nfile1.txt restored: {'file1.txt' in restored_files}")
        print(f"file1.txt in current: {'file1.txt' in current_files}")
        print("\nNote: Restored has file1.txt (from snapshot1), current doesn't (deleted)")
        print()
        
        # 10. Show storage efficiency
        print("=" * 70)
        print("STORAGE STATISTICS")
        print("=" * 70)
        
        chunks_dir = os.path.join(backup_store_path, "chunks")
        chunk_count = sum(len(files) for _, _, files in os.walk(chunks_dir))
        
        print(f"\nUnique chunks stored: {chunk_count}")
        print(f"Snapshots created:    2")
        print(f"\nDeduplication: Shared chunks between snapshots were stored only once")
        print()
        
        print("=" * 70)
        print(" DEMO COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"\nTest files location: {test_dir}")
        print("You can inspect the store structure:")
        print(f"  ls -R {backup_store_path}")
        print()
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup option
    response = input("Delete test files? (y/N): ")
    if response.lower() == 'y':
        shutil.rmtree(test_dir)
        print(f"Cleaned up: {test_dir}")
    else:
        print(f"Test files kept at: {test_dir}")


if __name__ == "__main__":
    main()
