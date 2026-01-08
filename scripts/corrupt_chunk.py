"""
Script to corrupt a chunk file for Demo 2
Simulates disk corruption / bit-rot by modifying 1 byte in a chunk file
"""

import os
import sys
import hashlib
from pathlib import Path


def find_chunk_file(store_path):
    """Find the first chunk file in the store"""
    chunks_dir = os.path.join(store_path, "chunks")
    
    if not os.path.exists(chunks_dir):
        print(f"❌ Chunks directory not found: {chunks_dir}")
        return None
    
    # Walk through chunks directory to find first file
    for root, dirs, files in os.walk(chunks_dir):
        if files:
            chunk_file = os.path.join(root, files[0])
            return chunk_file
    
    return None


def compute_hash(file_path):
    """Compute SHA-256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def corrupt_chunk(chunk_file, position=100, new_byte=0xFF):
    """
    Corrupt a chunk file by modifying one byte
    
    Args:
        chunk_file: Path to chunk file
        position: Byte position to modify (default: 100)
        new_byte: New byte value (default: 0xFF)
    """
    print("\n" + "=" * 70)
    print("  CHUNK CORRUPTION SCRIPT - Demo 2")
    print("=" * 70)
    
    # 1. Show original file info
    print(f"\n🔍 Target chunk file:")
    print(f"   Path: {chunk_file}")
    
    file_size = os.path.getsize(chunk_file)
    print(f"   Size: {file_size:,} bytes")
    
    # Get original hash from filename
    original_hash = Path(chunk_file).stem
    print(f"   Expected hash: {original_hash}")
    
    # 2. Compute actual hash before corruption
    print(f"\n📊 Computing hash before corruption...")
    actual_hash_before = compute_hash(chunk_file)
    print(f"   Actual hash: {actual_hash_before}")
    
    if original_hash == actual_hash_before:
        print(f"   Status: ✅ VALID (hash matches)")
    else:
        print(f"   Status: ⚠️ Already corrupted or hash mismatch")
    
    # 3. Read file
    print(f"\n⚠️  Corrupting chunk file...")
    with open(chunk_file, 'r+b') as f:
        # Read all bytes
        data = bytearray(f.read())
        
        # Check position is valid
        if position >= len(data):
            print(f"❌ Error: Position {position} is beyond file size {len(data)}")
            return False
        
        # Save original byte
        original_byte = data[position]
        print(f"   Position: {position}")
        print(f"   Original byte: 0x{original_byte:02X}")
        
        # Modify byte
        data[position] = new_byte
        print(f"   Modified byte: 0x{new_byte:02X}")
        
        # Write back
        f.seek(0)
        f.write(data)
        f.truncate()
    
    print(f"   ✓ Byte at position {position} has been modified")
    
    # 4. Verify corruption
    print(f"\n📊 Computing hash after corruption...")
    actual_hash_after = compute_hash(chunk_file)
    print(f"   New hash: {actual_hash_after}")
    
    # 5. Show result
    print(f"\n" + "=" * 70)
    print(f"  CORRUPTION RESULT")
    print(f"=" * 70)
    print(f"  Expected hash: {original_hash}")
    print(f"  Actual hash:   {actual_hash_after}")
    
    if original_hash != actual_hash_after:
        print(f"  Status:        CORRUPTED ❌")
        print(f"\n✅ Corruption successful! Chunk file has been modified.")
        print(f"=" * 70)
        return True
    else:
        print(f"  Status:        UNCHANGED ⚠️")
        print(f"\n⚠️  Warning: Hash did not change (unexpected)")
        print(f"=" * 70)
        return False


def main():
    """Main function"""
    # Get store path from command line or use default
    if len(sys.argv) > 1:
        store_path = sys.argv[1]
    else:
        store_path = "store"
    
    print(f"Store path: {store_path}")
    
    # Find a chunk file
    print(f"\n🔍 Searching for chunk files...")
    chunk_file = find_chunk_file(store_path)
    
    if not chunk_file:
        print(f"❌ No chunk files found in {store_path}/chunks/")
        print(f"\nPlease ensure you have created a backup first:")
        print(f"  python -m src.cli.main backup dataset/ --store {store_path}/")
        return 1
    
    print(f"✓ Found chunk file: {chunk_file}")
    
    # Corrupt the chunk
    success = corrupt_chunk(chunk_file, position=100, new_byte=0xFF)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
