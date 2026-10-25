#!/bin/bash
# One-off preparation of the licensed asset packs (not stored in the repository): rebuilt materials, real scale, kit
# pieces cut out of the library scene, texture sets renamed for the pipeline, FBX for Unreal.
# usage: scripts/prep_assets.sh ROOT PACKS_DIR      (PACKS_DIR = the extracted Dropbox folder: denniswoo1993/, HawtorStudio/, ...)
# Python that reads the packs runs with -I (isolated: nothing is imported from the pack folders).
set -e
S=$(cd "$1" && pwd); P=$(cd "$2" && pwd)
B="blender -b --factory-startup --python-exit-code 1 --python"
LIB=$(ls -d "$P"/denniswoo1993/*/ | head -1); FC=$(ls -d "$P"/HawtorStudio/*Fantasy*/ | head -1)
python3 -I $S/scripts/fc_fix_colors.py "$FC" $S/assets/fantasy/tex
python3 -I $S/scripts/lib_fix_colors.py "$LIB" $S/assets/library/tex
$B $S/scripts/prep_fantasy.py -- "$FC" $S/assets/fantasy 120 | grep -E "SIZE|DONE"
$B $S/scripts/prep_library.py -- "$LIB" $S/assets/library | grep -E "SIZE|DONE"
$B $S/scripts/lib_prefabs.py -- $S/assets/library/library.blend $S/assets/library | grep -E "DONE"
cp $S/assets/library/prefabs.json $S/data/kit_library.json
# prop packs of the second delivery (throne, rugs, furniture, chandelier, candelabra, paintings, crucifixes, coffin, shack):
# one prefab per prop (props_defs.py), data/props_library.json stored in the repository
$B $S/scripts/prep_props.py -- "$P" $S/assets/props | grep -E "PROPS_DONE|Error"
cp $S/assets/props/props.json $S/data/props_library.json
python3 -I $S/scripts/kit_textures.py $S "$P" | tail -1
# vampires' castle (Castle 2.0): face table -> materials per UV island, centred model at scale 160, walk-test triangles,
# ground plate (the hill it was built on: the crag top takes its relief). data/castle20_rooms.json and
# data/castle20_plate.npz are stored in the repository (analysis results).
C2=$(ls -d "$P"/EldersCrawler/*/ | head -1); C2FBX=$(ls "$C2"*.fbx "$C2"*.FBX 2>/dev/null | head -1)
mkdir -p $S/assets/castle20
$B $S/scripts/c20_faces.py -- "$C2FBX" $S/assets/castle20/faces.npz | grep -E "FACES|Error" || true
python3 -I $S/scripts/c20_classes.py $S | tail -1
$B $S/scripts/prep_castle20.py -- "$C2" $S 160 island | grep -E "SIZE|DONE"
$B $S/scripts/blend_tris.py -- $S/assets/castle20/castle20_island.blend $S/assets/castle20/tris.npz | grep TRIS
$B $S/scripts/c20_ground.py -- "$C2FBX" $S/assets/castle20/ground.npz 160 | grep GROUND
echo PREP_ASSETS_DONE
