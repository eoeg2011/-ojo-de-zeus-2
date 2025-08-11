import json
import os

ARCHIVO_SITIOS = "sitios.json"

def cargar_sitios():
    if not os.path.exists(ARCHIVO_SITIOS):
        return []
    with open(ARCHIVO_SITIOS, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_sitios(sitios):
    with open(ARCHIVO_SITIOS, "w", encoding="utf-8") as f:
        json.dump(sitios, f, indent=4, ensure_ascii=False)

def obtener_nombres_base(sitios):
    nombres_base = set()
    for sitio in sitios:
        nombre = sitio["nombre"]
        for i in range(len(nombre), 0, -1):
            if nombre[:i].isalpha():
                nombres_base.add(nombre[:i])
                break
    return sorted(list(nombres_base))

def borrar_metodos():
    sitios = cargar_sitios()
    if not sitios:
        print("❌ No hay métodos guardados.")
        return

    total_antes = len(sitios)

    nombres_base = obtener_nombres_base(sitios)
    print("\n🌐 Sitios disponibles:")
    for idx, nombre in enumerate(nombres_base, 1):
        print(f"{idx}. {nombre}")

    try:
        eleccion = int(input("\n🔢 Ingresa el número del sitio a modificar: "))
        nombre_base = nombres_base[eleccion - 1]
    except (ValueError, IndexError):
        print("❌ Opción no válida.")
        return

    relacionados = [s for s in sitios if s["nombre"].startswith(nombre_base)]
    if not relacionados:
        print("❌ No hay métodos asociados a ese sitio.")
        return

    print(f"\n📄 Métodos para '{nombre_base}':")
    for idx, sitio in enumerate(relacionados, 1):
        print(f"{idx}. {sitio['nombre']} - Método: {sitio['metodo']}")

    seleccion = input("\n🗑️ Ingresa los números de los métodos a eliminar (ej. 1,3,4): ")
    numeros = seleccion.replace(" ", "").split(",")

    a_eliminar = []
    for num in numeros:
        if num.isdigit():
            idx = int(num) - 1
            if 0 <= idx < len(relacionados):
                a_eliminar.append(relacionados[idx])

    if not a_eliminar:
        print("❌ No se seleccionó ningún método válido.")
        return

    for item in a_eliminar:
        sitios.remove(item)
        print(f"✅ Eliminado: {item['nombre']}")

    guardar_sitios(sitios)
    total_despues = len(sitios)
    print(f"\n💾 Cambios guardados en sitios.json.")
    print(f"📊 Métodos antes: {total_antes} | después: {total_despues}")

def ejecutar_borrador():
    borrar_metodos()
