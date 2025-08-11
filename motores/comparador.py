# motores/comparador.py

import unicodedata

def normalizar(texto):
    """
    Convierte el texto a minúsculas, elimina acentos y espacios extra.
    """
    texto = texto.lower()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto.strip()

def comparar_perfiles(html_real, html_falso, mostrar_resultado=True):
    """
    Función provisional. Devuelve sets vacíos, solo para pruebas.
    Reemplaza esto por la lógica real después.
    """
    if mostrar_resultado:
        print("⚠️ [comparador.py] Esta es una función provisional. Agrega la lógica real después.")
    palabras_auto = set()
    frases_auto = set()
    return palabras_auto, frases_auto
