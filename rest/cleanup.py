import os
import shutil

# File extensions and directory names to clean
TEMP_FILE_EXTENSIONS = ['.pyc', '.pyo', '.log', '.tmp']
TEMP_DIR_NAMES = ['__pycache__', '.pytest_cache', '.mypy_cache', '.cache']


def cleanup(root_dir):
    """Recursively delete __pycache__ and temp files from the project."""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove temp directories
        for temp_dir in TEMP_DIR_NAMES:
            temp_dir_path = os.path.join(dirpath, temp_dir)
            if os.path.isdir(temp_dir_path):
                print(f"Removing directory: {temp_dir_path}")
                shutil.rmtree(temp_dir_path, ignore_errors=True)
        # Remove temp files
        for filename in filenames:
            if any(filename.endswith(ext) for ext in TEMP_FILE_EXTENSIONS):
                file_path = os.path.join(dirpath, filename)
                print(f"Removing file: {file_path}")
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")

if __name__ == "__main__":
    cleanup(os.path.dirname(os.path.abspath(__file__)))
    print("Cleanup complete.") 