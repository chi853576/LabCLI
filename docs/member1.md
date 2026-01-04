# MEMBER 1: STORAGE & CHUNKING - IMPLEMENTATION NOTES

**Completed by:** Member 1  
**Date:** 2026-01-04

---

## OVERVIEW

Implementation bao gồm 3 files chính:
1. `src/core/chunker.py` - File chunking functionality
2. `src/core/storage.py` - Content-addressable storage
3. `tests/test_core/test_storage.py` - Comprehensive unit tests

---

## 1. CHUNKER.PY - FILE CHUNKING

### Functions Implemented:

#### `chunk_file(file_path, chunk_size=1*1024*1024)`
**Purpose:** Split file into fixed-size chunks

**Algorithm:**
1. Open file in binary mode
2. Read `chunk_size` bytes at a time (default 1 MiB)
3. Append each chunk to list
4. Return list of chunks when EOF reached

**Key Features:**
- Fixed chunk size: 1 MiB (1,048,576 bytes)
- Handles files of any size
- Memory efficient: reads incrementally
- Last chunk may be smaller than chunk_size

**Error Handling:**
- FileNotFoundError: if file doesn't exist
- ValueError: if path is not a file
- IOError: if file cannot be read

**Example:**
```python
# File: 2.5 MiB
chunks = chunk_file("dataset/large.bin")
# Returns: [chunk1(1MiB), chunk2(1MiB), chunk3(0.5MiB)]
```

---

#### `hash_chunk(chunk_data)`
**Purpose:** Compute SHA-256 hash of chunk

**Algorithm:**
1. Validate input is bytes type
2. Call `compute_sha256()` from utils.hash
3. Return 64-character hex string

**Key Features:**
- Uses SHA-256 (as required by lab spec)
- Returns lowercase hex string
- Deterministic: same data → same hash

**Example:**
```python
chunk_hash = hash_chunk(b"Hello World")
# Returns: "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
```

---

## 2. STORAGE.PY - CONTENT-ADDRESSABLE STORAGE

### Storage Structure:

```
store/
└── chunks/
    └── XX/           # First 2 chars of hash
        └── YY/       # Next 2 chars of hash
            └── XXYY... (full hash as filename)
```

**Example:**
- Hash: `abcd1234567890...`
- Path: `store/chunks/ab/cd/abcd1234567890...`

**Why this structure?**
- Prevents too many files in single directory (filesystem performance)
- 256 first-level subdirs (00-ff)
- 256 second-level subdirs per first-level
- Max ~65K subdirectories total

---

### Functions Implemented:

#### `init_storage(store_path)`
**Purpose:** Initialize storage directory structure

**Algorithm:**
1. Create `store_path/chunks/` directory
2. Use `os.makedirs(exist_ok=True)` - safe to call multiple times

**Example:**
```python
init_storage("store")
# Creates: store/chunks/
```

---

#### `store_chunk(store_path, chunk_data)`
**Purpose:** Store chunk in content-addressable storage with deduplication

**Algorithm:**
1. Compute SHA-256 hash of chunk_data
2. Generate storage path: `chunks/XX/YY/hash`
3. **Deduplication check:** if file exists, return hash immediately
4. Create parent directories if needed
5. **Atomic write:**
   - Write to temporary file (hash + ".tmp")
   - Flush and fsync to ensure disk write
   - Rename temp file to final name (atomic operation)
6. Return chunk hash

**Key Features:**
- **Deduplication:** Automatic - identical chunks stored only once
- **Atomic writes:** Prevents corruption if process crashes during write
- **fsync():** Ensures data is written to disk before rename
- **Error handling:** Cleans up temp file on failure

**Example:**
```python
hash1 = store_chunk("store", b"Hello")  # Stores chunk
hash2 = store_chunk("store", b"Hello")  # Deduplicated, returns same hash
# hash1 == hash2, only 1 file on disk
```

---

#### `get_chunk(store_path, chunk_hash)`
**Purpose:** Retrieve chunk data by hash

**Algorithm:**
1. Generate chunk file path from hash
2. Check if file exists → FileNotFoundError if not
3. Read chunk data from file
4. **Integrity verification:**
   - Recompute SHA-256 hash of read data
   - Compare with expected hash
   - Raise ValueError if mismatch
5. Return chunk data

