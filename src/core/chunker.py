"""
File chunking module - MEMBER 1

Responsibilities:
- Split files into 1 MiB chunks
- Compute SHA-256 hash for each chunk

Reference: src/interfaces.py
"""

import os
from typing import List
import sys

# Import hash utility
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.hash import compute_sha256


def chunk_file(file_path: str, chunk_size: int = 1*1024*1024) -> List[bytes]:
    """
    Split file into fixed-size chunks.
    
    Args:
        file_path: Path to the file to chunk
        chunk_size: Size of each chunk in bytes (default 1 MiB = 1,048,576 bytes)
    
    Returns:
        List of chunk data (bytes)
    
    Raises:
        FileNotFoundError: If file does not exist
        IOError: If file cannot be read
    
    Example:
        >>> chunks = chunk_file("dataset/file.txt")
        >>> len(chunks)
        3
        >>> len(chunks[0])
        1048576
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {file_path}")
    
    chunks = []
    
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk_data = f.read(chunk_size)
                if not chunk_data:
                    break
                chunks.append(chunk_data)
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")
    
    return chunks


def hash_chunk(chunk_data: bytes) -> str:
    """
    Compute SHA-256 hash of chunk.
    
    Args:
        chunk_data: Chunk data as bytes
    
    Returns:
        SHA-256 hash as hex string (64 characters)
    
    Example:
        >>> hash_chunk(b"Hello World")
        'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e'
    """
    if not isinstance(chunk_data, bytes):
        raise TypeError(f"chunk_data must be bytes, got {type(chunk_data)}")
    
    return compute_sha256(chunk_data)