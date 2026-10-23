# Blender: one Workbench view per prefab of a prefabs.blend, then a labelled contact sheet (Pillow).
import bpy, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from asset_lib import quick_views
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
out = a[1]; os.makedirs(out, exist_ok=True)
obs = [o for o in bpy.data.objects if o.type == "MESH"]
files = []
for o in obs:
    for p in obs:
        p.hide_render = p is not o
    files += [(o.name, quick_views([o], out, o.name, views=((215, 22),), res=(520, 420))[0])]
import json
json.dump(files, open(os.path.join(out, "views.json"), "w"))
