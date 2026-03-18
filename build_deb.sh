#!/usr/bin/env bash
# build_deb.sh — Genera el paquete .deb de EasyPodcast Manager
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
PKG_NAME="easypodcast-manager"
VERSION="0.0.1"
ARCH=$(dpkg --print-architecture 2>/dev/null || echo "amd64")
DEB_FILE="${PKG_NAME}_${VERSION}_${ARCH}.deb"

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$(mktemp -d /tmp/${PKG_NAME}_build_XXXXXX)"

APP_DIR="$BUILD_DIR/usr/lib/$PKG_NAME"
BIN_DIR="$BUILD_DIR/usr/bin"
SHARE_DIR="$BUILD_DIR/usr/share"
DEBIAN_DIR="$BUILD_DIR/DEBIAN"

echo "==> Preparando estructura en $BUILD_DIR"
mkdir -p "$APP_DIR/ui"
mkdir -p "$DEBIAN_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$SHARE_DIR/applications"
mkdir -p "$SHARE_DIR/icons/hicolor/256x256/apps"

# ---------------------------------------------------------------------------
# Copiar archivos de la aplicación
# ---------------------------------------------------------------------------
echo "==> Copiando archivos de la aplicación"

for f in main.py config.py api.py requirements.txt; do
    cp "$SRC_DIR/$f" "$APP_DIR/$f"
done

