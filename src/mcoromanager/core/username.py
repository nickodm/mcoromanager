from pathlib import Path
from os import remove

__all__: tuple[str] = ("txt_path", "load", "save")

txt_path: Path = Path("~/.mcoromanager/user_name.txt").expanduser()

def load() -> str | None:
    """Load the user's name.

    :return str | None: The user's name, if exists.
    """
    if not txt_path.exists():
        return None
    
    with txt_path.open(encoding="utf-8") as fp:
        s = fp.read()
        
    if "\n" in s:
        remove(s)
        return None
    
    return s

def save(name: str) -> None:
    """Save the user's name.

    :param str name: The user's name.
    """
    if not txt_path.parent.exists():
        txt_path.parent.mkdir()
    
    with txt_path.open("w", encoding="utf-8") as fp:
        fp.write(name)

def delete() -> None:
    """Delete the saved user's name."""
    if not txt_path.exists():
        return
    
    remove(txt_path)