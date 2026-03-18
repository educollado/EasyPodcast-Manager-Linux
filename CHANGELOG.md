# Changelog

Todos los cambios notables de este proyecto se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

---

## [1.0.0] — 2026-03-18

### Añadido

#### Episodios
- Tabla de episodios con columnas: Temporada, Número, Título, Estado, Fecha
- Filtro por estado: todos, publicados, borradores
- Operaciones CRUD completas: crear, editar (doble clic), eliminar
- Cambio de estado rápido (borrador ↔ publicado) desde la tabla
- Formulario con campos: título, slug, descripción, contenido HTML, audio, imagen, duración, temporada, número, tipo, estado y fecha de publicación

#### Audio
- Grabación de audio en directo desde el micrófono (WAV → MP3 vía ffmpeg)
- Reproductor de audio integrado para previsualizar episodios
- Lectura automática de duración al seleccionar un archivo de audio
- Soporte para audio vía URL remota, archivo local o grabación en directo

#### Editor HTML
- Editor de código fuente con fuente monoespaciada
- Vista previa en tiempo real del HTML renderizado
- Barra de herramientas: negrita, cursiva, párrafo, H2, H3, listas UL/OL, separador HR, enlace
- Envuelve el texto seleccionado en la etiqueta elegida

#### Podcast
- Formulario para editar metadatos globales: título, descripción, autor, nombre/email del propietario, idioma, categoría, sitio web, imagen de portada, copyright, contenido explícito, tipo iTunes

#### Páginas
- Lista de páginas estáticas con columnas: ID, Título, Slug, Estado
- Operaciones CRUD: crear, editar (doble clic), eliminar
- Campo «Orden en menú» con soporte de valores negativos

#### Redes sociales
- Formulario con URLs para 9 plataformas: Blog, LinkedIn, Mastodon, X (Twitter), Instagram, YouTube, GitHub, Bluesky, Pixelfed

#### Herramientas
- Limpiar caché del servidor
- Regenerar feed RSS
- Regenerar imágenes del podcast
- Estadísticas del servidor en tarjetas visuales (episodios y caché)
- Comprobación de versión del servidor y actualización remota desde la interfaz

#### Infraestructura
- Configuración guardada en `~/.config/easypodcast/config.ini`
- Diálogo de configuración inicial con prueba de conexión
- Paleta de colores propia: fondo `#f6f2eb`, texto `#1c1814`, acento `#8c3509`
- Hoja de estilos QSS completa para toda la interfaz
- Script `build_deb.sh` para generar paquete `.deb` instalable en Debian/Ubuntu
- Suite de 153 tests automatizados con pytest y pytest-qt

---

[1.0.0]: https://github.com/educollado/EasyPodcast-Manager-Linux/releases/tag/v1.0.0
