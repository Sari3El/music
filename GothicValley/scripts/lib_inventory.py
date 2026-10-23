import bpy, sys, os, re, json
import numpy as np
f = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.open_mainfile(filepath=f)
rows = []
for o in bpy.data.objects:
    if o.type != "MESH": continue
    co = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(o.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
    base = re.sub(r"^\d+_", "", o.name); base = re.sub(r"\.\d+", "", base); base = re.sub(r"_\d+$", "", base)
    rows.append(dict(name=o.name, type=base, lo=w.min(0).round(2).tolist(), hi=w.max(0).round(2).tolist(), tris=sum(len(p.vertices) - 2 for p in o.data.polygons)))
json.dump(rows, open(os.path.join(os.path.dirname(f), "inventory.json"), "w"))
import collections
by = collections.defaultdict(list)
for r in rows: by[r["type"]].append(r)
for t, L in sorted(by.items(), key=lambda kv: -len(kv[1])):
    s = np.array([np.array(r["hi"]) - np.array(r["lo"]) for r in L])
    zs = sorted(set(round(r["lo"][2], 1) for r in L))
    print(f"{len(L):4d} {t[:42]:42s} size~{np.median(s, 0).round(2).tolist()} z_lo {zs[:8]}")
