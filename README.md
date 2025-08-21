# Ojo de Zeus 2 🔱

**Ojo de Zeus 2** es una herramienta **OSINT avanzada en Python** que permite verificar usuarios y correos electrónicos en múltiples sitios web, utilizando distintos métodos de comprobación como seguimiento de URL final, análisis de contenido y códigos de estado HTTP.  

---

## 📖 Historia

Hola, soy Kike. Desde pequeño me ha apasionado la informática y la seguridad digital.  
Un incidente reciente, en el que un familiar sufrió el robo de un celular, me motivó a crear esta herramienta. Aunque el valor del dispositivo no era lo importante, sabía que el ladrón empezaría a hacer mal uso del contenido personal.  

Gracias a una cuenta ingresada en el teléfono pude rastrear la identidad del delincuente y ubicarlo en sus zonas frecuentes. Esa experiencia me inspiró a desarrollar **Ojo de Zeus 2**, con la idea de que cualquiera pueda contar con una herramienta similar para proteger su información y obtener datos OSINT de manera sencilla.

---

## ✨ Características principales

- **Verificación OSINT** de usuarios y correos electrónicos en múltiples plataformas mediante:
  - Redirección de URL final.
  - Análisis del contenido de las páginas.
  - Códigos de estado HTTP.
- **Generador de sitios personalizados**: permite crear plantillas intuitivas para validar combinaciones reales e inexistentes.
- **Gestión de métodos**: posibilidad de eliminar sitios o métodos guardados si ya no funcionan o no son útiles.
- **Compatibilidad multiplataforma**: funciona en Linux, macOS, Termux y sistemas embebidos como Orange Pi.

---

## ⚙️ Instalación

### 🔹 En Linux / macOS

bash
Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

Actualizar pip e instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

### EN TERMUX ANDROID 
Actualizar paquetes
pkg update -y && pkg upgrade -y

 Instalar dependencias básicas
pkg install -y git python python-pip

(Opcional) Herramientas de compilación
pkg install -y clang make

 Clonar repositorio e instalar dependencias
git clone https://github.com/eoeg2011/ojo-de-zeus-2.git
cd ojo-de-zeus-2
pip install --upgrade pip
pip install -r requirements.txt
