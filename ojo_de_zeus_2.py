import os
from motores.borrador import ejecutar_borrador
from motores.buscador_auto_graficos import ejecutar_buscador as buscador_auto
from motores.creador_auto_graficos import ejecutar_creador as creador_auto  # ✅ CORREGIDO

def limpiar_pantalla():
    os.system("clear" if os.name == "posix" else "cls")

def mostrar_menu():
    print("🔱  Bienvenido a Ojo de Zeus 2")
    print("=====================================")
    print("1. Buscador automático gráfico")
    print("2. Creator automático gráfico")
    print("3. Borrar métodos")
    print("4. Salir")
    print("=====================================")

def main():
    while True:
        limpiar_pantalla()
        mostrar_menu()
        opcion = input("👉 Selecciona una opción (1-4): ").strip()

        if opcion == "1":
            buscador_auto()
            input("\n🔁 Presiona Enter para volver al menú...")
        elif opcion == "2":
            creador_auto()
            input("\n🔁 Presiona Enter para volver al menú...")
        elif opcion == "3":
            ejecutar_borrador()
            input("\n🔁 Presiona Enter para volver al menú...")
        elif opcion == "4":
            print("👋 Saliendo de Ojo de Zeus 2...")
            break
        else:
            input("❌ Opción inválida. Presiona Enter para intentarlo...")

if __name__ == "__main__":
    main()
