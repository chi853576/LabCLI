"""
Unit tests for storage module - MEMBER 1

Test coverage:
- Chunking with different file sizes
- Hash computation
- Content-addressable storage
- Deduplication
- Chunk retrieval
- Error handling
"""

import os
import sys
import tempfile
import shutil
import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from core.chunker import chunk_file, hash_chunk
from core.storage import init_storage, store_chunk, get_chunk, chunk_exists


class TestChunker:
    """Test chunking functionality"""
    
    def setup_method(self):
        """Create temporary test directory"""
        self.test_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary test directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_chunk_small_file(self):
        """Test chunking a file smaller than chunk size"""
        test_file = os.path.join(self.test_dir, "small.txt")
        with open(test_file, 'wb') as f:
            f.write(b"Hello World")
        
        chunks = chunk_file(test_file, chunk_size=1024*1024)
        
        assert len(chunks) == 1
        assert chunks[0] == b"Hello World"
    
    def test_chunk_exact_size(self):
        """Test chunking a file exactly 1 MiB"""
        test_file = os.path.join(self.test_dir, "exact.bin")
        chunk_size = 1024 * 1024
        data = b"A" * chunk_size
        
        with open(test_file, 'wb') as f:
            f.write(data)
        
        chunks = chunk_file(test_file, chunk_size=chunk_size)
        
        assert len(chunks) == 1
        assert len(chunks[0]) == chunk_size
    
    def test_chunk_multiple_chunks(self):
        """Test chunking a file into multiple chunks"""
        test_file = os.path.join(self.test_dir, "large.bin")
        chunk_size = 1024 * 1024
        # Create 2.5 MiB file
        data = b"B" * int(chunk_size * 2.5)
        
        with open(test_file, 'wb') as f:
            f.write(data)
        
        chunks = chunk_file(test_file, chunk_size=chunk_size)
        
        assert len(chunks) == 3
        assert len(chunks[0]) == chunk_size
        assert len(chunks[1]) == chunk_size
        assert len(chunks[2]) == chunk_size // 2
    
    def test_chunk_empty_file(self):
        """Test chunking an empty file"""
        test_file = os.path.join(self.test_dir, "empty.txt")
        with open(test_file, 'wb') as f:
            pass
        
        chunks = chunk_file(test_file)
        
        assert len(chunks) == 0
    
    def test_chunk_nonexistent_file(self):
        """Test chunking a file that doesn't exist"""
        with pytest.raises(FileNotFoundError):
            chunk_file(os.path.join(self.test_dir, "nonexistent.txt"))
    
    def test_hash_chunk(self):
        """Test hash computation"""
        chunk_data = b"Hello World"
        chunk_hash = hash_chunk(chunk_data)
        
        # Expected SHA-256 hash of "Hello World"
        expected = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
        assert chunk_hash == expected
        assert len(chunk_hash) == 64  # SHA-256 hex string is 64 chars
    
    def test_hash_empty_chunk(self):
        """Test hashing empty data"""
        chunk_hash = hash_chunk(b"")
        
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert chunk_hash == expected


class TestStorage:
    """Test storage functionality"""
    
    def setup_method(self):
        """Create temporary store directory"""
        self.store_path = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary store directory"""
        if os.path.exists(self.store_path):
            shutil.rmtree(self.store_path)
    
    def test_init_storage(self):
        """Test storage initialization"""
        init_storage(self.store_path)
        
        chunks_dir = os.path.join(self.store_path, "chunks")
        assert os.path.exists(chunks_dir)
        assert os.path.isdir(chunks_dir)
    
    def test_store_and_retrieve_chunk(self):
        """Test storing and retrieving a chunk"""
        init_storage(self.store_path)
        
        chunk_data = b"Test chunk data"
        chunk_hash = store_chunk(self.store_path, chunk_data)
        
        # Verify hash is correct
        assert len(chunk_hash) == 64
        
        # Retrieve chunk
        retrieved = get_chunk(self.store_path, chunk_hash)
        assert retrieved == chunk_data
    
    def test_deduplication(self):
        """Test that identical chunks are not stored twice"""
        init_storage(self.store_path)
        
        chunk_data = b"Duplicate chunk"
        
        # Store chunk first time
        hash1 = store_chunk(self.store_path, chunk_data)
        
        # Count files before second store
        chunks_dir = os.path.join(self.store_path, "chunks")
        files_before = sum(len(files) for _, _, files in os.walk(chunks_dir))
        
        # Store same chunk again
        hash2 = store_chunk(self.store_path, chunk_data)
        
        # Count files after second store
        files_after = sum(len(files) for _, _, files in os.walk(chunks_dir))
        
        # Hashes should be identical
        assert hash1 == hash2
        
        # No new files should be created
        assert files_before == files_after
    
    def test_chunk_exists(self):
        """Test chunk existence check"""
        init_storage(self.store_path)
        
        chunk_data = b"Test existence"
        chunk_hash = store_chunk(self.store_path, chunk_data)
        
        # Chunk should exist
        assert chunk_exists(self.store_path, chunk_hash) == True
        
        # Non-existent chunk
        fake_hash = "0" * 64
        assert chunk_exists(self.store_path, fake_hash) == False
    
    def test_get_nonexistent_chunk(self):
        """Test retrieving a chunk that doesn't exist"""
        init_storage(self.store_path)
        
        fake_hash = "0" * 64
        with pytest.raises(FileNotFoundError):
            get_chunk(self.store_path, fake_hash)
    
    def test_chunk_path_structure(self):
        """Test that chunks are stored in correct directory structure"""
        init_storage(self.store_path)
        
        chunk_data = b"Path structure test"
        chunk_hash = store_chunk(self.store_path, chunk_data)
        
        # Expected path: chunks/XX/YY/XXYY...
        expected_path = os.path.join(
            self.store_path, 
            "chunks",
            chunk_hash[:2],
            chunk_hash[2:4],
            chunk_hash
        )
        
        assert os.path.exists(expected_path)
    
    def test_large_chunk(self):
        """Test storing and retrieving a large chunk (1 MiB)"""
        init_storage(self.store_path)
        
        # Create 1 MiB chunk
        chunk_data = b"X" * (1024 * 1024)
        chunk_hash = store_chunk(self.store_path, chunk_data)
        
        # Retrieve and verify
        retrieved = get_chunk(self.store_path, chunk_hash)
        assert len(retrieved) == 1024 * 1024
        assert retrieved == chunk_data


