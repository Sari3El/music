#!/bin/bash
# terrain -> checks -> greybox, nav, audit, textures, FBX, renders, log, pack
S=$1
cd $S/scripts
rm -f $S/terrain/check_done
python3 terrain_gv.py $S > $S/terrain/terrain_log.txt 2>&1 && python3 terrain_check.py $S > $S/terrain/check_log.txt 2>&1
touch $S/terrain/check_done
grep -E "cuts" $S/terrain/terrain_log.txt; grep -E "PASS_ALL" $S/terrain/check_log.txt
$S/scripts/run_all.sh $S > $S/run_all.log 2>&1
echo "run_all exit $?"
