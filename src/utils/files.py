import os
from typing import Generator, List


def ensure_dir(path: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.

    Parameters
    ----------
    path : str
        The path to the directory.
    """
    os.makedirs(path, exist_ok=True)


def find_files(directory: str, extensions: List[str]) -> Generator[str, None, None]:
    """
    Find all files in a directory with the given extensions.

    Parameters
    ----------
    directory : str
        The directory to search.
    extensions : List[str]
        A list of file extensions to find (e.g., ['.pdf', '.png']).

    Yields
    -------
    Generator[str, None, None]
        A generator of paths to the found files.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                yield os.path.join(root, file)
