"""
Hash utilities for the backup system.

This module provides SHA-256 hashing functions used throughout the system.
"""

import hashlib


def compute_sha256(data: bytes) -> str:
    """
    Compute SHA-256 hash of data.
    
    Args:
        data: Data to hash (bytes)
    
    Returns:
        SHA-256 hash as hex string (64 characters)
    
    Example:
        >>> compute_sha256(b"Hello World")
        'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e'
    """
    return hashlib.sha256(data).hexdigest()
