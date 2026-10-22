# Greybox sanity checks: naming/folders, stray primitives, triangle and collision budgets, ceiling heights (>= 4 m),
# interiors count (>= 25), city building count (260-320), towers, spirals and stairs rules recorded by the generators.
import sys, os, json
import numpy as np

ROOT = sys.argv[1]
FOLDERS = {"Maps", "Environment/Castle", "Environment/City", "Environment/Church", "Environment/Manor", "Environment/Ruins",
           "Environment/Nature", "Environment/Landscape", "Environment/Props"}
WIDE = ("Walls", "Backdrop", "Houses", "Stairs", "SerpentineWall", "RoadProps", "Signposts", "Fen", "Hamlet", "Faubourg", "Exterior",
        "Docks", "Watermills", "BorderPost", "Cemetery", "Gates")
rep = dict(groups=0, prims=0, tris=0, hulls=0, issues=[], per_file={})
for part in ("castle", "city", "sites"):
    G = json.load(open(f"{ROOT}/greybox/{part}_groups.json"))
    n_tri = 0
    for g in G:
        rep["groups"] += 1
        if not g["name"].startswith("SM_"):
            rep["issues"].append(f"{g['name']}: missing SM_ prefix")
        if g["folder"] not in FOLDERS:
            rep["issues"].append(f"{g['name']}: folder {g['folder']} not in the document's list")
        cen = np.array([np.mean(np.asarray(p["v"], float), 0) for p in g["prims"]])
        med = np.median(cen, 0)
        far = np.hypot(cen[:, 0] - med[0], cen[:, 1] - med[1])
        lim = 2500 if any(w in g["name"] for w in WIDE) else 260
        if (far > lim).any():
            rep["issues"].append(f"{g['name']}: {int((far > lim).sum())} primitive(s) more than {lim} m from the group centre")
        for p in g["prims"]:
            t = sum(len(f) - 2 for f in p["f"])
            n_tri += t if p["col"] != "only" else 0
            rep["hulls"] += p["col"] is not False
        rep["prims"] += len(g["prims"])
    rep["tris"] += n_tri
    rep["per_file"][part] = dict(groups=len(G), tris=n_tri)
rooms = []
for part in ("castle", "city", "sites"):
    m = json.load(open(f"{ROOT}/greybox/{part}_meta.json"))
    for r in m.get("rooms", []):
        r["part"] = part
        rooms.append(r)
low = [r for r in rooms if r["z1"] - r["z0"] < 4.0 - 1e-6]
rep["rooms"] = len(rooms)
rep["rooms_under_4m"] = [(r["part"], r["name"], round(r["z1"] - r["z0"], 2)) for r in low]
city = json.load(open(f"{ROOT}/greybox/city_meta.json"))
sites = json.load(open(f"{ROOT}/greybox/sites_meta.json"))
interiors = sorted({r.get("interior") for r in rooms if r.get("interior")} - {"site", "ruin", "cave"})
named = (["Great Church", "Noble Manor", "Town hall", "Guild hall", "City Watch barracks"] + [e["name"] for e in city["interiors"]] +
         [r["name"] for r in sites["rooms"] if r.get("interior") in ("mortuary_chapel", "faubourg_stables", "watermill", "dock_warehouse")])
rep["enterable_interiors"] = len(named)
rep["enterable_list"] = named
rep["city_buildings_inside_walls"] = city["buildings_inside_walls"]
rep["checks"] = {"interiors >= 25": len(named) >= 25, "city buildings 260-320": 260 <= city["buildings_inside_walls"] <= 320,
                 "city towers 16": len(city["towers"]) == 16, "ceilings >= 4 m": not low,
                 "castle stairs <= 28 deg": sites["stairs"]["max_angle_deg"] <= 28.0 + 1e-6, "no stray primitives": not any("primitive" in i for i in rep["issues"])}
json.dump(rep, open(f"{ROOT}/greybox/gb_checks.json", "w"), indent=1)
print(json.dumps({k: v for k, v in rep.items() if k not in ("enterable_list",)}, indent=1))
