# Gothic Vampire Map - greybox setup for the Nanos World ADK (Unreal Engine 5.7)
# Run in the editor with the target level open:  Tools > Execute Python Script... > setup_map.py
#
# What it does (Phase 2 of the build plan, section 12 of the design document):
#  1. imports every greybox FBX (simple collision UCX_, Nanite on) into /Game/<PACK>/Environment/... as listed in the doc
#  2. builds M_GB_Master + one MI_ per greybox surface, with the matching physical material when the project has it
#  3. places every mesh at its world position (1 m = 100 UU, +X north, +Y east), doors/gates/portcullis as Movable
#  4. spawn markers (named empty actors), hero cameras V1-V8, blocking volumes behind the natural borders,
#     NavMeshBoundsVolumes (castle, city, roads), river + fen water (Water plugin, if enabled)
#  5. World Settings: GameMode override None, Kill Z -20000; one sky set (directional light, sky light, sky atmosphere,
#     height fog with volumetric fog) tagged "Sun"
#  6. if a Landscape is already in the level: placeholder auto material + checks (crag at [720, 310] = +204 m)
#
# The landscape itself is imported by hand first (Unreal Python cannot create a landscape):
#   Landscape mode > Manage > New > Import from File > Heightmap/heightmap_base_4033.png
#   Section size 63x63 quads, 2x2 sections per component, 32x32 components (4033 x 4033)
#   Location X -151200, Y -151200, Z 0 - Scale X 75, Y 75, Z 200
import os, json, math
import unreal

PACK = "GothicValley"                      # asset-pack folder under Content/ (the doc asks for one folder)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
FBX = os.path.join(ROOT, "Content")
DATA = os.path.join(ROOT, "Data")
DEST = "/Game/" + PACK
USE_NANITE = True
REPLACE_EXISTING_ACTORS = True             # removes the actors this script placed before (folder "GV/...") and re-places them

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
ACT = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
WORLD = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
REPORT = {"imported": 0, "placed": 0, "warnings": []}


def log(m):
    unreal.log("GV | " + m)


def warn(m):
    REPORT["warnings"].append(m)
    unreal.log_warning("GV | " + m)


def ue(p):
    """World metres [x north, y east, z up] -> Unreal units."""
    return unreal.Vector(p[0] * 100.0, p[1] * 100.0, p[2] * 100.0)


def load_json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ 1. import
def fbx_options():
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    d = ui.get_editor_property("static_mesh_import_data")
    d.set_editor_property("combine_meshes", True)
    d.set_editor_property("auto_generate_collision", False)            # the UCX_ hulls are the collision
    for k, v in (("one_convex_hull_per_ucx", True), ("generate_lightmap_u_vs", False), ("build_nanite", USE_NANITE),
                 ("remove_degenerates", True), ("import_uniform_scale", 1.0)):
        try:
            d.set_editor_property(k, v)
        except Exception:
            pass
    return ui


def import_all(report):
    by_folder = {}
    for r in report:
        by_folder.setdefault(r["folder"], []).append(r)
    try:                                                                 # legacy FBX pipeline keeps the UCX options
        unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
    except Exception:
        pass
    for folder, items in by_folder.items():
        tasks = []
        for r in items:
            t = unreal.AssetImportTask()
            t.set_editor_property("filename", os.path.join(FBX, folder, r["name"] + ".fbx"))
            t.set_editor_property("destination_path", f"{DEST}/{folder}")
            t.set_editor_property("automated", True)
            t.set_editor_property("replace_existing", True)
            t.set_editor_property("save", True)
            t.set_editor_property("options", fbx_options())
            tasks.append(t)
        AT.import_asset_tasks(tasks)
        REPORT["imported"] += len(tasks)
        log(f"{len(tasks)} meshes -> {DEST}/{folder}")


