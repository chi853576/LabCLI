"""
Unit tests for manifest module - MEMBER 2

Test coverage:
- create_manifest() - canonical ordering
- serialize_manifest() - deterministic
- hash_manifest() - deterministic
"""

# Cách chạy tests: Nhập lệnh trong terminal ở thư mục gốc LabCLI
#     python -m pytest tests/test_core/test_manifest.py 

import pytest
from src.core.manifest import create_manifest, serialize_manifest, hash_manifest
from src.interfaces import FileEntry

# TODO: Implement tests
def test_create_manifest_canonical_ordering():
    entries = [
        FileEntry(path="b.txt", chunks=["chunk2", "chunk3"]),
        FileEntry(path="a.txt", chunks=["chunk1"]),
        FileEntry(path="c.txt", chunks=["chunk4", "chunk5", "chunk6"]),
    ]
    
    manifest = create_manifest(entries)
    
    expected_paths = ["a.txt", "b.txt", "c.txt"]
    actual_paths = [file["path"] for file in manifest["files"]]
    
    assert actual_paths == expected_paths, "Files should be sorted by path"

def test_serialize_manifest_deterministic():
    manifest = {
        "files": [
            {"path": "a.txt", "chunks": ["chunk1"]},
            {"path": "b.txt", "chunks": ["chunk2", "chunk3"]},
        ]
    }
    
    serialized1 = serialize_manifest(manifest)
    serialized2 = serialize_manifest(manifest)
    
    assert serialized1 == serialized2, "Serialization should be deterministic"

def test_hash_manifest_deterministic():
    manifest = {
        "files": [
            {"path": "a.txt", "chunks": ["chunk1"]},
            {"path": "b.txt", "chunks": ["chunk2", "chunk3"]},
        ]
    }
    
    hash1 = hash_manifest(manifest)
    hash2 = hash_manifest(manifest)
    assert hash1 == hash2, "Hashing should be deterministic"