**Key Features:**
- **Integrity check:** Detects chunk corruption
- **Tamper detection:** Modified chunks will fail verification

**Example:**
```python
data = get_chunk("store", "a591a6d4...")
# Returns: b"Hello World"

# If chunk was tampered:
# Raises: ValueError("Chunk integrity check failed...")
```

---

#### `chunk_exists(store_path, chunk_hash)`
**Purpose:** Check if chunk exists in storage

**Algorithm:**
1. Generate chunk file path
2. Return `os.path.exists(path)`

**Example:**
```python
exists = chunk_exists("store", "a591a6d4...")
# Returns: True or False
```

---

#### `_get_chunk_path(store_path, chunk_hash)` (Helper)
**Purpose:** Generate file path for chunk

**Algorithm:**
1. Extract first 2 chars: `hash[:2]`
2. Extract next 2 chars: `hash[2:4]`
3. Build path: `store_path/chunks/XX/YY/hash`

**Example:**
```python
path = _get_chunk_path("store", "abcd1234...")
# Returns: "store/chunks/ab/cd/abcd1234..."
```

---

## 3. DESIGN DECISIONS

### Chunk Size: 1 MiB (1,048,576 bytes)
**Rationale:**
- Efficient deduplication (small changes → few chunks affected)
- Low memory footprint (only 1 MiB in memory at a time)
- Fast verification (can verify chunks in parallel)
- Good balance between overhead and efficiency

### Content-Addressable Storage
**Rationale:**
- Hash as filename → automatic deduplication
- Immutable: hash changes if content changes
- Enables integrity verification
- Industry standard (Git, Docker, etc.)

### Directory Structure (XX/YY/)
**Rationale:**
- Filesystem performance: many filesystems slow down with >10K files in one directory
- 2-level hierarchy: max 256×256 = 65,536 subdirectories
- Each subdirectory holds fewer chunks → faster lookup

### Atomic Writes with fsync()
**Rationale:**
- Prevents corruption if process crashes during write
- Write to temp file → fsync → rename (atomic)
- Rename is atomic operation on POSIX systems
- Ensures crash consistency

### Integrity Verification on Read
**Rationale:**
- Detects silent data corruption (bit rot)
- Detects tampering
- Small overhead (SHA-256 is fast)
- Critical for restore reliability

---

## 4. TESTING

### Test Coverage:

**Chunker Tests:**
- Small files (< 1 MiB)
- Exact chunk size (= 1 MiB)
- Multiple chunks (> 1 MiB)
- Empty files
- Non-existent files
- Hash computation correctness

**Storage Tests:**
- Storage initialization
- Store and retrieve
- Deduplication
- Chunk existence check
- Non-existent chunk retrieval
- Directory structure verification
- Large chunks (1 MiB)

**Integration Tests:**
- Complete workflow: chunk → store → retrieve
- File reconstruction from chunks
- Deduplication across multiple files

### Running Tests:

```bash
# Run all tests
pytest tests/test_core/test_storage.py -v

# Run specific test class
pytest tests/test_core/test_storage.py::TestChunker -v

# Run with coverage
pytest tests/test_core/test_storage.py --cov=src.core
```

---

## 5. EXAMPLE USAGE

### Complete Backup Workflow (Member 1 Part):

```python
from src.core.chunker import chunk_file, hash_chunk
from src.core.storage import init_storage, store_chunk

# Setup
store_path = "store"
init_storage(store_path)

# Chunk file
file_path = "dataset/document.pdf"
chunks = chunk_file(file_path)  # List of bytes

# Store chunks and collect hashes
chunk_hashes = []
for chunk_data in chunks:
    chunk_hash = store_chunk(store_path, chunk_data)
    chunk_hashes.append(chunk_hash)

print(f"Stored {len(chunks)} chunks")
print(f"Chunk hashes: {chunk_hashes}")
```

### Complete Restore Workflow (Member 1 Part):

```python
from src.core.storage import get_chunk

# Given list of chunk hashes from manifest
chunk_hashes = ["a591a6d4...", "b7c2e8f1...", ...]

# Reconstruct file
file_data = b""
for chunk_hash in chunk_hashes:
    chunk_data = get_chunk(store_path, chunk_hash)
    file_data += chunk_data

# Write reconstructed file
with open("restored/document.pdf", 'wb') as f:
    f.write(file_data)
```

