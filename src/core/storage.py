"""
Content-addressable storage module - MEMBER 1

Responsibilities:
- Store chunks by hash (store/chunks/XX/XXXXXX...)
- Deduplication: don't store duplicate chunks
- Retrieve chunks by hash

Reference: src/interfaces.py
"""

import os
import sys

# Import hash utility
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.hash import compute_sha256


def init_storage(store_path: str) -> None:
    """
    Initialize storage directory structure.
    Creates: store_path/chunks/ directory
    
    Args:
        store_path: Path to backup store
    
    Example:
        >>> init_storage("store")
        # Creates: store/chunks/
    """
    chunks_dir = os.path.join(store_path, "chunks")
    os.makedirs(chunks_dir, exist_ok=True)


def _get_chunk_path(store_path: str, chunk_hash: str) -> str:
    """
    Get the file path for a chunk based on its hash.
    
    Uses first 2 characters of hash as subdirectory for better filesystem performance.
    Path format: store_path/chunks/XX/XXXXXX...
    
    Args:
        store_path: Path to backup store
        chunk_hash: SHA-256 hash of chunk (64 hex characters)
    
    Returns:
        Full path to chunk file
    
    Example:
        >>> _get_chunk_path("store", "abcd1234...")
        'store/chunks/ab/cd/abcd1234...'
    """
    if len(chunk_hash) < 4:
        raise ValueError(f"Invalid chunk hash (too short): {chunk_hash}")
    
    # Use first 2 chars as first level, next 2 chars as second level
    subdir1 = chunk_hash[:2]
    subdir2 = chunk_hash[2:4]
    
    return os.path.join(store_path, "chunks", subdir1, subdir2, chunk_hash)


def store_chunk(store_path: str, chunk_data: bytes) -> str:
    """
    Store chunk in content-addressable storage.
    Storage path: store_path/chunks/XX/YY/XXYY... (first 4 chars of hash as subdirectories)
    
    Deduplication: If chunk with same hash already exists, don't write again.
    
    Args:
        store_path: Path to backup store
        chunk_data: Chunk data to store
    
    Returns:
        SHA-256 hash of the chunk
    
    Example:
        >>> chunk_hash = store_chunk("store", b"Hello World")
        >>> print(chunk_hash)
        'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e'
    """
    if not isinstance(chunk_data, bytes):
        raise TypeError(f"chunk_data must be bytes, got {type(chunk_data)}")
    
    # Compute hash of chunk
    chunk_hash = compute_sha256(chunk_data)
    
    # Get chunk file path
    chunk_path = _get_chunk_path(store_path, chunk_hash)
    
    # Deduplication: if chunk already exists, skip writing
    if os.path.exists(chunk_path):
        return chunk_hash
    
    # Create parent directories if they don't exist
    os.makedirs(os.path.dirname(chunk_path), exist_ok=True)
    
    # Write chunk data to file
    # Use atomic write: write to temp file, then rename
    temp_path = chunk_path + ".tmp"
    try:
        with open(temp_path, 'wb') as f:
            f.write(chunk_data)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
        
        # Atomic rename
        os.rename(temp_path, chunk_path)
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise IOError(f"Failed to store chunk {chunk_hash}: {e}")
    
    return chunk_hash


def get_chunk(store_path: str, chunk_hash: str) -> bytes:
    """
    Retrieve chunk data by hash.
    
    Args:
        store_path: Path to backup store
        chunk_hash: SHA-256 hash of chunk
    
    Returns:
        Chunk data as bytes
    
    Raises:
        FileNotFoundError: If chunk does not exist
    
    Example:
        >>> data = get_chunk("store", "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e")
        >>> print(data)
        b'Hello World'
    """
    chunk_path = _get_chunk_path(store_path, chunk_hash)
    
    if not os.path.exists(chunk_path):
        raise FileNotFoundError(f"Chunk not found: {chunk_hash}")
    
    try:
        with open(chunk_path, 'rb') as f:
            chunk_data = f.read()
    except IOError as e:
        raise IOError(f"Failed to read chunk {chunk_hash}: {e}")
    
    # Verify integrity: recompute hash and compare
    actual_hash = compute_sha256(chunk_data)
    if actual_hash != chunk_hash:
        raise ValueError(
            f"Chunk integrity check failed for {chunk_hash}: "
            f"expected {chunk_hash}, got {actual_hash}"
        )
    
    return chunk_data


def chunk_exists(store_path: str, chunk_hash: str) -> bool:
    """
    Check if chunk exists in storage.
    
    Args:
        store_path: Path to backup store
        chunk_hash: SHA-256 hash of chunk
    
    Returns:
        True if chunk exists, False otherwise
    
    Example:
        >>> chunk_exists("store", "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e")
        True
    """
    chunk_path = _get_chunk_path(store_path, chunk_hash)
    return os.path.exists(chunk_path)