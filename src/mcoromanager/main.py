from argparse import ArgumentParser, Namespace
from subprocess import run as runcmd
from rich.console import Console
from rich.prompt import Confirm, Prompt, IntPrompt
from pathlib import Path

from .core import *
from . import __version__

CHECK: str = ":white_heavy_check_mark:" # Emoji

console = Console()
print = console.print

err = Console(stderr=True, style="bold red")
printerr = err.print

subjects: tuple[str] = (
    "TIC",      # Tecnologías de la Información
    "HPROGRA",  # Herramientas de Programación
    "IDB",      # Introducción a las Bases de Datos
    "PROGRA",   # Programación
    "HDB",      # Herramientas de Bases de Datos
    "GDB",      # Gestión de Bases de Datos
    "TSI",      # Tecnología y Sistemas de Información
    "DST"       # Desarrollo de Soluciones Tecnológicas
)


def init_parser() -> ArgumentParser:
    """Initialize the argument parser."""
    def abs_path(p: Path) -> Path:
        return p.expanduser().absolute()
    
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

def cmd_init(path: Path, start: int, stop: int, git: bool, force: bool) -> int:
    if git and not is_git_installed():
        print(":warning: [bold orange]Warning: Git was not found, so the folders will be created "
              "without repositories.")
        git = False
    
    if not force and path.exists() and not dir_is_empty(path):
        printerr(f"Error: The \"{path}\" directory is not empty.")
        return 1
    
    if not path.exists():
        path.mkdir()

    results: list[bool] = []
    with console.status("") as status:
        for i in range(start, stop + 1):
            status.update(f"Creating directory [blue]{i}[/]...")
            results.append(new_task_dir(i, git, path, force))
            
            if results[i] != 0:
                printerr(f"Failed to create directory \"Tarea_{i}\".")
                continue
    
    if results.count(False) >= len(results) / 2:
        printerr("Failed to create a lot of directories.")
        return 1
    
    if git:
        connector = "[green]with[/green]"
    else:
        connector = "[red]without[/red]"
    
    print(f"{CHECK} Created directories {connector} git repositories.")
    
    return 0

def cmd_done(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        printerr(f"The path {path} doesn't exists or isn't a directory.")
        return 1
    
    #* ----- FOLDER NAME ------
    
    sub_prompt: Prompt = Prompt("What is the subject?", choices=subjects, case_sensitive=False)
    
    if sub_prompt.check_choice(path.parent.name):
        sub: str = path.parent.name
        print(f"Detected subject [bold blue]{sub}")
    else:
        sub: str = sub_prompt()
    
    ev_num: int = IntPrompt.ask("What is the evaluation number?")
    
    if ev_num < 0:
        printerr("Please, specify a valid number.")
        return 1
    
    name: str = username.load()
    
    if name:
        print(f"Loaded name [bold blue]{name}[/].")
    else:
        name: str = Prompt.ask("Please, enter your name [bold blue]as in the required format[/]. "
                               "[i](For example, nicolasdanilo_mirandacolivoro)[/]")

        if Confirm.ask("Do you want to save your name for the next time?"):
            username.save(name)
    
    zip_path: Path = path / f"e{ev_num}_{sub}_{name}.7z".lower()
    
    if zip_path.exists():
        result = Confirm.ask(f"The file [bold blue]{zip_path.name}[/] already exists. "
                             "Do you want to overwrite it?")
        
        if not result:
            printerr("The file was not modified.")
            return 1
        
        print("The file will be overwriten.")
    
    #* ----- FORMAT VERIFICATION -----
    
    status = console.status("Verifying format...")
    status.start()
    
    for p in path.iterdir():
        if not p.is_dir() or is_valid_task_name(p.name):
            continue
        
        printerr(f"Error: \"{p.name}\" doesn't follow the required format.")
        
        status.stop()
        if not Confirm.ask("Continue?"):
            return 1
        status.start()
    
    print(CHECK + " Format verified.")
    
    #* ----- COMPRESSING & MD5 -----
    
    status.update("Compressing to 7z...")
    szip = compress_7z(path, zip_path.stem)
    
    status.update("Calculating the MD5...")
    code: str = calculate_md5(szip)
    
    print(f"Your MD5 is: [bold blue]{code}[/].")
    
    status.update("Saving the MD5...")
    with open(path / "md5.txt", "w") as fp:
        fp.write(code)
    
    print('MD5 saved to: "md5.txt".')
    
    status.update(f"Saving the 7z...")
    with open(zip_path, "wb") as fp:
        fp.write(szip)
    
    #* ----- DONE -----
    
    status.stop()
    console.bell()
    
    print(CHECK + " [bold green]Done.")
    return 0

def cmd_name(args: Namespace) -> int:
    """Handle the "new" command.

    :param Namespace args: 
    :return int: Exit code
    """
    match args.name_cmd:
        case "get":
            name = username.load()
            
            if name is None:
                printerr("There isn't a saved user name.")
                return 1
            
            print(f"The user name is: [bold blue]\"{name}\".")
            return 0
            
        case "set":
            new: str = args.name
            username.save(new)
            print(CHECK + "The new user name was saved.")
            return 0
            
        case "delete":
            username.delete()
            print(CHECK + "Deleted username.")
            return 0

    return 0

def main() -> int:
    parser = init_parser()
    args = parser.parse_args()
    
    match args.command:
        case "init":
            return cmd_init(args.path, args.start, args.stop, args.git, args.force)
        
        case "done":
            return cmd_done(args.path)
        
        case "name":
            return cmd_name(args)
    
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