---

## 6. INTEGRATION WITH OTHER MEMBERS

### Member 2 (Manifest & Merkle) will use:
- `chunk_file()` - to chunk files during backup
- `store_chunk()` - to store chunks and get hashes
- `chunk_exists()` - to verify chunks before creating manifest

### Member 3 (CLI) will use:
- `init_storage()` - in `cmd_init()`
- `chunk_file()` + `store_chunk()` - in `cmd_backup()`
- `get_chunk()` - in `cmd_restore()`

### Member 4 (Security) will use:
- Storage is independent of security layer
- No direct integration needed

---

## 7. PERFORMANCE CHARACTERISTICS

### Time Complexity:
- `chunk_file()`: O(n) where n = file size
- `hash_chunk()`: O(m) where m = chunk size (1 MiB)
- `store_chunk()`: O(1) with dedup check, O(m) for first store
- `get_chunk()`: O(m) for read + hash verification
- `chunk_exists()`: O(1) filesystem lookup

### Space Complexity:
- Memory: O(1) - only one chunk in memory at a time
- Disk: O(n) where n = unique data size (deduplication reduces this)

### Deduplication Savings:
Example: 10 snapshots of 1 GB dataset with 10% change per snapshot
- Without dedup: 10 GB storage
- With dedup: ~1 GB + 9×0.1 GB = ~1.9 GB storage
- Savings: ~80%

---

## 8. ERROR HANDLING

### Chunker Errors:
- `FileNotFoundError`: File doesn't exist
- `ValueError`: Path is not a file
- `IOError`: File cannot be read
- `TypeError`: chunk_data is not bytes

### Storage Errors:
- `FileNotFoundError`: Chunk not found in storage
- `ValueError`: Chunk integrity check failed (corruption/tampering)
- `IOError`: Failed to read/write chunk

### Recovery:
- All errors are propagated to caller
- Atomic writes ensure no partial chunks
- Temp files cleaned up on error

---

## 9. LIMITATIONS & ASSUMPTIONS

### Limitations:
1. Fixed chunk size (1 MiB) - not configurable at runtime
2. No compression (can be added later)
3. No encryption (security layer is separate)
4. Single-threaded (can be parallelized for large files)

### Assumptions:
1. Filesystem supports atomic rename
2. SHA-256 collisions are negligible
3. Sufficient disk space for chunks
4. File content doesn't change during chunking

---

## 10. FUTURE IMPROVEMENTS

### Possible Enhancements:
1. **Variable chunk size:** Content-defined chunking for better deduplication
2. **Compression:** Compress chunks before storage
3. **Parallel chunking:** Multi-threaded chunking for large files
4. **Garbage collection:** Remove unreferenced chunks
5. **Chunk caching:** LRU cache for frequently accessed chunks
6. **Statistics:** Track deduplication ratio, storage savings

---

## 11. DELIVERABLES CHECKLIST

- `src/core/chunker.py` - Fully implemented
- `src/core/storage.py` - Fully implemented
- `tests/test_core/test_storage.py` - Comprehensive tests
- All functions match interface signatures in `src/interfaces.py`
- Error handling implemented
- Atomic writes with fsync()
- Deduplication working
- Integrity verification on read
- Documentation and examples
- Unit tests passing

---

## 12. NOTES FOR OTHER MEMBERS

### For Member 2 (Manifest & Merkle):
- Use `chunk_file()` to get chunks, then `store_chunk()` to get hashes
- Build manifest with chunk_hashes in order
- Verify chunks exist before creating snapshot

### For Member 3 (CLI):
- Call `init_storage()` once in `cmd_init()`
- For backup: iterate through files, chunk, store, collect hashes
- For restore: use manifest to get chunk_hashes, then `get_chunk()` to reconstruct

### For Member 4 (Security):
- No direct dependency on storage layer
- Audit log should record backup/restore operations
- Storage operations don't need permission checks

---

## CONCLUSION

Member 1's implementation provides a solid foundation for the backup system:
- Reliable chunking with fixed 1 MiB size
- Content-addressable storage with automatic deduplication
- Integrity verification to detect corruption/tampering
- Atomic writes for crash consistency
- Comprehensive test coverage

The implementation follows best practices from production backup systems (e.g., Borg, Restic, Duplicity) and is ready for integration with other members' work.