class TestIntegration:
    """Integration tests combining chunking and storage"""
    
    def setup_method(self):
        """Create temporary directories"""
        self.test_dir = tempfile.mkdtemp()
        self.store_path = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary directories"""
        for path in [self.test_dir, self.store_path]:
            if os.path.exists(path):
                shutil.rmtree(path)
    
    def test_chunk_and_store_file(self):
        """Test complete workflow: chunk file and store all chunks"""
        # Create test file (3 MiB)
        test_file = os.path.join(self.test_dir, "test.bin")
        chunk_size = 1024 * 1024
        file_data = b"ABC" * (chunk_size * 3 // 3)  # 3 MiB
        
        with open(test_file, 'wb') as f:
            f.write(file_data)
        
        # Initialize storage
        init_storage(self.store_path)
        
        # Chunk file
        chunks = chunk_file(test_file, chunk_size=chunk_size)
        assert len(chunks) == 3
        
        # Store all chunks and collect hashes
        chunk_hashes = []
        for chunk_data in chunks:
            chunk_hash = store_chunk(self.store_path, chunk_data)
            chunk_hashes.append(chunk_hash)
        
        # Verify all chunks can be retrieved
        for i, chunk_hash in enumerate(chunk_hashes):
            retrieved = get_chunk(self.store_path, chunk_hash)
            assert retrieved == chunks[i]
    
    def test_reconstruct_file_from_chunks(self):
        """Test reconstructing a file from stored chunks"""
        # Create test file
        test_file = os.path.join(self.test_dir, "original.txt")
        original_data = b"This is a test file for reconstruction." * 1000
        
        with open(test_file, 'wb') as f:
            f.write(original_data)
        
        # Initialize storage
        init_storage(self.store_path)
        
        # Chunk and store
        chunks = chunk_file(test_file, chunk_size=1024)
        chunk_hashes = [store_chunk(self.store_path, chunk) for chunk in chunks]
        
        # Reconstruct file from chunks
        reconstructed_data = b""
        for chunk_hash in chunk_hashes:
            reconstructed_data += get_chunk(self.store_path, chunk_hash)
        
        # Verify reconstruction
        assert reconstructed_data == original_data
    
    def test_deduplication_across_files(self):
        """Test deduplication when multiple files share chunks"""
        init_storage(self.store_path)
        
        # Create two files with some shared content
        chunk_size = 1024
        shared_data = b"SHARED" * (chunk_size // 6)
        
        file1_data = shared_data + b"FILE1" * (chunk_size // 5)
        file2_data = shared_data + b"FILE2" * (chunk_size // 5)
        
        file1 = os.path.join(self.test_dir, "file1.bin")
        file2 = os.path.join(self.test_dir, "file2.bin")
        
        with open(file1, 'wb') as f:
            f.write(file1_data)
        with open(file2, 'wb') as f:
            f.write(file2_data)
        
        # Chunk both files
        chunks1 = chunk_file(file1, chunk_size=chunk_size)
        chunks2 = chunk_file(file2, chunk_size=chunk_size)
        
        # Store chunks from file1
        hashes1 = [store_chunk(self.store_path, chunk) for chunk in chunks1]
        
        # Count chunks before storing file2
        chunks_dir = os.path.join(self.store_path, "chunks")
        files_before = sum(len(files) for _, _, files in os.walk(chunks_dir))
        
        # Store chunks from file2
        hashes2 = [store_chunk(self.store_path, chunk) for chunk in chunks2]
        
        # Count chunks after storing file2
        files_after = sum(len(files) for _, _, files in os.walk(chunks_dir))
        
        # First chunks should be identical (shared data)
        assert hashes1[0] == hashes2[0]
        
        # Should have deduplicated the shared chunk
        assert files_after < files_before + len(chunks2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])