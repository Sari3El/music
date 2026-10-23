#!/bin/bash
# One-off preparation of the licensed asset packs (not stored in the repository): rebuilt materials, real scale, kit
# pieces cut out of the library scene, texture sets renamed for the pipeline, FBX for Unreal.
# usage: scripts/prep_assets.sh ROOT PACKS_DIR      (PACKS_DIR = the extracted Dropbox folder: denniswoo1993/, HawtorStudio/, ...)
# Python that reads the packs runs with -I (isolated: nothing is imported from the pack folders).
set -e
S=$(cd "$1" && pwd); P=$(cd "$2" && pwd)
B="blender -b --factory-startup --python-exit-code 1 --python"
LIB=$(ls -d "$P"/denniswoo1993/*/ | head -1); FC=$(ls -d "$P"/HawtorStudio/*/ | head -1)
python3 -I $S/scripts/fc_fix_colors.py "$FC" $S/assets/fantasy/tex
python3 -I $S/scripts/lib_fix_colors.py "$LIB" $S/assets/library/tex
$B $S/scripts/prep_fantasy.py -- "$FC" $S/assets/fantasy 120 | grep -E "SIZE|DONE"
$B $S/scripts/prep_library.py -- "$LIB" $S/assets/library | grep -E "SIZE|DONE"
$B $S/scripts/lib_prefabs.py -- $S/assets/library/library.blend $S/assets/library | grep -E "DONE"
cp $S/assets/library/prefabs.json $S/data/kit_library.json
python3 -I $S/scripts/kit_textures.py $S "$P" | tail -1
echo PREP_ASSETS_DONE
