"""
Default data files for LeetCode Tools.
"""
import os

def get_data_path(filename: str) -> str:
    """Get the path to a data file."""
    return os.path.join(os.path.dirname(__file__), filename)