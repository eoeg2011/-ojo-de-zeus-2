import os
from colorama import Fore, Style

def limpiar_pantalla():
    os.system('clear' if os.name == 'posix' else 'cls')

def input_colores(texto):
    return input(Fore.CYAN + texto + Style.RESET_ALL)

def print_titulo(titulo):
    print(Fore.GREEN + "\n" + "=" * len(titulo))
    print(titulo.upper())
    print("=" * len(titulo) + "\n" + Style.RESET_ALL)