# ------------------------------------------------------------------ 2. materials
COLORS = {"GB_Stone": (0.42, 0.42, 0.44), "GB_Roof": (0.17, 0.15, 0.17), "GB_Wood": (0.40, 0.28, 0.18), "GB_Interior": (0.62, 0.60, 0.57),
          "GB_Floor": (0.50, 0.48, 0.45), "GB_Detail": (0.62, 0.16, 0.12), "GB_Metal": (0.12, 0.12, 0.14), "GB_Plaster": (0.72, 0.67, 0.56),
          "GB_Tile": (0.48, 0.24, 0.17), "GB_Timber": (0.30, 0.20, 0.13), "GB_Water": (0.22, 0.34, 0.42), "GB_Church": (0.70, 0.68, 0.62),
          "GB_Ground": (0.35, 0.33, 0.28), "GB_Hedge": (0.18, 0.26, 0.14), "GB_Marker": (0.95, 0.75, 0.10),
          "GB_WinLit": (0.95, 0.62, 0.25), "GB_WinDark": (0.08, 0.09, 0.12)}
PHYS = {"GB_Stone": "Stone", "GB_Roof": "Stone", "GB_Wood": "Wood", "GB_Interior": "Stone", "GB_Floor": "Stone", "GB_Detail": "Wood",
        "GB_Metal": "Metal", "GB_Plaster": "Stone", "GB_Tile": "Stone", "GB_Timber": "Wood", "GB_Water": "Water", "GB_Church": "Stone",
        "GB_Ground": "Dirt", "GB_Hedge": "Grass", "GB_Marker": "Wood", "GB_WinLit": "Wood", "GB_WinDark": "Wood"}


def find_phys_materials():
    """The ADK ships physical materials for footsteps; pick them up by name wherever they are."""
    found = {}
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/PhysicsCore", "PhysicalMaterial")], recursive_paths=True)
    for a in reg.get_assets(flt):
        n = str(a.asset_name).lower()
        for key in ("stone", "wood", "metal", "dirt", "grass", "water", "concrete", "rock"):
            if key in n and key.capitalize() not in found:
                found["Stone" if key in ("concrete", "rock") else key.capitalize()] = a.get_asset()
    return found


def build_materials():
    path = f"{DEST}/Materials"
    mp = f"{path}/M_GB_Master"
    created = not EAL.does_asset_exist(mp)
    mat = AT.create_asset("M_GB_Master", path, unreal.Material, unreal.MaterialFactoryNew()) if created else EAL.load_asset(mp)
    if created:
        col = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -600, 0)
        col.set_editor_property("parameter_name", "Color")
        col.set_editor_property("default_value", unreal.LinearColor(0.5, 0.5, 0.5, 1.0))
        rough = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -600, 250)
        rough.set_editor_property("parameter_name", "Roughness")
        rough.set_editor_property("default_value", 0.85)
        emis = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -600, 400)
        emis.set_editor_property("parameter_name", "Emissive")
        emis.set_editor_property("default_value", 0.0)
        mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -300, 400)
        MEL.connect_material_expressions(col, "", mul, "A")
        MEL.connect_material_expressions(emis, "", mul, "B")
        MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
        MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
        MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        MEL.recompile_material(mat)
        EAL.save_loaded_asset(mat)
    phys = find_phys_materials()
    if not phys:
        warn("no PhysicalMaterial found in the project: footstep sounds will use the default (assign the ADK ones to the MI_GB_ later)")
    mis = {}
    for name, c in COLORS.items():
        ip = f"{path}/MI_{name}"
        mi = EAL.load_asset(ip) if EAL.does_asset_exist(ip) else AT.create_asset(f"MI_{name}", path, unreal.MaterialInstanceConstant,
                                                                                  unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, mat)
        MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(c[0], c[1], c[2], 1.0))
        if name == "GB_WinLit":
            MEL.set_material_instance_scalar_parameter_value(mi, "Emissive", 4.0)
        if name == "GB_Water":
            MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", 0.1)
        pm = phys.get(PHYS[name])
        if pm is not None:
            try:
                mi.set_editor_property("phys_material", pm)
            except Exception:
                pass
        EAL.save_loaded_asset(mi)
        mis[name] = mi
    log(f"{len(mis)} material instances, physical materials found: {sorted(phys)}")
    return mis


def assign_materials(mesh, mis):
    mats = mesh.get_editor_property("static_materials")
    changed = False
    for i, sm in enumerate(mats):
        slot = str(sm.get_editor_property("material_slot_name"))
        base = slot.split(".")[0]
        for key in sorted(mis, key=len, reverse=True):
            if base.startswith(key):
                mesh.set_material(i, mis[key])
                changed = True
                break
    if USE_NANITE:
        try:
            ns = mesh.get_editor_property("nanite_settings")
            if not ns.get_editor_property("enabled"):
                ns.set_editor_property("enabled", True)
                mesh.set_editor_property("nanite_settings", ns)
                changed = True
        except Exception:
            pass
    if changed:
        EAL.save_loaded_asset(mesh)


