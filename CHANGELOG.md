# Changelog

Todos los cambios notables de este proyecto se documentan en este fichero.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es/1.1.0/),
y este proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

---

## [0.0.6] — 2026-08-20

### Añadido

- Gestión de la imagen Hero de la web del podcast mediante URL o subida de un
  archivo local, con previsualización y opción de eliminarla.

### Cambiado

- El cliente API admite `hero_image_file` mediante `multipart/form-data` y
  conserva el envío JSON cuando no se seleccionan archivos.
- README y paquete Debian actualizados a la versión 0.0.6.
- Suite ampliada a 190 tests.

## [0.0.5] — 2026-07-27

### Cambiado

- Compatibilidad actualizada con EasyPodcast 1.9.5
- Los borradores de episodios solo requieren título; contenido y audio se
  validan al publicar o programar
- Los listados de episodios y páginas recorren automáticamente toda la
  paginación de la API
- Las páginas usan el campo correcto `sort_order` y admiten jerarquía mediante
  `parent_id`
- Los audios remotos admiten tamaño en bytes y tipo MIME, requeridos por el
  servidor al publicar
- Se elimina el campo de slug de episodios, ya que EasyPodcast genera y
  conserva automáticamente la URL pública
- Las estadísticas muestran descargas y reproducciones
- La actualización del servidor explica cuándo se necesita un token con
  alcance `admin`
- La versión del cliente se centraliza en `client_version.py`
- Las dependencias declaran rangos compatibles para evitar saltos de versión
  principal inesperados

### Corregido

- Corregido un error de sintaxis en `api.py`
- El reproductor y el grabador inicializan los subsistemas de audio solo al
  utilizarlos, evitando bloqueos al abrir formularios sin PipeWire/ALSA
- Los ficheros usados en peticiones multipart se cierran correctamente
- README y paquete Debian actualizados a la versión 0.0.5
- Suite ampliada a 184 tests

## [0.0.4] — 2026-04-14

### Añadido

#### Interfaz
- Diálogo "Acerca de" ahora muestra la versión del cliente (0.0.4) y la versión del servidor obtenida de la API

---

## [0.0.3] — 2026-04-14

### Añadido

#### Episodios
- Nuevo estado **`scheduled`** (programado): permite fijar una fecha futura de publicación en formato ISO 8601
- Filtro por estado `scheduled` en la lista de episodios
- La etiqueta «Fecha programada» se marca como obligatoria en el formulario al seleccionar el estado programado
- El botón «Publicar/Borrador» ahora también cancela la programación (pasa de `scheduled` a `draft`)

---

## [0.0.2] — 2026-03-19

### Añadido

#### Audio
- Selector de dispositivo de entrada en el diálogo de grabación: filtra los dispositivos ALSA virtuales y selecciona automáticamente el primer hardware real (`hw:`)
- Vúmetro LED segmentado en tiempo real durante la grabación: 20 segmentos con colores verde / naranja / rojo según el nivel
- Suavizado del vúmetro con ataque rápido y caída lenta (interpolación exponencial a ~25 fps)

---

## [0.0.1] — 2026-03-18

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

[0.0.6]: https://github.com/educollado/EasyPodcast-Manager-Linux/releases/tag/v0.0.6
[0.0.5]: https://github.com/educollado/EasyPodcast-Manager-Linux/releases/tag/v0.0.5
[0.0.4]: https://github.com/educollado/EasyPodcast-Manager-Linux/releases/tag/v0.0.4
[0.0.3]: https://github.com/educollado/EasyPodcast-Manager-Linux/releases/tag/v0.0.3
[0.0.2]: https://github.com/educollado/EasyPodcast-Manager-Linux/releases/tag/v0.0.2
[0.0.1]: https://github.com/educollado/EasyPodcast-Manager-Linux/releases/tag/v0.0.1
