from pathlib import Path
from rich.prompt import Prompt, IntPrompt, Confirm
from ..core import *

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

def main(path: Path) -> int:
    """Handle the `done` command.

    :param Path path: The path of the evaluations folder
    :return int: Exit code
    """
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