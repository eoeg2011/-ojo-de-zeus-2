# Ojo de Zeus 2 🔱

Herramienta OSINT en Python para verificar usuarios/correos en múltiples sitios con varios métodos (URL final, contenido, códigos de estado, etc.). Requiere Python 3.9+ y (opcional) Firefox + Geckodriver para modo gráfico.

## Instalación
\```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\```

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
