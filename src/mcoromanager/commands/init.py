from pathlib import Path
from ..core import *

def main(path: Path, start: int, stop: int, git: bool, force: bool) -> int:
    """Handle the `init` command.

    :param Path path: The path of the evaluation folder
    :param int start: The start of the task number range
    :param int stop: The end of the task number range
    :param bool git: Whether to create a git repository for each task
    :param bool force: Whether to force the creation of new directories
    :return int: Exit code
    """
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
            
            if results[i - 1] != 0:
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