"""
Demo script for Member 1 - Storage & Chunking

This script demonstrates:
1. File chunking
2. Content-addressable storage
3. Deduplication
4. File reconstruction

Run: python demo_storage.py
"""

import os
import sys
import tempfile
import shutil

# Add src to path
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
)

from core.chunker import chunk_file, hash_chunk
from core.storage import init_storage, store_chunk, get_chunk, chunk_exists


def demo_basic_chunking():
    """Demo 1: Basic file chunking"""
    print("=" * 60)
    print("DEMO 1: BASIC FILE CHUNKING")
    print("=" * 60)
    
    # Create test file
    test_dir = tempfile.mkdtemp()
    test_file = os.path.join(test_dir, "test.txt")
    
    # 2.5 MiB of data
    data = b"Hello World! " * 200000
    with open(test_file, 'wb') as f:
        f.write(data)
    
    file_size = len(data)
    print(f"Created test file: {file_size:,} bytes ({file_size/1024/1024:.2f} MiB)")
    
    # Chunk file
    chunks = chunk_file(test_file, chunk_size=1024*1024)
    print(f"Number of chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        chunk_hash = hash_chunk(chunk)
        print(f"  Chunk {i+1}: {len(chunk):,} bytes, hash: {chunk_hash[:16]}...")
    
    # Cleanup
    shutil.rmtree(test_dir)
    print()


def demo_storage_and_dedup():
    """Demo 2: Storage and deduplication"""
    print("=" * 60)
    print("DEMO 2: STORAGE AND DEDUPLICATION")
    print("=" * 60)
    
    # Create temporary store
    store_path = tempfile.mkdtemp()
    init_storage(store_path)
    print(f"Initialized storage at: {store_path}")
    
    # Store some chunks
    chunk1 = b"First chunk data"
    chunk2 = b"Second chunk data"
    chunk3 = b"First chunk data"  # Duplicate of chunk1
    
    hash1 = store_chunk(store_path, chunk1)
    print(f"Stored chunk 1: {hash1[:16]}...")
    
    hash2 = store_chunk(store_path, chunk2)
    print(f"Stored chunk 2: {hash2[:16]}...")
    
    hash3 = store_chunk(store_path, chunk3)
    print(f"Stored chunk 3 (duplicate): {hash3[:16]}...")
    
    # Check deduplication
    print(f"\nDeduplication check:")
    print(f"  Hash1 == Hash3: {hash1 == hash3}")
    
    # Count files in storage
    chunks_dir = os.path.join(store_path, "chunks")
    file_count = sum(len(files) for _, _, files in os.walk(chunks_dir))
    print(f"  Total files in storage: {file_count} (should be 2, not 3)")
    
    # Verify chunks exist
    print(f"\nChunk existence:")
    print(f"  Chunk 1 exists: {chunk_exists(store_path, hash1)}")
    print(f"  Chunk 2 exists: {chunk_exists(store_path, hash2)}")
    print(f"  Fake chunk exists: {chunk_exists(store_path, '0'*64)}")
    
    # Cleanup
    shutil.rmtree(store_path)
    print()


def demo_file_reconstruction():
    """Demo 3: Complete workflow - chunk, store, retrieve, reconstruct"""
    print("=" * 60)
    print("DEMO 3: FILE RECONSTRUCTION")
    print("=" * 60)
    
    # Create directories
    test_dir = tempfile.mkdtemp()
    store_path = tempfile.mkdtemp()
    
    # Initialize storage
    init_storage(store_path)
    
    # Create original file
    original_file = os.path.join(test_dir, "original.txt")
    original_data = b"This is the original file content. " * 50000  # ~1.6 MiB
    
    with open(original_file, 'wb') as f:
        f.write(original_data)
    
    print(f"Original file size: {len(original_data):,} bytes")
    
    # BACKUP: Chunk and store
    print("\n--- BACKUP PHASE ---")
    chunks = chunk_file(original_file, chunk_size=1024*1024)
    print(f"File chunked into {len(chunks)} chunks")
    
    chunk_hashes = []
    for i, chunk in enumerate(chunks):
        chunk_hash = store_chunk(store_path, chunk)
        chunk_hashes.append(chunk_hash)
        print(f"  Stored chunk {i+1}: {len(chunk):,} bytes -> {chunk_hash[:16]}...")
    
    # RESTORE: Retrieve chunks and reconstruct
    print("\n--- RESTORE PHASE ---")
    reconstructed_data = b""
    for i, chunk_hash in enumerate(chunk_hashes):
        chunk = get_chunk(store_path, chunk_hash)
        reconstructed_data += chunk
        print(f"  Retrieved chunk {i+1}: {len(chunk):,} bytes")
    
    # Verify reconstruction
    print("\n--- VERIFICATION ---")
    print(f"Original size:      {len(original_data):,} bytes")
    print(f"Reconstructed size: {len(reconstructed_data):,} bytes")
    print(f"Data matches: {original_data == reconstructed_data}")
    
    # Save reconstructed file
    restored_file = os.path.join(test_dir, "restored.txt")
    with open(restored_file, 'wb') as f:
        f.write(reconstructed_data)
    
    print(f"\nRestored file saved to: {restored_file}")
    
    # Cleanup
    shutil.rmtree(test_dir)
    shutil.rmtree(store_path)
    print()


def demo_integrity_check():
    """Demo 4: Integrity verification"""
    print("=" * 60)
    print("DEMO 4: INTEGRITY VERIFICATION")
    print("=" * 60)
    
    # Create temporary store
    store_path = tempfile.mkdtemp()
    init_storage(store_path)
    
    # Store a chunk
    chunk_data = b"Important data that must not be corrupted"
    chunk_hash = store_chunk(store_path, chunk_data)
    print(f"Stored chunk: {chunk_hash[:16]}...")
    
    # Retrieve normally (should work)
    retrieved = get_chunk(store_path, chunk_hash)
    print(f"Retrieved successfully: {len(retrieved)} bytes")
    
    # Simulate corruption
    print("\n--- SIMULATING CORRUPTION ---")
    chunk_path = os.path.join(
        store_path, "chunks", 
        chunk_hash[:2], chunk_hash[2:4], chunk_hash
    )
    
    # Corrupt the chunk file
    with open(chunk_path, 'wb') as f:
        f.write(b"CORRUPTED DATA")
    print("Chunk file corrupted on disk")
    
    # Try to retrieve (should fail)
    print("\nAttempting to retrieve corrupted chunk...")
    try:
        get_chunk(store_path, chunk_hash)
        print("ERROR: Should have detected corruption!")
    except ValueError as e:
        print(f"SUCCESS: Corruption detected!")
        print(f"  Error: {str(e)[:80]}...")
    
    # Cleanup
    shutil.rmtree(store_path)
    print()


def demo_dedup_across_files():
    """Demo 5: Deduplication across multiple files"""
    print("=" * 60)
    print("DEMO 5: DEDUPLICATION ACROSS FILES")
    print("=" * 60)
    
    # Create directories
    test_dir = tempfile.mkdtemp()
    store_path = tempfile.mkdtemp()
    init_storage(store_path)
    
    # Create three files with some shared content
    shared_content = b"SHARED BLOCK " * 80000  # ~1 MiB shared
    
    file1_data = shared_content + b"FILE1 UNIQUE " * 10000
    file2_data = shared_content + b"FILE2 UNIQUE " * 10000
    file3_data = shared_content + b"FILE3 UNIQUE " * 10000
    
    files = []
    for i, data in enumerate([file1_data, file2_data, file3_data], 1):
        filepath = os.path.join(test_dir, f"file{i}.bin")
        with open(filepath, 'wb') as f:
            f.write(data)
        files.append(filepath)
    
    print(f"Created 3 files with shared content")
    print(f"Each file size: ~{len(file1_data)/1024/1024:.2f} MiB")
    
    # Backup all files
    all_chunks = 0
    for i, filepath in enumerate(files, 1):
        chunks = chunk_file(filepath, chunk_size=1024*1024)
        print(f"\nFile {i}: {len(chunks)} chunks")
        
        for chunk in chunks:
            store_chunk(store_path, chunk)
            all_chunks += 1
    
    # Count unique chunks in storage
    chunks_dir = os.path.join(store_path, "chunks")
    unique_chunks = sum(len(files) for _, _, files in os.walk(chunks_dir))
    
    print(f"\n--- DEDUPLICATION RESULTS ---")
    print(f"Total chunks processed: {all_chunks}")
    print(f"Unique chunks stored:   {unique_chunks}")
    print(f"Deduplication saved:    {all_chunks - unique_chunks} chunks")
    print(f"Storage efficiency:     {unique_chunks/all_chunks*100:.1f}% of original")
    
    # Cleanup
    shutil.rmtree(test_dir)
    shutil.rmtree(store_path)
    print()


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print(" MEMBER 1 - STORAGE & CHUNKING DEMO")
    print("=" * 60 + "\n")
    
    try:
        demo_basic_chunking()
        demo_storage_and_dedup()
        demo_file_reconstruction()
        demo_integrity_check()
        demo_dedup_across_files()
        
        print("=" * 60)
        print(" ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()