# ------------------------------------------------------------------ 3. placement
def clear_previous():
    if not REPLACE_EXISTING_ACTORS:
        return
    n = 0
    for a in ACT.get_all_level_actors():
        if str(a.get_folder_path()).startswith("GV/"):
            ACT.destroy_actor(a)
            n += 1
    if n:
        log(f"{n} actors from a previous run removed")


ZONE = {"Environment/Castle": "GV/Castle", "Environment/City": "GV/City", "Environment/Church": "GV/City/Church",
        "Environment/Manor": "GV/City/Manor", "Environment/Ruins": "GV/Ruins", "Environment/Nature": "GV/Nature",
        "Environment/Landscape": "GV/Backdrop", "Environment/Props": "GV/Props", "Maps": "GV/Debug"}


def place_meshes(report, mis):
    for r in report:
        mesh = EAL.load_asset(f"{DEST}/{r['folder']}/{r['name']}")
        if mesh is None:
            warn("missing mesh after import: " + r["name"])
            continue
        assign_materials(mesh, mis)
        try:
            ncol = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).get_convex_collision_count(mesh)
            if r["ucx"] and ncol == 0:
                warn(f"{r['name']}: no simple collision imported (expected {r['ucx']} UCX hulls)")
        except Exception:
            pass
        a = ACT.spawn_actor_from_object(mesh, ue(r["location_m"]), unreal.Rotator(0, 0, 0))
        a.set_actor_label(r["name"].replace("SM_GB_", "GB_"))
        a.set_folder_path(ZONE.get(r["folder"], "GV/Other"))
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if r.get("movable"):
            smc.set_mobility(unreal.ComponentMobility.MOVABLE)
            a.set_editor_property("tags", [unreal.Name("ScriptedDoor")])
        if "Backdrop" in r["name"]:
            smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            smc.set_editor_property("cast_shadow", False)
        REPORT["placed"] += 1
    probe = [a for a in ACT.get_all_level_actors() if a.get_actor_label() == "GB_AxisProbe"]
    if probe:
        o, e = probe[0].get_actor_bounds(False)
        if abs(o.x - 100000) > 300 or abs(o.y - 50000) > 300:
            warn(f"axis probe at ({o.x:.0f}, {o.y:.0f}) instead of (100000, 50000): the FBX axes are swapped, report it")
        else:
            log("axis probe OK: +X north, +Y east")
        ACT.destroy_actor(probe[0])


# ------------------------------------------------------------------ 4. markers, cameras, volumes, water
def spawn(cls, loc, rot=(0, 0, 0), label=None, folder=None, tags=()):
    a = ACT.spawn_actor_from_class(cls, loc, unreal.Rotator(*rot))
    if label:
        a.set_actor_label(label)
    if folder:
        a.set_folder_path(folder)
    if tags:
        a.set_editor_property("tags", [unreal.Name(t) for t in tags])
    return a


def look_rot(cam, tgt):
    dx, dy, dz = tgt[0] - cam[0], tgt[1] - cam[1], tgt[2] - cam[2]
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    return (pitch, yaw, 0.0)          # unreal.Rotator(roll, pitch, yaw) is built below


