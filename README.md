# Ojo de Zeus 2 🔱
hola soy kike me gusta todo lo que es informatica y la seguridad desde chico. pero recientemente un robo de un celular de un familiar me motivo a crear esta herraminta ya que el aser algo parecido como lo que hace esta herramienta me ayudo a encontrar a ese ladron (no fue por el celuler si no por que empezo aser mal uso de todo el contenido de el celular) y logre optener vastante informacion que me ayudo a confirmar su identidad y donde se ubicaba sus lugares de frecuencia no pudonegarse a que era el quien tenia el celular y todo gracias a un usuario que metio en el dispositivo y con eso di con toda su informacion.

1.Herramienta OSINT en Python para verificar usuarios/correos en múltiples sitios con varios métodos (URL final, contenido, códigos de estado, etc.).

2.incluye una segunda heramienta que te ayuda a crear mas sitios para verificar muy intuitiva para crearlos atraves de usuarios reales vs no existentes si verifica los metodos funcionales.

3.herramienta para borrar las paginas o metodos guardados para verificar. 

## Instalación
\```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\```

# INSTALACION EN TERMUX
1. Actualiza paquetes
   
pkg update -y && pkg upgrade -y

3. Instala dependencias básicas
   
pkg install -y git python python-pip

5. (Opcional) Instalar herramientas de compilación
   
pkg install -y clang make

7. Clona tu repositorio
   
git clone https://github.com/eoeg2011/ojo-de-zeus-2.git
cd ojo-de-zeus-2

9. Instala dependencias de Python
    
pip install --upgrade pip
pip install -r requirements.txt

## TERMUX CON ENTORNO GRÁFICO 
Cómo se haría (resumen técnico)

1. Instalar Termux-X11 (APK oficial de su GitHub).


2. Instalar proot-distro en Termux:

pkg install proot-distro
proot-distro install debian


3. Entrar a Debian:

proot-distro login debian


4. Instalar entorno gráfico + Firefox:

apt update && apt install -y lxde firefox-esr


5. Ejecutar servidor gráfico y exportar DISPLAY=:0 para que Firefox se abra en la pantalla de Termux-X11.



Así Ojo de Zeus 2 podrá usar Selenium con Firefox en Termux igual que en Linux normal.


## Uso
\```bash
python3 ojo_de_zeus_2.py
\```

## Estructura
\```
motores/            # módulos: buscador_auto_graficos, creador_auto_graficos, comparador, utils, borrador
sitios.json         # métodos guardados (este repo SÍ lo publica)
ojo_de_zeus_2.py    # menú principal
requirements.txt    # dependencias
README.md
.gitignore
\```

## Requisitos
- Python 3.9+
- (Opcional para modo gráfico) Firefox + GeckoDriver en el PATH.

### Notas de entorno gráfico (Firefox/GeckoDriver)
- En Debian/Orange Pi: `sudo apt-get install -y firefox-esr`
- Instala `geckodriver` acorde a tu sistema y verifica con `geckodriver --version`.
- Si no hay entorno gráfico, la herramienta usa modos “ocultos” cuando aplica.

## Contribución
- Abre issues o PRs con descripción clara del entorno y pasos para reproducir.

## Licencia
MIT
