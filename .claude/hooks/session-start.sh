#!/bin/bash
# Installs headless Blender 4.5 LTS + Blender Source Tools (SMD/DMX export for Source/Garry's Mod)
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

BLENDER_VERSION="4.5.14"
BLENDER_DIR="/opt/blender-${BLENDER_VERSION}-linux-x64"
BLENDER_URL="https://download.blender.org/release/Blender4.5/blender-${BLENDER_VERSION}-linux-x64.tar.xz"

if [ ! -x "${BLENDER_DIR}/blender" ]; then
  tmp="$(mktemp -d)"
  curl -sSfL -o "${tmp}/blender.tar.xz" "${BLENDER_URL}"
  tar -xf "${tmp}/blender.tar.xz" -C /opt
  rm -rf "${tmp}"
fi
ln -sf "${BLENDER_DIR}/blender" /usr/local/bin/blender

# System libraries Blender needs to render headless (EGL/X11 client libs)
if ! ldconfig -p | grep -q 'libEGL.so.1'; then
  apt-get install -y -q libegl1 libgl1 libxkbcommon0 libsm6 libxi6 libxrender1 libxxf86vm1 libxfixes3 >/dev/null 2>&1 \
    || { apt-get update -q >/dev/null 2>&1 && apt-get install -y -q libegl1 libgl1 libxkbcommon0 libsm6 libxi6 libxrender1 libxxf86vm1 libxfixes3 >/dev/null 2>&1; }
fi

# Blender Source Tools add-on
ADDONS_DIR="$(blender -b --factory-startup --python-expr \
  "import bpy;print('ADDONS='+bpy.utils.user_resource('SCRIPTS',path='addons',create=True))" 2>/dev/null \
  | grep '^ADDONS=' | cut -d= -f2-)"

if [ ! -d "${ADDONS_DIR}/io_scene_valvesource" ]; then
  tmp="$(mktemp -d)"
  git clone -q --depth 1 https://github.com/Artfunkel/BlenderSourceTools.git "${tmp}/bst"
  cp -r "${tmp}/bst/io_scene_valvesource" "${ADDONS_DIR}/"
  rm -rf "${tmp}"
fi

blender -b --factory-startup --python-expr \
  "import bpy,addon_utils;addon_utils.enable('io_scene_valvesource',default_set=True,persistent=True);bpy.ops.wm.save_userpref()" \
  >/dev/null 2>&1

blender --version | head -1
