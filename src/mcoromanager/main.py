from argparse import ArgumentParser
from subprocess import run as runcmd
from rich.console import Console
from rich.prompt import Confirm, Prompt, IntPrompt
from pathlib import Path
from py7zr import SevenZipFile
from io import BytesIO
import os
import re
from . import core

from . import __version__

TASK_NAME_PATTERN = re.compile(r"^Tarea_\d+$")
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

def init_parser():
    parser = ArgumentParser(
        prog="mcoromanager",
        description="A simple program to handle directories created by students "
                    "to do the Moisés Coronado's tasks.",
        epilog="Copyright (c) 2026 Nicolás Miranda Colivoro. MIT License."
    )

    parser.add_argument("-v", "--version", action='version', version=__version__)

    subparsers = parser.add_subparsers(title="subcommands", required=True, dest="command", help=None)
    
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
                                              "directory", type=Path, default=Path.cwd())

    #* ----- DONE -----
    cmd_md5 = subparsers.add_parser("done", help="verify the folder's format and calculate the MD5",
                                    description="Verify the folder's format, zip it to .7z and "
                                                "calculate and save the folder's MD5.")
    cmd_md5.add_argument("-p", "--path", help="the dir's path, defaults to the current working "
                                              "directory", type=Path, default=Path.cwd())
    
    return parser

def is_valid_task_name(task_name: str) -> bool:
    """Whether the task name is valid according to the format required bt the professor.

    :param str task_name:
    :return bool:
    """
    return TASK_NAME_PATTERN.match(task_name) is not None

def is_git_installed() -> bool:
    """Whether Git is installed in the computer."""
    try:
        res = runcmd(['git', '--version'], capture_output=True)
        return res.returncode == 0
    except FileNotFoundError:
        return False

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

def new_task_dir(number: int, git: bool, *, parent: Path, force: bool = False) -> int:
    path = parent / f"Tarea_{number:0>2}"
    
    try:
        path.mkdir()
    except PermissionError:
        printerr(f"Error: You don't have permission to create the directory \"{path}\".")
        return 1
    except FileExistsError:
        if not force:
            printerr(f"Error: The directory \"{path}\" already exists.")
            return 1
    except FileNotFoundError:
        printerr(f"Error: The path \"{path}\" is invalid.")
        return 1
    
    if not git:
        return 0
    
    os.chdir(path)
    result = runcmd(["git", "init"], capture_output=True)
    
    if result.returncode != 0:
        printerr(f"Failed to create git repository in \"{path.name}\": {result.stderr.decode()}")
    
    os.chdir(parent)
    
    return result.returncode


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

    with console.status("") as status:
        for i in range(start, stop + 1):
            status.update(f"Creating directory [blue]{i}[/]...")
            result = new_task_dir(i, git, parent=path, force=force)
            
            if result != 0:
                return result
    
    if git:
        connector = "[green]with[/green]"
    else:
        connector = "[red]without[/red]"
    
    print(f"{CHECK} Created directories {connector} git repositories.")
    
    return 1

def cmd_done(path: Path) -> int:
    from hashlib import md5
    
    if not path.exists() or not path.is_dir():
        printerr(f"The path {path} doesn't exists or isn't a directory.")
        return 1
    
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
    
    # TODO: This can be added as a setting
    name: str = Prompt.ask("Please, enter your name [bold blue]as in the required format[/]. "
                           "[i](For example, nicolasdanilo_mirandacolivoro)[/]")
    
    zip_path: Path = path / f"e{ev_num}_{sub}_{name}.7z".lower()
    
    if zip_path.exists():
        result = Confirm.ask(f"The file [bold blue]{zip_path.name}[/] already exists. "
                             "Do you want to overwrite it?")
        
        if not result:
            printerr("The file was not modified.")
            return 1
        
        print("The file will be overwriten.")
    
    buffer = BytesIO()
    
    status = console.status("Verifying format...")
    status.start()
    
    for p in path.iterdir():
        status.start()
        if not p.is_dir() or is_valid_task_name(p.name):
            continue
        
        printerr(f"Error: The folder \"{p.name}\" does not follow the required format.")
        
        status.stop()
        if not Confirm.ask("Continue?"):
            return 1
    
    print(CHECK + " Format verified.")
    
    status.update("Compressing to 7z...")
    
    with SevenZipFile(buffer, mode="w") as zipfile:
        for item in path.iterdir():
            if item in {zip_path, path / "md5.txt"}:
                print(f":warning: [yellow] \"{item.name}\" was ommited in the compressed file.")
                continue
            
            if item.is_dir():
                zipfile.writeall(item, zip_path.stem + "/" + item.stem)
            else:
                zipfile.write(item, zip_path.stem + "/" + item.name)
    
    status.update(f"Saving to \"{zip_path.name}\"...")
    
    buffer.seek(0)
    with open(zip_path, "wb") as fp:
        fp.write(buffer.read())
    
    status.update("Calculating the MD5...")
    
    buffer.seek(0)
    
    code: str = md5(buffer.read()).hexdigest()
    
    print(f"Your MD5 is: [bold blue]{code}[/].", end="")
    console.file.flush()
    
    status.update("Saving the MD5...")
    with open(path / "md5.txt", "w") as fp:
        fp.write(code)
    
    print('MD5 saved to: "md5.txt".')
    
    status.stop()
    
    console.bell()
    print(CHECK + " [bold green]Done.")
    return 0

def main() -> int:
    parser = init_parser()
    args = parser.parse_args()
    
    match args.command:
        case "init":
            return cmd_init(args.path.absolute(), args.start, args.stop, args.git, args.force)
        
        case "done":
            path: Path = args.path.absolute()
            return cmd_done(path)
        
        case _:
            parser.print_usage()
            return 1

def run() -> int:
    try:
        return main()
    except KeyboardInterrupt:
        printerr("Process killed by the user.")
        return 1
    except Exception as e:
        console.print_exception(e)
        return 1

if __name__ == "__main__":
    exit(run())