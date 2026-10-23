# Blender: cut reusable prefabs out of the Classic Library scene (assets/library/library.blend). Each prefab joins the
# pieces found in a box of the source scene, gets its pivot at the base centre (or a given point) and is saved, alone,
# in assets/library/prefabs.blend; prefabs.json records their sizes. Coordinates below are the source scene's (metres).
import bpy, sys, os, json, re
import numpy as np
from mathutils import Vector, Matrix

a = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = a[0], a[1]
bpy.ops.wm.open_mainfile(filepath=SRC)
MESH = [o for o in bpy.data.objects if o.type == "MESH"]


def wbox(o):
    co = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(o.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
    return w.min(0), w.max(0)


BOX = {o.name: wbox(o) for o in MESH}


def pick(lo, hi, types=None, names=None, centre_inside=True):
    out = []
    for o in MESH:
        if names is not None and o.name not in names:
            continue
        t = re.sub(r"_\d+$", "", re.sub(r"\.\d+", "", re.sub(r"^\d+_", "", o.name)))     # "0181_Chair.001_Glossy wood_0" -> "Chair_Glossy wood"
        if types is not None and not any(t.startswith(k) for k in types):
            continue
        l, h = BOX[o.name]
        c = (l + h) / 2
        ok = np.all(c >= lo) and np.all(c <= hi) if centre_inside else (np.all(l >= np.array(lo) - 0.05) and np.all(h <= np.array(hi) + 0.05))
        if ok:
            out.append(o)
    return out


PREF = {}


def make(name, obs, pivot=None, rot_z=0.0, clip=None):
    """Duplicate + join `obs`, pivot at `pivot` (world) or the base centre; optionally keep only faces inside `clip`."""
    if not obs:
        print("EMPTY", name); return
    bpy.ops.object.select_all(action="DESELECT")
    dups = []
    for o in obs:
        d = o.copy(); d.data = o.data.copy(); bpy.context.scene.collection.objects.link(d); dups.append(d)
    for d in dups:
        d.select_set(True)
    bpy.context.view_layer.objects.active = dups[0]
    if len(dups) > 1:
        bpy.ops.object.join()
    j = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if clip is not None:                                   # drop faces outside the clip box (shared meshes like the stained glass)
        import bmesh
        bm = bmesh.new(); bm.from_mesh(j.data)
        lo, hi = np.array(clip[0]), np.array(clip[1])
        kill = [f for f in bm.faces if not (np.all(np.array(f.calc_center_median()) >= lo) and np.all(np.array(f.calc_center_median()) <= hi))]
        bmesh.ops.delete(bm, geom=kill, context="FACES"); bm.to_mesh(j.data); bm.free()
    co = np.empty(len(j.data.vertices) * 3); j.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    lo, hi = co.min(0), co.max(0)
    p = np.array(pivot, float) if pivot is not None else np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
    j.data.transform(Matrix.Translation(Vector(-p)))
    if rot_z:
        j.data.transform(Matrix.Rotation(np.radians(rot_z), 4, "Z"))
    j.data.update(); j.location = (0, 0, 0); j.name = name; j.data.name = name
    co = np.empty(len(j.data.vertices) * 3); j.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    PREF[name] = dict(lo=co.min(0).round(3).tolist(), hi=co.max(0).round(3).tolist(), tris=sum(len(f.vertices) - 2 for f in j.data.polygons),
                      materials=[m.name for m in j.data.materials])
    j["prefab"] = True
    print("PREFAB", name, PREF[name]["lo"], PREF[name]["hi"], PREF[name]["tris"])


# Scene grid: columns centred on x, y = 10k + 5 (base z 0, springing 12.03), vault bays centred on 10k, main floor z 4.03.
# Pivots: architecture at the floor (4.03) or the springing line (12.03), furniture at the floor, chandeliers at the hook.
FLOOR = 4.03
make("PF_LB_Column", pick([4.5, -5.5, -1], [5.5, -4.5, 13], types=["Collum"]), pivot=[5.0, -5.0, FLOOR])
make("PF_LB_Vault", pick([-1, -11, 11], [1, -9, 23], types=["Cross vault", "Vaulted roof", "Ceiling top trim", "Vaulted ceiling centerpiece"]),
     pivot=[0.0, -10.0, 12.03])
make("PF_LB_Rib", pick([-1, -15.5, 11], [1, -14.5, 23], types=["Ceiling arch"]), pivot=[0.0, -15.0, 12.03])      # 9 m along X
# window wall (east wall of the scene, x = 5, bay y -15..-5): sandstone wall + gothic frame + leaded glazing; local -X = inside
make("PF_LB_WindowWall", pick([4.4, -15.2, 0], [5.6, -4.8, 30], types=["Wall_Sandstone", "stone window frame", "Glass frame"]),
     pivot=[5.0, -10.0, FLOOR])
make("PF_LB_StainedGlass", [o for o in MESH if o.name.split("_", 1)[1].startswith("Stained glass")], pivot=[5.0, -10.0, FLOOR],
     clip=([4.3, -13.2, 0], [5.9, -6.8, 30]))
make("PF_LB_WallPlain", pick([-5.6, 4.8, 0], [-4.4, 15.2, 30], types=["Wall_Sandstone"]), pivot=[-5.0, 10.0, FLOOR])
# bookcase against a wall (x 4.16..4.76, y -12.46..-7.56, 4.9 x 0.6 x 2.7 m) with its books; local +X = back
make("PF_LB_Bookcase", pick([4.0, -12.6, 3.9], [5.0, -7.4, 6.9], types=["Bookcase", "Bookshelf", "SHC Old Book"]), pivot=[4.76, -10.01, FLOOR])
# freestanding double bookcase (two units back to back, y -5.64..-4.44)
make("PF_LB_BookcaseDouble", pick([-4.3, -5.8, 3.9], [0.8, -4.3, 6.9], types=["Bookcase", "Bookshelf", "SHC Old Book"]), pivot=[-1.75, -5.04, FLOOR])
# furniture
make("PF_LB_ReadingSet", pick([-3.3, -11.3, 3.9], [-0.5, -8.6, 5.0], types=["Table", "Chair"]), pivot=[-1.95, -9.935, FLOOR])
make("PF_LB_Chandelier", pick([-11, -11, 11], [-9, -9, 17], types=["Chandelier"]), pivot=[-10.0, -10.0, 16.19])
make("PF_LB_ChandelierLong", pick([-1, -11, 11], [1, -9, 25], types=["Chandelier"]), pivot=[0.0, -10.0, 24.06])
make("PF_LB_SpiralStair", pick([-13.0, -13.0, 5.0], [-9.4, -9.4, 12.0], types=["Plane_Metal", "Stair rail end", "metal platform", "Metal rail bars"]),
     pivot=[-11.12, -11.1, 5.53])
make("PF_LB_RailingWood", pick([-5.0, -2.6, 3.9], [0.4, -2.1, 5.4], types=["Wooden railing"]), pivot=[-2.245, -2.345, FLOOR])
make("PF_LB_Bridge", pick([-11.2, -5.3, 9.9], [-8.8, 5.3, 12.6], types=["Bridge"]), pivot=[-10.0, 0.0, 10.33])
make("PF_LB_DoorArch", pick([-10.6, -1.3, 2.4], [-10.1, 1.3, 6.1], types=["door arch"]), pivot=[-10.36, 0.0, 2.53])
make("PF_LB_Door", pick([-10.6, -1.3, 2.4], [-10.1, 1.3, 6.1], types=["Door", "door arch"]), pivot=[-10.36, 0.0, 2.53])


def make_clipped(name, case_types, box, pivot, rot_z=0.0):
    """Straight piece of a long or L-shaped unit: the casework is cut by the box planes, books kept whole (by centre)."""
    import bmesh
    lo, hi = np.array(box[0], float), np.array(box[1], float)
    case = [o for o in MESH if any(re.sub(r"_\d+$", "", re.sub(r"\.\d+", "", re.sub(r"^\d+_", "", o.name))).startswith(t) for t in case_types)
            and np.all(BOX[o.name][1] > lo) and np.all(BOX[o.name][0] < hi)]
    books = pick(lo + [0, 0.3, 0] if box[1][1] - box[0][1] < 6 else lo, hi - [0, 0.3, 0] if box[1][1] - box[0][1] < 6 else hi,
                 types=["SHC Old Book"])                     # whole books only, none hanging over the cut ends
    make(name, case + books, pivot=pivot, rot_z=rot_z)
    j = bpy.data.objects[name]
    p = np.array(pivot, float)
    lo_l, hi_l = lo - p, hi - p
    if rot_z:                                              # box in the rotated frame (180 deg only)
        lo_l, hi_l = np.array([-hi_l[0], -hi_l[1], lo_l[2]]), np.array([-lo_l[0], -lo_l[1], hi_l[2]])
    bm = bmesh.new(); bm.from_mesh(j.data)
    bookmat = {i for i, m in enumerate(j.data.materials) if m and m.name in ("LB_OldBook", "LB_Paper")}
    for ax in range(3):
        for val, keep_pos in ((lo_l[ax], True), (hi_l[ax], False)):
            nrm = [0, 0, 0]; nrm[ax] = 1
            geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
            res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=[val if k == ax else 0 for k in range(3)], plane_no=nrm,
                                         clear_inner=False, clear_outer=False)
            kill = [f for f in bm.faces if f.material_index not in bookmat and
                    ((f.calc_center_median()[ax] < val - 1e-4) if keep_pos else (f.calc_center_median()[ax] > val + 1e-4))]
            bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(j.data); bm.free(); j.data.update()
    co = np.empty(len(j.data.vertices) * 3); j.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    PREF[name].update(lo=co.min(0).round(3).tolist(), hi=co.max(0).round(3).tolist(), tris=sum(len(f.vertices) - 2 for f in j.data.polygons))
    print("CLIPPED", name, PREF[name]["lo"], PREF[name]["hi"], PREF[name]["tris"])


