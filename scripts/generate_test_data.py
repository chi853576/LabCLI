#!/usr/bin/env python3
"""
Generate test dataset for backup system.
Creates 2000 files totaling ~200MB.
"""

import os
import random
import string

def random_text(size):
    """Generate random text data"""
    return ''.join(random.choices(string.ascii_letters + string.digits + '\n ', k=size))

def random_binary(size):
    """Generate random binary data"""
    return os.urandom(size)

def generate_test_data(output_dir="dataset", num_files=2000, total_size_mb=200):
    """
    Generate test dataset.
    
    Args:
        output_dir: Output directory
        num_files: Number of files to create
        total_size_mb: Total size in MB
    """
    os.makedirs(output_dir, exist_ok=True)
    
    total_size = total_size_mb * 1024 * 1024  # Convert to bytes
    avg_size = total_size // num_files
    
    print(f"Generating {num_files} files (~{total_size_mb}MB total)...")
    
    # Create subdirectories
    subdirs = ['docs', 'images', 'data', 'config', 'logs']
    for subdir in subdirs:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)
    
    files_created = 0
    
    for i in range(num_files):
        # Vary file size (50% to 150% of average)
        size = random.randint(int(avg_size * 0.5), int(avg_size * 1.5))
        
        # Choose file type (now includes config)
        file_type = random.choice(['text', 'binary', 'json', 'log', 'config'])
        
        if file_type == 'text':
            subdir = 'docs'
            ext = '.txt'
            data = random_text(size).encode('utf-8')
        elif file_type == 'binary':
            subdir = 'images'
            ext = '.bin'
            data = random_binary(size)
        elif file_type == 'json':
            subdir = 'data'
            ext = '.json'
            # Generate simple JSON
            json_data = '{"id": %d, "data": "%s"}' % (i, random_text(size - 50))
            data = json_data.encode('utf-8')
        elif file_type == 'config':
            subdir = 'config'
            ext = '.cfg'
            # Generate config-like data
            config_data = f"[section_{i}]\n" + random_text(size - 20)
            data = config_data.encode('utf-8')
        else:  # log
            subdir = 'logs'
            ext = '.log'
            data = random_text(size).encode('utf-8')
        
        filename = f"file_{i:04d}{ext}"
        filepath = os.path.join(output_dir, subdir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(data)
        
        files_created += 1
        
        if (i + 1) % 200 == 0:
            print(f"  Created {i + 1}/{num_files} files...")
    
    print(f"✓ Done! Created {files_created} files in '{output_dir}/'")
    
    # Print statistics
    total_actual_size = sum(
        os.path.getsize(os.path.join(root, file))
        for root, dirs, files in os.walk(output_dir)
        for file in files
    )
    
    print(f"  Total size: {total_actual_size / (1024*1024):.2f} MB")
    print(f"  Files: {files_created}")
    print(f"  Subdirectories: {len(subdirs)}")

if __name__ == "__main__":
    generate_test_data()
