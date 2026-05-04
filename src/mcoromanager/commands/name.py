from argparse import Namespace

from ..core import *

def get() -> int:
    """Handle the `get` subcommand.

    :return int: Exit code.
    """
    name = username.load()
    
    if name is None:
        printerr("There isn't a saved user name.")
        return 1
    
    print(f"The user name is: [bold blue]\"{name}\".")
    return 0

def set(name: str) -> int:
    """Handle the `set` subcommand.

    :param str name: The user's name.
    :return int: Exit code.
    """
    username.save(name)
    print(CHECK + "The new user name was saved.")
    return 0

def delete() -> int:
    """Handle the `delete` subcommand.

    :return int: Exit code.
    """
    username.delete()
    print(CHECK + "Deleted username.")
    return 0   

def main(args: Namespace) -> int:
    """Handle the "new" command.

    :param Namespace args: The parsed args.
    :return int: Exit code.
    """
    match args.name_cmd:
        case "get":
            return get()
            
        case "set":
            return set(args.name)
            
        case "delete":
            return delete()

    return 0
