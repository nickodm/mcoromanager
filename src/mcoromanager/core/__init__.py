from py7zr import SevenZipFile
from io import BytesIO
from pathlib import Path
from hashlib import md5
from subprocess import run as runcmd
from re import compile

__all__ = ("username", "compress_7z", "calculate_md5", "new_task_dir", "dir_is_empty",
           "is_valid_task_name", "is_git_installed")

from . import username

TASK_NAME_PATTERN = compile(r"^Tarea_[1-9]+\d*$")

def compress_7z(path: Path, root: str) -> bytes:
    """Compress the folder at `path` in 7zip and return it as bytes.

    :param Path path: the original folder's path
    :param str root: the root of the compressed folder
    :return bytes: The compressed folder
    """
    buffer = BytesIO()
    
    with SevenZipFile(buffer, mode="w") as zipfile:
        for item in path.iterdir():
            if item.is_dir():
                zipfile.writeall(item, root + "/" + item.stem)
            else:
                zipfile.write(item, root + "/" + item.name)
    
    buffer.seek(0)
    return buffer.read()

def calculate_md5(b: bytes) -> str:
    """Calculate the MD5 of the given bytes and return it as a string.

    :param bytes b: The bytes
    :return str: The MD5 as a string
    """
    return md5(b).hexdigest()

def new_task_dir(number: int, git: bool, parent: Path, force: bool = False) -> int:
    path: Path = parent / f"Tarea_{number}"
    
    if not force and path.exists():
        return 1
    
    try:
        path.mkdir(exist_ok=True)
    except PermissionError:
        return 126
    except FileNotFoundError:
        return 127
    
    if not git:
        return 0
    
    return runcmd(["git", "init"], cwd=path, capture_output=True).returncode

def dir_is_empty(path: Path) -> bool:
    """Whether the directory at `path` is empty.

    :param Path path:
    :return bool:
    """
    if not path.exists():
        return True
    
    if not path.is_dir():
        return False
    
    for _ in path.iterdir():
        # If the dir is empty, the loop will no run.
        return False
    
    return True

def is_valid_task_name(task_name: str) -> bool:
    """Whether the task name is valid according to the format required bt the professor.

    :param str task_name:
    :return bool:
    """
    return TASK_NAME_PATTERN.match(task_name) is not None

def is_git_installed() -> bool:
    """Whether Git is installed in the computer."""
    try:
        return runcmd(['git', '--version'], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False