#!/usr/bin/env python3

"""
Cleanup Script for Worker Data Directory
Removes macOS hidden files and other problematic files
"""

import os
import sys
from pathlib import Path

def cleanup_macos_files(directory):
    """Remove macOS hidden files from a directory"""
    directory = Path(directory)
    removed_files = []
    
    if not directory.exists():
        print(f"Directory does not exist: {directory}")
        return removed_files
    
    # Patterns to remove
    patterns_to_remove = [
        "._*",           # macOS resource fork files
        ".DS_Store",     # macOS directory metadata
        "*.tmp",         # Temporary files
        "*~",            # Backup files
    ]
    
    for pattern in patterns_to_remove:
        for file_path in directory.rglob(pattern):
            if file_path.is_file():
                try:
                    file_path.unlink()
                    removed_files.append(str(file_path))
                    print(f"Removed: {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
    
    return removed_files

def main():
    """Main cleanup function"""
    print("🧹 Worker Data Directory Cleanup")
    print("=" * 40)
    
    # Get the worker data directory
    script_dir = Path(__file__).parent
    worker_data_dir = script_dir / "worker" / "data"
    
    if not worker_data_dir.exists():
        print("📁 Worker data directory not found, creating it...")
        worker_data_dir.mkdir(parents=True, exist_ok=True)
        (worker_data_dir / "tasks").mkdir(exist_ok=True)
        (worker_data_dir / "results").mkdir(exist_ok=True)
        print("✅ Worker data directory structure created")
        return
    
    print(f"📁 Cleaning up directory: {worker_data_dir}")
    
    # Clean up each subdirectory
    subdirs = ["tasks", "results", "logs"]
    total_removed = 0
    
    for subdir in subdirs:
        subdir_path = worker_data_dir / subdir
        if subdir_path.exists():
            print(f"\n🔍 Checking {subdir}/")
            removed = cleanup_macos_files(subdir_path)
            total_removed += len(removed)
            if removed:
                print(f"   Removed {len(removed)} files")
            else:
                print(f"   No problematic files found")
        else:
            print(f"\n📁 Creating {subdir}/")
            subdir_path.mkdir(exist_ok=True)
    
    # Also clean the main data directory
    print(f"\n🔍 Checking main data directory")
    removed = cleanup_macos_files(worker_data_dir)
    total_removed += len(removed)
    
    print(f"\n📊 Summary:")
    print(f"   Total files removed: {total_removed}")
    
    if total_removed > 0:
        print("✅ Cleanup completed successfully!")
    else:
        print("✅ No cleanup needed - directory is clean!")
    
    print("\n💡 You can now restart the worker service:")
    print("   python3 -m worker")

if __name__ == "__main__":
    main()