# tall gallery bookcases: the straight leg of the L units (x -14.75..-14.15, y -12.5..-7.5), lower (4.75 m) and upper
# (5.8 m with its cornice); turned 180 deg so that, like PF_LB_Bookcase, the back is at x = 0 and the front faces -X
CASE = ["Bookcase", "Bookshelf"]
make_clipped("PF_LB_BookcaseTall", CASE, ([-14.8, -12.5, 5.45], [-14.0, -7.5, 10.31]), [-14.75, -10.0, 5.53], rot_z=180)
make_clipped("PF_LB_BookcaseTallUpper", CASE, ([-14.8, -12.5, 10.31], [-14.0, -7.5, 16.5]), [-14.75, -10.0, 10.33], rot_z=180)

def hull2d(P):
    """Monotone-chain convex hull, counter-clockwise."""
    P = sorted(set(map(tuple, np.round(P, 4))))
    if len(P) < 3:
        return np.array(P)
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo_, up_ = [], []
    for p in P:
        while len(lo_) >= 2 and cross(lo_[-2], lo_[-1], p) <= 0: lo_.pop()
        lo_.append(p)
    for p in reversed(P):
        while len(up_) >= 2 and cross(up_[-2], up_[-1], p) <= 0: up_.pop()
        up_.append(p)
    return np.array(lo_[:-1] + up_[:-1])