for f in "$SRC_DIR"/ui/*.py; do
    cp "$f" "$APP_DIR/ui/"
done

# ---------------------------------------------------------------------------
# Icono
# ---------------------------------------------------------------------------
if [ -f "$SRC_DIR/easypodcast.ico" ]; then
    if command -v convert &>/dev/null; then
        echo "==> Convirtiendo icono .ico → .png"
        convert "$SRC_DIR/easypodcast.ico[0]" \
            "$SHARE_DIR/icons/hicolor/256x256/apps/$PKG_NAME.png" 2>/dev/null \
            && echo "    Icono convertido" \
            || echo "    Advertencia: no se pudo convertir el icono"
    else
        cp "$SRC_DIR/easypodcast.ico" "$APP_DIR/easypodcast.ico"
    fi
fi

# ---------------------------------------------------------------------------
# Lanzador /usr/bin/easypodcast-manager
# ---------------------------------------------------------------------------
echo "==> Creando lanzador"
cat > "$BIN_DIR/$PKG_NAME" << 'LAUNCHER'
#!/bin/bash
APP_DIR="/usr/lib/easypodcast-manager"
VENV="$APP_DIR/venv"

if [ ! -d "$VENV" ]; then
    echo "Error: entorno virtual no encontrado en $VENV"
    echo "Prueba a reinstalar el paquete con: sudo apt install --reinstall easypodcast-manager"
    exit 1
fi

exec "$VENV/bin/python" "$APP_DIR/main.py" "$@"
LAUNCHER
chmod 755 "$BIN_DIR/$PKG_NAME"

# ---------------------------------------------------------------------------
# Entrada de escritorio .desktop
# ---------------------------------------------------------------------------
echo "==> Creando entrada de escritorio"
cat > "$SHARE_DIR/applications/$PKG_NAME.desktop" << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=EasyPodcast Manager
GenericName=Gestor de Podcast
Comment=Gestiona tu podcast EasyPodcast desde el escritorio
Exec=/usr/bin/$PKG_NAME
Icon=$PKG_NAME
Categories=AudioVideo;Audio;
Terminal=false
StartupNotify=true
StartupWMClass=main
Keywords=podcast;audio;easypodcast;
DESKTOP

# ---------------------------------------------------------------------------
# DEBIAN/control
# ---------------------------------------------------------------------------
echo "==> Generando DEBIAN/control"
INSTALLED_SIZE=$(du -sk "$BUILD_DIR" | cut -f1)
cat > "$DEBIAN_DIR/control" << CONTROL
Package: $PKG_NAME
Version: $VERSION
Architecture: $ARCH
Section: sound
Priority: optional
Installed-Size: $INSTALLED_SIZE
Depends: python3 (>= 3.10), python3-venv, python3-pip, ffmpeg, libgl1, libglib2.0-0
Maintainer: EasyPodcast <info@easypodcast.eu>
Homepage: https://www.easypodcast.eu
Description: Cliente de escritorio para gestionar podcasts EasyPodcast
 Aplicación de escritorio para Linux/KDE que permite gestionar un podcast
 alojado en un servidor EasyPodcast directamente desde el escritorio,
 sin necesidad de acceder al panel web.
 .
 Incluye gestión de episodios con grabación de audio, editor HTML con
 vista previa, gestión de páginas, redes sociales, estadísticas y
 herramientas de mantenimiento del servidor.
CONTROL

# ---------------------------------------------------------------------------
# DEBIAN/postinst — crea el entorno virtual e instala dependencias
# ---------------------------------------------------------------------------
echo "==> Generando DEBIAN/postinst"
cat > "$DEBIAN_DIR/postinst" << 'POSTINST'
#!/bin/bash
set -e

APP_DIR="/usr/lib/easypodcast-manager"
VENV="$APP_DIR/venv"

case "$1" in
    configure)
        echo "EasyPodcast Manager: creando entorno virtual Python..."

        if [ ! -d "$VENV" ]; then
            python3 -m venv "$VENV"
        fi

        echo "EasyPodcast Manager: instalando dependencias Python..."
        "$VENV/bin/pip" install --quiet --upgrade pip
        "$VENV/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

        echo "EasyPodcast Manager: instalación completada."

        # Actualizar caché de iconos y base de datos de menú
        if command -v update-icon-caches &>/dev/null; then
            update-icon-caches /usr/share/icons/hicolor 2>/dev/null || true
        fi
        if command -v update-desktop-database &>/dev/null; then
            update-desktop-database /usr/share/applications 2>/dev/null || true
        fi
        ;;
esac

exit 0
POSTINST
chmod 755 "$DEBIAN_DIR/postinst"

# ---------------------------------------------------------------------------
# DEBIAN/prerm — elimina el entorno virtual antes de desinstalar
# ---------------------------------------------------------------------------
echo "==> Generando DEBIAN/prerm"
cat > "$DEBIAN_DIR/prerm" << 'PRERM'
#!/bin/bash
set -e

APP_DIR="/usr/lib/easypodcast-manager"
VENV="$APP_DIR/venv"

case "$1" in
    remove|purge)
        echo "EasyPodcast Manager: eliminando entorno virtual..."
        rm -rf "$VENV"
        ;;
esac

exit 0
PRERM
chmod 755 "$DEBIAN_DIR/prerm"

# ---------------------------------------------------------------------------
# Permisos finales
# ---------------------------------------------------------------------------
echo "==> Ajustando permisos"
find "$BUILD_DIR" -type d -exec chmod 755 {} \;
find "$BUILD_DIR" -type f -exec chmod 644 {} \;
chmod 755 "$BIN_DIR/$PKG_NAME"
chmod 755 "$DEBIAN_DIR/postinst"
chmod 755 "$DEBIAN_DIR/prerm"

# ---------------------------------------------------------------------------
# Construir el .deb
# ---------------------------------------------------------------------------
echo "==> Construyendo $DEB_FILE"
dpkg-deb --build --root-owner-group "$BUILD_DIR" "$SRC_DIR/$DEB_FILE"

# Limpiar directorio temporal
rm -rf "$BUILD_DIR"

echo ""
echo "✓ Paquete generado: $DEB_FILE"
echo ""
echo "Para instalar:"
echo "  sudo apt install ./$DEB_FILE"
echo ""
echo "Para desinstalar:"
echo "  sudo apt remove $PKG_NAME"
