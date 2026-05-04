from argparse import ArgumentParser
from pathlib import Path

from .core import *
from . import commands

from . import __version__

def init_parser() -> ArgumentParser:
    """Initialize the argument parser."""
    def abs_path(p: Path) -> Path:
        return Path(p).expanduser().absolute()
    
    parser = ArgumentParser(
        prog="mcoromanager",
        description="A simple program to handle directories created by students "
                    "to do the Moisés Coronado's tasks.",
        epilog="Copyright (c) 2026 Nicolás Miranda Colivoro. MIT License."
    )

    parser.add_argument("-v", "--version", action='version', version=__version__)

    subparsers = parser.add_subparsers(title="subcommands", required=True, dest="command")
    
    #* ----- NEW -----
    cmd_new = subparsers.add_parser("init", help="create folders to do coronado's tasks",
                                    description="Create a single folder for each task in the "
                                                "current working directory.")
    cmd_new.add_argument("start", help="the first task", type=int)
    cmd_new.add_argument("stop", help="the last task", type=int)
    cmd_new.add_argument("--no-git", action='store_false', dest="git", 
                         help="don't create git repositories for each task")
    cmd_new.add_argument("-f", "--force", action="store_true", help="force the directory creation")
    cmd_new.add_argument("-p", "--path", help="the dir's path, defaults to the current working "
                                              "directory", type=abs_path, default=Path.cwd())

    #* ----- DONE -----
    cmd_md5 = subparsers.add_parser("done", help="verify the folder's format and calculate the MD5",
                                    description="Verify the folder's format, zip it to .7z and "
                                                "calculate and save the folder's MD5.")
    cmd_md5.add_argument("-p", "--path", help="the dir's path, defaults to the current working "
                                              "directory", type=abs_path, default=Path.cwd())

    #* ----- NAME -----
    cmd_name = subparsers.add_parser("name", help="set, get or delete the name to save files",
                                     description="Set, get or delete the name to save files.")
    
    cmd_name_sub = cmd_name.add_subparsers(title="subcommands", required=True, dest="name_cmd")
    
    cmd_name_set = cmd_name_sub.add_parser("set", help="set the user's name")
    cmd_name_set.add_argument("name", type=str)
    
    cmd_name_sub.add_parser("get", help="get the user's name")
    cmd_name_sub.add_parser("delete", help="delete the user's name")
    
    return parser

def main() -> int:
    parser = init_parser()
    args = parser.parse_args()
    
    match args.command:
        case "init":
            return commands.init(args.path, args.start, args.stop, args.git, args.force)
        
        case "done":
            return commands.done(args.path)
        
        case "name":
            return commands.name(args)
    
    return 0

def run() -> int:
    try:
        return main()
    except KeyboardInterrupt:
        printerr("Process killed by the user.")
        return 1
    except Exception:
        err.print_exception()
        return 1

if __name__ == "__main__":
    exit(run())