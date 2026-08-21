# EasyPodcast Manager · Linux

> Cliente de escritorio para Linux que permite gestionar varios podcasts alojados en un servidor [EasyPodcast](https://www.easypodcast.eu) directamente desde el escritorio, sin necesidad de acceder al panel web.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6%20%2F%20Qt6-41cd52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-206%20passing-brightgreen)](#tests)
[![Version](https://img.shields.io/badge/version-0.0.7-blue)](https://github.com/educollado/EasyPodcast-Manager-Linux/releases/tag/v0.0.7)

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
| **Perfiles** | Varios podcasts y usuarios, migración de la configuración antigua y cambio inmediato desde el selector principal |
| **Episodios** | Crear, editar, eliminar, cambiar estado (borrador ↔ publicado), programar, filtrar y cargar automáticamente todas las páginas de resultados |
| **Audio** | Grabación en directo desde micrófono (WAV → MP3 vía ffmpeg), selector de dispositivo de entrada, vúmetro LED en tiempo real, reproductor integrado, subida de archivo o URL remota con tamaño y MIME |
| **Editor HTML** | Editor de código + vista previa en tiempo real, barra de herramientas con atajos |
| **Podcast** | Edición de metadatos, portada, imagen Hero de la web, categoría, datos de iTunes... |
| **Páginas** | Gestión de páginas estáticas con contenido HTML completo, jerarquía padre/hijo y orden en menú |
| **Redes sociales** | 9 plataformas: Blog, LinkedIn, Mastodon, X, Instagram, YouTube, GitHub, Bluesky, Pixelfed |
| **Herramientas** | Limpiar caché, regenerar feed RSS, regenerar imágenes y consultar estadísticas de episodios, caché, descargas y reproducciones |
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
sudo apt install ./easypodcast-manager_0.0.7_amd64.deb

# Desinstalar
sudo apt remove easypodcast-manager
```

---

## Primer uso

Al lanzar la aplicación por primera vez aparece el **diálogo de configuración**. Cada perfil contiene:

- **Nombre del perfil**: nombre reconocible para mostrar en el selector.
- **URL del podcast**: URL que incluye el directorio del podcast (p.ej. `https://www.mipodcast.com/mi-podcast`). No se debe añadir `/api/v1`.
- **Token de acceso**: token de API generado en el panel de EasyPodcast. El
  alcance `content` permite gestionar los podcasts asignados al usuario;
  actualizar el servidor requiere alcance `admin`.

La aplicación prueba la conexión antes de guardar. Se pueden crear tantos
perfiles como sean necesarios y cambiar entre ellos desde la barra superior.
Los datos se almacenan en `~/.config/easypodcast/config.ini`; una configuración
antigua de un único podcast se detecta y migra al editarla.

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

Los endpoints administrativos `/users` y `/users/podcasts` pertenecen a la
administración global del servidor y no forman parte de este cliente de
contenidos. Los permisos multiusuario sí se respetan automáticamente mediante
el token de cada perfil.

Los listados paginados de episodios y páginas se recorren automáticamente
hasta recuperar todos los resultados. Al crear un episodio se exige título,
contenido y audio, también si comienza como borrador. Con una URL de audio
remota también debe indicarse su tamaño en bytes; el botón
«Detectar desde URL» intenta obtener automáticamente el tamaño y el tipo MIME,
tal como requiere la API actual de EasyPodcast.

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
| `tests/test_config.py` | 19 | Perfiles, migración, selección y credenciales |
| `tests/test_api.py` | 45 | URLs, cabeceras, paginación, multipart, `_handle` y endpoints |
| `tests/test_tools_tab.py` | 36 | Formateo de valores, estadísticas y permisos de actualización |
| `tests/test_episode_dialog.py` | 60 | Validación por estado, audio remoto, autor, explícito y `get_data` |
| `tests/test_page_dialog.py` | 36 | Validación, jerarquía, orden y `get_data` |
| `tests/test_podcast_tab.py` | 7 | Metadatos avanzados e imagen Hero |
| `tests/test_profiles_ui.py` | 3 | Alta, selección y cambio de perfiles desde la interfaz |
| **Total** | **206** | |

---

## Licencia

[GNU General Public License v3.0](LICENSE) — Software libre.

Más información en [https://www.easypodcast.eu](https://www.easypodcast.eu).