def markers(manifest, extra):
    for s in manifest["spawn_markers"]:
        spawn(unreal.TargetPoint, ue(s["xyz"]), label=f"SPAWN_{s['id']}", folder="GV/Spawns",
              tags=["Spawn"] + (["DefaultSpawn"] if s.get("default") else []))
    for v in manifest["hero_views"]:
        p, y, _ = look_rot(v["camera"], v["look_at"])
        cam = ACT.spawn_actor_from_class(unreal.CineCameraActor, ue(v["camera"]), unreal.Rotator(0.0, p, y))
        cam.set_actor_label(f"HERO_{v['id']}_{v['name'].replace(' ', '_')}")
        cam.set_folder_path("GV/HeroViews")
    for b in extra.get("blockers", []):
        a = spawn(unreal.BlockingVolume, ue(b["centre"]), label=b["name"], folder="GV/Blocking")
        a.set_actor_scale3d(unreal.Vector(b["extent"][0], b["extent"][1], b["extent"][2]))   # default brush = 200 UU cube
        if a.get_actor_bounds(False)[1].x < 1.0:
            warn(f"{b['name']}: the volume has no brush; resize it by hand (half-size {b['extent']} m)")
    for name, c, e in (("NAV_Castle", (700, 260, 200), (190, 200, 120)), ("NAV_City", (-450, -460, 30), (260, 330, 80)),
                       ("NAV_Approach", (450, -60, 120), (330, 200, 120)), ("NAV_Valley", (-250, 0, 40), (1250, 1300, 220))):
        a = spawn(unreal.NavMeshBoundsVolume, ue(c), label=name, folder="GV/Navigation")
        a.set_actor_scale3d(unreal.Vector(e[0], e[1], e[2]))
    for m in extra.get("markers", []):
        spawn(unreal.TargetPoint, ue(m["xyz"]), label=("SIGN_" if m["name"] == "signpost" else "FX_") + m["name"],
              folder="GV/Markers", tags=[m["kind"].split(" ")[0]])


def water(manifest):
    cls = getattr(unreal, "WaterBodyRiver", None)
    if cls is None:
        warn("Water plugin not enabled: river not created (enable the whitelisted Water plugin and run again)")
        return
    pts = manifest["water"]["river"]["points_x_y_bedz_halfwidth"]
    riv = spawn(cls, ue([pts[0][0], pts[0][1], pts[0][2] + 1.5]), label="WATER_River", folder="GV/Water")
    try:
        spl = riv.get_water_spline()
        spl.clear_spline_points(True)
        for x, y, bz, hw in pts:
            spl.add_spline_point(ue([x, y, bz + 1.5]), unreal.SplineCoordinateSpace.WORLD, False)
        spl.update_spline()
        md = riv.get_editor_property("water_spline_metadata") if hasattr(riv, "get_editor_property") else None
        if md is not None:
            for i, (x, y, bz, hw) in enumerate(pts):
                try:
                    md.river_width.points[i].out_val = hw * 2 * 100
                    md.depth.points[i].out_val = 250.0
                except Exception:
                    pass
        log(f"river spline: {len(pts)} points (width/depth: check the spline metadata in the details panel)")
    except Exception as ex:
        warn(f"river spline could not be edited from Python ({ex}); move the points by hand using Data/layout_manifest.json")
    lake = getattr(unreal, "WaterBodyLake", None)
    if lake is not None:
        spawn(lake, ue([-1230, -1230, 3.0]), label="WATER_FenPools", folder="GV/Water")


# ------------------------------------------------------------------ 5. world settings + sky
def world_settings():
    ws = WORLD.get_world_settings()
    for k, v in (("default_game_mode", None), ("kill_z", -20000.0)):
        try:
            ws.set_editor_property(k, v)
        except Exception as ex:
            warn(f"world settings {k}: {ex}")
    log("World Settings: GameMode override None, Kill Z -20000")
    have = {type(a).__name__ for a in ACT.get_all_level_actors()}
    sky = [("DirectionalLight", unreal.DirectionalLight, (-40.0, 135.0, 0.0)), ("SkyLight", unreal.SkyLight, (0, 0, 0)),
           ("SkyAtmosphere", unreal.SkyAtmosphere, (0, 0, 0)), ("ExponentialHeightFog", unreal.ExponentialHeightFog, (0, 0, 0))]
    for nm, cls, rot in sky:
        if nm in have:
            for a in ACT.get_all_level_actors():
                if type(a).__name__ == nm:
                    tags = list(a.get_editor_property("tags"))
                    if unreal.Name("Sun") not in tags:
                        a.set_editor_property("tags", tags + [unreal.Name("Sun")])
            continue
        a = ACT.spawn_actor_from_class(cls, unreal.Vector(0, 0, 50000), unreal.Rotator(rot[2], rot[0], rot[1]))
        a.set_actor_label(nm)
        a.set_folder_path("GV/Lighting")
        a.set_editor_property("tags", [unreal.Name("Sun")])
        if nm == "ExponentialHeightFog":
            try:
                fc = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
                fc.set_editor_property("volumetric_fog", True)
                fc.set_editor_property("fog_density", 0.004)
            except Exception:
                pass
        if nm == "SkyLight":
            try:
                a.get_component_by_class(unreal.SkyLightComponent).set_editor_property("real_time_capture", True)
            except Exception:
                pass


