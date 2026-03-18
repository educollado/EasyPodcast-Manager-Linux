# EasyPodcast Manager · Linux

> Cliente de escritorio para Linux que permite gestionar un podcast alojado en un servidor [EasyPodcast](https://www.easypodcast.eu) directamente desde el escritorio, sin necesidad de acceder al panel web.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6%20%2F%20Qt6-41cd52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-153%20passing-brightgreen)](#tests)

---

## Capturas

```
┌──────────────────────────────────────────────────────────────┐
│  EasyPodcast Manager                              [─][□][✕]  │
├──────────────────────────────────────────────────────────────┤
│  Episodios │ Podcast │ Páginas │ Redes sociales │ Herramientas│
├──────────────────────────────────────────────────────────────┤
│  Filtro: [Todos ▾]                    [+ Nuevo] [✎ Editar]   │
│  ┌────┬──────┬────────────────────────┬────────────┬───────┐ │
│  │ T. │  Nº  │ Título                 │ Estado     │ Fecha │ │
│  ├────┼──────┼────────────────────────┼────────────┼───────┤ │
│  │  1 │    1 │ Episodio piloto        │ publicado  │ ...   │ │
│  │  1 │    2 │ Entrevista con...      │ borrador   │ ...   │ │
│  └────┴──────┴────────────────────────┴────────────┴───────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Características

| Módulo | Funcionalidades |
|---|---|
| **Episodios** | Crear, editar, eliminar, cambiar estado (borrador ↔ publicado), filtrar |
| **Audio** | Grabación en directo desde micrófono (WAV → MP3 vía ffmpeg), reproductor integrado, subida de archivo o URL remota |
| **Editor HTML** | Editor de código + vista previa en tiempo real, barra de herramientas con atajos |
| **Podcast** | Edición de todos los metadatos: título, descripción, autor, categoría, imagen, iTunes... |
| **Páginas** | Gestión de páginas estáticas con contenido HTML completo y orden en menú |
| **Redes sociales** | 9 plataformas: Blog, LinkedIn, Mastodon, X, Instagram, YouTube, GitHub, Bluesky, Pixelfed |
| **Herramientas** | Limpiar caché, regenerar feed RSS, regenerar imágenes, estadísticas del servidor |
| **Actualizaciones** | Comprobación y actualización del servidor remoto desde la interfaz |

---

## Requisitos

- **Python** 3.10 o superior
- **ffmpeg** instalado en el sistema

```bash
# Debian / Ubuntu / KDE Neon
sudo apt install ffmpeg

# Arch / Manjaro
sudo pacman -S ffmpeg

# Fedora
sudo dnf install ffmpeg
```

### Dependencias Python

| Paquete | Uso |
|---|---|
| `PySide6` | Interfaz gráfica Qt6 |
| `requests` | Llamadas a la API REST |
| `mutagen` | Lectura de metadatos de audio (duración) |
| `sounddevice` | Captura de audio del micrófono |
| `numpy` | Procesamiento de audio en la grabación |

---

## Instalación

### Desde el código fuente

```bash
# 1. Clonar el repositorio
git clone https://github.com/educollado/EasyPodcast-Manager-Linux.git
cd EasyPodcast-Manager-Linux

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python main.py
```

### Paquete .deb (Debian / Ubuntu)

```bash
# Generar el paquete
./build_deb.sh

# Instalar
sudo apt install ./easypodcast-manager_1.0.0_amd64.deb

# Desinstalar
sudo apt remove easypodcast-manager
```

---

## Primer uso

Al lanzar la aplicación por primera vez aparece el **diálogo de configuración** donde se introducen:

- **URL del servidor**: dirección base del servidor EasyPodcast (p.ej. `https://www.mipodcast.com`)
- **Token de acceso**: token de API generado en el panel de EasyPodcast

La aplicación prueba la conexión antes de guardar. Los datos se almacenan en `~/.config/easypodcast/config.ini`.

Para reconfigurar: menú **Preferencias → Configuración**.

---

## Estructura del código

```
EasyPodcast-Manager-Linux/
├── main.py                # Punto de entrada, estilos QSS, lógica de arranque
├── config.py              # Lectura y escritura de ~/.config/easypodcast/config.ini
├── api.py                 # Cliente REST (EasyPodcastAPI + APIError)
├── build_deb.sh           # Script para generar el paquete .deb
├── requirements.txt       # Dependencias de producción
├── requirements-dev.txt   # Dependencias de desarrollo (pytest, pytest-qt)
├── pytest.ini             # Configuración de pytest
└── ui/
    ├── main_window.py     # QMainWindow: pestañas, menú, barra de estado
    ├── setup_dialog.py    # Diálogo de configuración inicial (URL + token)
    ├── episodes_tab.py    # Pestaña episodios: tabla + filtro + CRUD
    ├── episode_dialog.py  # Formulario completo de episodio
    ├── podcast_tab.py     # Formulario de metadatos del podcast
    ├── pages_tab.py       # Pestaña páginas: tabla + CRUD
    ├── page_dialog.py     # Formulario de página
    ├── social_tab.py      # Formulario de redes sociales
    ├── tools_tab.py       # Herramientas, estadísticas y actualizaciones
    ├── html_editor.py     # Widget HtmlEditorField (editor HTML + vista previa)
    ├── image_preview.py   # Widget ImagePreviewField (URL + miniatura)
    ├── audio_player.py    # Widget AudioPlayerField (URL + controles)
    └── audio_recorder.py  # Diálogo de grabación (WAV → MP3)
```

---

## API

Todos los endpoints siguen el patrón `{base_url}/api/v1/{recurso}`.

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/episodes` | Lista de episodios (filtrable por `status`) |
| GET / POST / DELETE | `/episodes/{id}` | Obtener / crear+actualizar / eliminar episodio |
| GET / POST | `/podcast` | Metadatos del podcast |
| GET / POST | `/pages` | Lista / crear página |
| GET / POST / DELETE | `/pages/{id}` | Obtener / actualizar / eliminar página |
| GET / POST | `/social` | Redes sociales |
| POST | `/cache/clear` | Limpiar caché |
| POST | `/feed/regenerate` | Regenerar feed RSS |
| POST | `/cache/regenerate-images` | Regenerar imágenes |
| GET | `/stats` | Estadísticas del servidor |
| GET | `/system/version` | Versión actual y última disponible |
| POST | `/system/update` | Actualizar el servidor |

La autenticación es mediante cabecera `Authorization: Bearer {token}`. Todos los errores HTTP se convierten en `APIError` y se muestran al usuario.

---

## Tests

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar todos los tests
python -m pytest

# Con detalle
python -m pytest -v
```

| Fichero | Tests | Cobertura |
|---|---|---|
| `tests/test_config.py` | 14 | Carga, guardado y validación de credenciales |
| `tests/test_api.py` | 40 | URLs, cabeceras, `_handle`, todos los endpoints |
| `tests/test_tools_tab.py` | 31 | Formateo de valores y renderizado de estadísticas |
| `tests/test_episode_dialog.py` | 38 | Validación, población de campos, `get_data` |
| `tests/test_page_dialog.py` | 30 | Validación, población de campos, `get_data` |
| **Total** | **153** | |

---

## Licencia

[GNU General Public License v3.0](LICENSE) — Software libre.

Más información en [https://www.easypodcast.eu](https://www.easypodcast.eu).