# spiral stair treads (upward faces) for the collision hulls: convex outline + height of each step, in prefab coords
import bmesh
j = bpy.data.objects["PF_LB_SpiralStair"]
bm = bmesh.new(); bm.from_mesh(j.data); bm.faces.ensure_lookup_table()
tr = []
for f in bm.faces:
    if f.normal.z > 0.97 and f.calc_area() > 0.02:
        tr.append((round(f.calc_center_median().z, 2), [tuple(v.co[:2]) for v in f.verts], f.calc_area()))
bm.free()
by = {}
for z, pts, ar in tr:
    by.setdefault(z, []).append((pts, ar))
steps = []
for z in sorted(by):
    pts = np.array([p for ps, _ in by[z] for p in ps]); ar = sum(a for _, a in by[z])
    if ar < 0.08:
        continue
    poly = hull2d(pts)
    if len(poly) < 3:
        continue
    steps.append(dict(z=z, area=round(ar, 3), poly=np.round(poly, 3).tolist()))
PREF["PF_LB_SpiralStair"]["treads"] = steps
print("TREADS", len(steps), [s["z"] for s in steps])

# keep only the prefabs in the file
for o in list(bpy.data.objects):
    if not o.get("prefab"):
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.outliner.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "prefabs.blend"))
json.dump(PREF, open(os.path.join(OUT, "prefabs.json"), "w"), indent=1)
print("DONE", len(PREF))