# ------------------------------------------------------------------ 6. landscape checks + placeholder material
def landscape_material():
    path = f"{DEST}/Materials"
    mp = f"{path}/M_GB_Landscape"
    if EAL.does_asset_exist(mp):
        return EAL.load_asset(mp)
    mat = AT.create_asset("M_GB_Landscape", path, unreal.Material, unreal.MaterialFactoryNew())
    nrm = MEL.create_material_expression(mat, unreal.MaterialExpressionVertexNormalWS, -900, 0)
    msk = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -700, 0)
    msk.set_editor_property("r", False); msk.set_editor_property("g", False); msk.set_editor_property("b", True)
    MEL.connect_material_expressions(nrm, "", msk, "")
    pw = MEL.create_material_expression(mat, unreal.MaterialExpressionPower, -500, 0)
    ex = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -700, 150)
    ex.set_editor_property("r", 8.0)
    MEL.connect_material_expressions(msk, "", pw, "Base")
    MEL.connect_material_expressions(ex, "", pw, "Exp")
    rock = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -500, -250)
    rock.set_editor_property("constant", unreal.LinearColor(0.26, 0.25, 0.24, 1))
    grass = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -500, 250)
    grass.set_editor_property("constant", unreal.LinearColor(0.16, 0.18, 0.10, 1))
    lp = MEL.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -250, 0)
    MEL.connect_material_expressions(rock, "", lp, "A")
    MEL.connect_material_expressions(grass, "", lp, "B")
    MEL.connect_material_expressions(pw, "", lp, "Alpha")
    MEL.connect_material_property(lp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    r = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -250, 250)
    r.set_editor_property("r", 0.9)
    MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    return mat


def landscape_checks():
    lands = [a for a in ACT.get_all_level_actors() if isinstance(a, unreal.LandscapeProxy)]
    if not lands:
        warn("no Landscape in the level yet: import Heightmap/heightmap_base_4033.png first (see the top of this script), then run again")
        return
    mat = landscape_material()
    for l in lands:
        if l.get_editor_property("landscape_material") is None:
            l.set_editor_property("landscape_material", mat)
    checks = load_json("landscape_checks.json")
    for c in checks:
        start, end = ue([c["x"], c["y"], 600.0]), ue([c["x"], c["y"], -100.0])
        hit = unreal.SystemLibrary.line_trace_single(WORLD, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        if not hit:
            warn(f"landscape check {c['name']}: no hit")
            continue
        z = hit.to_tuple()[4].z / 100.0 if hasattr(hit, "to_tuple") else None
        if z is None:
            continue
        ok = abs(z - c["z"]) <= c.get("tol", 2.0)
        (log if ok else warn)(f"landscape check {c['name']}: {z:.1f} m (expected {c['z']} +- {c.get('tol', 2.0)}){'' if ok else ' - axes swapped or wrong scale?'}")


# ------------------------------------------------------------------ run
def main():
    report = load_json("build_report.json")
    manifest = load_json("layout_manifest.json")
    extra = load_json("ue_extra.json")
    with unreal.ScopedSlowTask(6, "Gothic Vampire Map - greybox") as task:
        task.make_dialog(True)
        task.enter_progress_frame(1, "Import FBX")
        import_all(report)
        task.enter_progress_frame(1, "Materials")
        mis = build_materials()
        task.enter_progress_frame(1, "Placement")
        clear_previous()
        place_meshes(report, mis)
        task.enter_progress_frame(1, "Markers, cameras, volumes, water")
        markers(manifest, extra)
        water(manifest)
        task.enter_progress_frame(1, "World settings and sky")
        world_settings()
        task.enter_progress_frame(1, "Landscape")
        landscape_checks()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log(f"done: {REPORT['imported']} meshes imported, {REPORT['placed']} placed, {len(REPORT['warnings'])} warning(s)")
    for w in REPORT["warnings"]:
        unreal.log_warning("GV | " + w)


main()
