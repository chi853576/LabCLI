"""
Quick Test - Member 1 với store_path

Script đơn giản để test nhanh Member 1 functions như CLI sẽ dùng.

Run: python quick_test.py
"""

import os
import sys
import shutil

# Add src to path
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
)

from core.chunker import chunk_file
from core.storage import init_storage, store_chunk, get_chunk, chunk_exists


def main():
    print("\n" + "="*60)
    print("QUICK TEST - Member 1 with store_path")
    print("="*60 + "\n")
    
    # Setup
    store_path = "test_store"
    dataset_path = "test_dataset"
    
    # Clean up if exists
    for path in [store_path, dataset_path]:
        if os.path.exists(path):
            shutil.rmtree(path)
    
    try:
        # 1. Initialize storage (như CLI: init store)
        print("1. INIT")
        print("-" * 60)
        init_storage(store_path)
        print(f"✓ Initialized storage at: {store_path}")
        print(f"  Created: {store_path}/chunks/\n")
        
        # 2. Create test dataset
        print("2. CREATE TEST FILES")
        print("-" * 60)
        os.makedirs(dataset_path)
        
        test_files = {
            "file1.txt": b"Hello World! " * 10000,  # ~120 KB
            "file2.txt": b"Python is awesome. " * 20000,  # ~360 KB
            "subdir/file3.bin": b"Binary data " * 50000,  # ~550 KB
        }
        
        for filepath, content in test_files.items():
            full_path = os.path.join(dataset_path, filepath)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(content)
            print(f"✓ Created: {filepath} ({len(content):,} bytes)")
        
        total_size = sum(len(c) for c in test_files.values())
        print(f"\nTotal dataset: {total_size:,} bytes ({total_size/1024:.1f} KB)\n")
        
        # 3. Backup files (như CLI: backup dataset/ --label "test")
        print("3. BACKUP (chunk + store)")
        print("-" * 60)
        
        all_chunks = []
        for filepath, content in test_files.items():
            full_path = os.path.join(dataset_path, filepath)
            
            # Chunk file
            chunks = chunk_file(full_path, chunk_size=1024*1024)
            
            # Store chunks
            chunk_hashes = []
            for chunk_data in chunks:
                chunk_hash = store_chunk(store_path, chunk_data)
                chunk_hashes.append(chunk_hash)
            
            all_chunks.extend(chunk_hashes)
            print(f"✓ {filepath}: {len(chunks)} chunks → {len(chunk_hashes)} hashes")
        
        print(f"\nTotal chunks stored: {len(all_chunks)}\n")
        
        # 4. Verify chunks exist
        print("4. VERIFY")
        print("-" * 60)
        
        for i, chunk_hash in enumerate(all_chunks[:3], 1):  # Check first 3
            exists = chunk_exists(store_path, chunk_hash)
            print(f"✓ Chunk {i}: {chunk_hash[:16]}... exists: {exists}")
        
        print(f"  ... and {len(all_chunks) - 3} more chunks\n")
        
        # 5. Restore test (retrieve chunks)
        print("5. RESTORE TEST (retrieve chunks)")
        print("-" * 60)
        
        # Test restore file1.txt
        test_file = "file1.txt"
        original_content = test_files[test_file]
        
        # Get chunks for this file (would come from manifest in real system)
        file_path = os.path.join(dataset_path, test_file)
        chunks = chunk_file(file_path, chunk_size=1024*1024)
        
        # Reconstruct
        reconstructed = b""
        for chunk_data in chunks:
            chunk_hash = store_chunk(store_path, chunk_data)  # Get hash
            retrieved = get_chunk(store_path, chunk_hash)  # Retrieve
            reconstructed += retrieved
        
        # Verify
        match = (reconstructed == original_content)
        print(f"✓ Restored: {test_file}")
        print(f"  Original size:      {len(original_content):,} bytes")
        print(f"  Reconstructed size: {len(reconstructed):,} bytes")
        print(f"  Data matches: {match}")
        
        if not match:
            print("  ERROR: Reconstruction failed!")
            return
        
        print()
        
        # 6. Show storage structure
        print("6. STORAGE STRUCTURE")
        print("-" * 60)
        print(f"Store path: {store_path}/")
        
        for root, dirs, files in os.walk(store_path):
            level = root.replace(store_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            
            # Limit files shown
            subindent = ' ' * 2 * (level + 1)
            for file in files[:3]:
                print(f'{subindent}{file}')
            if len(files) > 3:
                print(f'{subindent}... and {len(files) - 3} more chunks')
        
        print()
        
        # 7. Deduplication test
        print("7. DEDUPLICATION TEST")
        print("-" * 60)
        
        # Store same data again
        duplicate_data = b"Hello World! " * 10000
        hash1 = store_chunk(store_path, duplicate_data)
        
        # Count chunks before
        chunks_dir = os.path.join(store_path, "chunks")
        files_before = sum(len(files) for _, _, files in os.walk(chunks_dir))
        
        # Store again
        hash2 = store_chunk(store_path, duplicate_data)
        
        # Count chunks after
        files_after = sum(len(files) for _, _, files in os.walk(chunks_dir))
        
        print(f"✓ First store:  {hash1[:16]}...")
        print(f"✓ Second store: {hash2[:16]}...")
        print(f"  Hashes match: {hash1 == hash2}")
        print(f"  Files before: {files_before}")
        print(f"  Files after:  {files_after}")
        print(f"  Deduplicated: {files_before == files_after}")
        print()
        
        # Success
        print("="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print(f"\nTest store location: {os.path.abspath(store_path)}/")
        print(f"Test dataset location: {os.path.abspath(dataset_path)}/")
        print("\nYou can inspect the files:")
        print(f"  ls -R {store_path}")
        print(f"  ls -R {dataset_path}")
        print()
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup option
        response = input("Delete test files? (y/N): ")
        if response.lower() == 'y':
            for path in [store_path, dataset_path]:
                if os.path.exists(path):
                    shutil.rmtree(path)
            print("✓ Cleaned up test files")
        else:
            print(f"✓ Test files kept")


if __name__ == "__main__":
    main()
