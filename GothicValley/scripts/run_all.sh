#!/bin/bash
set -e
S=$1
cd $S/scripts
until [ -f $S/terrain/check_done ]; do sleep 5; done
echo "== terrain"; grep "PASS_ALL" $S/terrain/check_log.txt || true
python3 gb_castle.py $S | tail -1
python3 gb_city.py $S | tail -2
python3 gb_sites.py $S | tail -1
python3 gb_checks.py $S | grep -A8 '"checks"'
echo "== nav"
python3 nav_check.py $S $S/greybox/nav_castle.json 2>&1 | grep -v "reached': True"
python3 nav_check.py $S $S/greybox/nav_city.json 2>&1 | grep -v "reached': True"
python3 nav_sites.py $S
python3 travel.py $S > /dev/null
echo "== blender build"
rm -rf $S/export/Content $S/export/*.blend
for p in castle city sites; do
  blender -b --factory-startup --python gb_build.py -- $S $S/export/Content $S/export/$p.blend $S/greybox/${p}_groups.json 2>&1 | grep -E "GB_BUILD|Error" | tail -2
done
echo "== renders"
rm -rf $S/renders/hero
blender -b --factory-startup --python render_hero.py -- $S $S/renders/hero $S/export/castle.blend $S/export/city.blend $S/export/sites.blend 2>&1 | grep -E "rendered|Error|objects" | tail -12
echo "== log + pack"
python3 overlay_city.py $S
python3 make_log.py $S
python3 make_pack.py $S $S/pack_out/GothicValley_Greybox_Phase2
echo ALL_DONE
