# Gothic Vampire Map - greybox setup for the Nanos World ADK (Unreal Engine 5.7)
# Run in the editor with the target level open:  Tools > Execute Python Script... > setup_map.py
#
# What it does (Phase 2 of the build plan, section 12 of the design document):
#  1. imports every greybox FBX (simple collision UCX_, Nanite on) into /Game/<PACK>/Environment/... as listed in the doc
#  2. imports the generated textures (Textures/) and builds M_GB_MasterTex + one MI_ per surface (albedo, normal,
#     roughness; UVs are world metres / 2 m), with the matching physical material when the project has it
#  3. places every mesh at its world position (1 m = 100 UU, +X north, +Y east), doors/gates/portcullis as Movable
#  4. spawn markers (named empty actors), hero cameras V1-V8, blocking volumes behind the natural borders,
#     NavMeshBoundsVolumes (castle, city, roads), river + fen water (Water plugin, if enabled)
#  5. World Settings: GameMode override None, Kill Z -20000; one sky set (directional light, sky light, sky atmosphere,
#     height fog with volumetric fog) tagged "Sun"
#  6. asset packs (lodge, underground library, ...): imports their meshes (Content/Props, Content/Environment/Lodge),
#     builds their material instances from Textures/T_LB_*, T_FC_* (two-sided shells, translucent glass), places every
#     piece listed in Data/placements_*.json (no collision on them: the invisible UCX of the SM_GB_ meshes carry it) and
#     the point lights of Data/lights.json (lumens, warm candle / torch colours)
#  7. if a Landscape is already in the level: auto material M_GV_Landscape (grass, mud, road, rock, snow blended by the
#     splat map T_GV_Splat, which follows the terrain) + checks (crag at [720, 310] = +204 m)
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
TEXDIR = os.path.join(ROOT, "Textures")
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
          "GB_WinLit": (0.95, 0.62, 0.25), "GB_WinDark": (0.08, 0.09, 0.12), "GB_Rock": (0.30, 0.29, 0.28)}
PHYS = {"GB_Stone": "Stone", "GB_Roof": "Stone", "GB_Wood": "Wood", "GB_Interior": "Stone", "GB_Floor": "Stone", "GB_Detail": "Wood",
        "GB_Metal": "Metal", "GB_Plaster": "Stone", "GB_Tile": "Stone", "GB_Timber": "Wood", "GB_Water": "Water", "GB_Church": "Stone",
        "GB_Ground": "Dirt", "GB_Hedge": "Grass", "GB_Marker": "Wood", "GB_WinLit": "Wood", "GB_WinDark": "Wood", "GB_Rock": "Stone"}


def load_json_opt(name):
    p = os.path.join(DATA, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


KITMAT = load_json_opt("materials_kit.json") or {}                     # pack materials: colour, surface, flags
for _n, _k in KITMAT.items():
    COLORS[_n] = tuple(_k["color"]); PHYS[_n] = _k["phys"]


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


def import_textures():
    """Textures/T_*.jpg|png -> /Game/<PACK>/Textures, with the right compression for each map."""
    tasks, names = [], []
    for f in sorted(os.listdir(TEXDIR)):
        if f.startswith("T_") and f.lower().endswith((".png", ".jpg")):
            t = unreal.AssetImportTask()
            for k, v in (("filename", os.path.join(TEXDIR, f)), ("destination_path", f"{DEST}/Textures"), ("automated", True),
                         ("replace_existing", True), ("save", True)):
                t.set_editor_property(k, v)
            tasks.append(t); names.append(os.path.splitext(f)[0])
    AT.import_asset_tasks(tasks)
    tex = {}
    for name in names:
        a = EAL.load_asset(f"{DEST}/Textures/{name}")
        if a is None:
            warn("texture not imported: " + name)
            continue
        if name.endswith("_N"):
            a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            a.set_editor_property("srgb", False)
            a.set_editor_property("flip_green_channel", True)               # the maps are OpenGL (green up)
        elif name.endswith("_R"):
            a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
            a.set_editor_property("srgb", False)
        elif name.startswith("T_GV_Splat"):
            a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_VECTOR_DISPLACEMENTMAP)
            a.set_editor_property("srgb", False)
            a.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
            a.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
        EAL.save_loaded_asset(a)
        tex[name] = a
    log(f"{len(tex)} textures -> {DEST}/Textures")
    return tex


SAMPLER = {"D": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, "N": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
           "R": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS}


def tex_param(mat, name, default, kind, uv, x, y):
    t = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
    t.set_editor_property("parameter_name", name)
    t.set_editor_property("texture", default)
    t.set_editor_property("sampler_type", SAMPLER[kind])
    t.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
    MEL.connect_material_expressions(uv, "", t, "UVs")
    return t


def build_materials(tex):
    path = f"{DEST}/Materials"
    mp = f"{path}/M_GB_MasterTex"
    created = not EAL.does_asset_exist(mp)
    mat = AT.create_asset("M_GB_MasterTex", path, unreal.Material, unreal.MaterialFactoryNew()) if created else EAL.load_asset(mp)
    if created:
        tc = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -1200, 0)
        til = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1200, 150)
        til.set_editor_property("parameter_name", "Tiling"); til.set_editor_property("default_value", 1.0)
        uv = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -1000, 50)
        MEL.connect_material_expressions(tc, "", uv, "A"); MEL.connect_material_expressions(til, "", uv, "B")
        d = tex_param(mat, "BaseColorTex", tex["T_GB_Stone_D"], "D", uv, -700, -300)
        n = tex_param(mat, "NormalTex", tex["T_GB_Stone_N"], "N", uv, -700, 0)
        r = tex_param(mat, "RoughnessTex", tex["T_GB_Stone_R"], "R", uv, -700, 300)
        tint = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -700, -550)
        tint.set_editor_property("parameter_name", "Tint"); tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
        col = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -350, -350)
        MEL.connect_material_expressions(d, "RGB", col, "A"); MEL.connect_material_expressions(tint, "", col, "B")
        met = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -350, 150)
        met.set_editor_property("parameter_name", "Metallic"); met.set_editor_property("default_value", 0.0)
        emis = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 550)
        emis.set_editor_property("parameter_name", "Emissive"); emis.set_editor_property("default_value", 0.0)
        em = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -350, 500)
        MEL.connect_material_expressions(col, "", em, "A"); MEL.connect_material_expressions(emis, "", em, "B")
        MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
        MEL.connect_material_property(n, "RGB", unreal.MaterialProperty.MP_NORMAL)
        MEL.connect_material_property(r, "R", unreal.MaterialProperty.MP_ROUGHNESS)
        MEL.connect_material_property(met, "", unreal.MaterialProperty.MP_METALLIC)
        MEL.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        MEL.recompile_material(mat)
        EAL.save_loaded_asset(mat)
    glass = None
    if any(k.get("translucent") for k in KITMAT.values()):
        gp = f"{path}/M_GB_MasterGlass"
        if EAL.does_asset_exist(gp):
            glass = EAL.load_asset(gp)
        else:
            glass = AT.create_asset("M_GB_MasterGlass", path, unreal.Material, unreal.MaterialFactoryNew())
            glass.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
            glass.set_editor_property("two_sided", True)
            tc = MEL.create_material_expression(glass, unreal.MaterialExpressionTextureCoordinate, -900, 0)
            d = tex_param(glass, "BaseColorTex", tex["T_GB_Stone_D"], "D", tc, -600, -200)
            op = MEL.create_material_expression(glass, unreal.MaterialExpressionScalarParameter, -600, 200)
            op.set_editor_property("parameter_name", "Opacity"); op.set_editor_property("default_value", 0.35)
            rg = MEL.create_material_expression(glass, unreal.MaterialExpressionConstant, -600, 350)
            rg.set_editor_property("r", 0.08)
            MEL.connect_material_property(d, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
            MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
            MEL.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS)
            MEL.recompile_material(glass)
            EAL.save_loaded_asset(glass)
    masked = None
    if any(k.get("masked") for k in KITMAT.values()):                 # prop packs: alpha-cut leaves, flames (glow map)
        mp2 = f"{path}/M_GB_MasterMasked"
        if EAL.does_asset_exist(mp2):
            masked = EAL.load_asset(mp2)
        else:
            masked = AT.create_asset("M_GB_MasterMasked", path, unreal.Material, unreal.MaterialFactoryNew())
            masked.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
            masked.set_editor_property("two_sided", True)
            tc = MEL.create_material_expression(masked, unreal.MaterialExpressionTextureCoordinate, -1000, 0)
            d = tex_param(masked, "BaseColorTex", tex["T_GB_Stone_D"], "D", tc, -700, -300)
            n = tex_param(masked, "NormalTex", tex["T_GB_Stone_N"], "N", tc, -700, 0)
            r = tex_param(masked, "RoughnessTex", tex["T_GB_Stone_R"], "R", tc, -700, 300)
            e = tex_param(masked, "EmissiveTex", tex["T_GB_Stone_D"], "D", tc, -700, 600)
            tint = MEL.create_material_expression(masked, unreal.MaterialExpressionVectorParameter, -700, -550)
            tint.set_editor_property("parameter_name", "Tint"); tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
            col = MEL.create_material_expression(masked, unreal.MaterialExpressionMultiply, -350, -350)
            MEL.connect_material_expressions(d, "RGB", col, "A"); MEL.connect_material_expressions(tint, "", col, "B")
            met = MEL.create_material_expression(masked, unreal.MaterialExpressionScalarParameter, -350, 150)
            met.set_editor_property("parameter_name", "Metallic"); met.set_editor_property("default_value", 0.0)
            emis = MEL.create_material_expression(masked, unreal.MaterialExpressionScalarParameter, -700, 850)
            emis.set_editor_property("parameter_name", "Emissive"); emis.set_editor_property("default_value", 0.0)
            em = MEL.create_material_expression(masked, unreal.MaterialExpressionMultiply, -350, 650)
            MEL.connect_material_expressions(e, "RGB", em, "A"); MEL.connect_material_expressions(emis, "", em, "B")
            MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
            MEL.connect_material_property(n, "RGB", unreal.MaterialProperty.MP_NORMAL)
            MEL.connect_material_property(r, "R", unreal.MaterialProperty.MP_ROUGHNESS)
            MEL.connect_material_property(met, "", unreal.MaterialProperty.MP_METALLIC)
            MEL.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
            MEL.connect_material_property(d, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
            MEL.recompile_material(masked)
            EAL.save_loaded_asset(masked)
    phys = find_phys_materials()
    if not phys:
        warn("no PhysicalMaterial found in the project: footstep sounds will use the default (assign the ADK ones to the MI_GB_ later)")
    mis = {}
    for name, c in COLORS.items():
        ip = f"{path}/MI_{name}"
        mi = EAL.load_asset(ip) if EAL.does_asset_exist(ip) else AT.create_asset(f"MI_{name}", path, unreal.MaterialInstanceConstant,
                                                                                  unreal.MaterialInstanceConstantFactoryNew())
        kit = KITMAT.get(name, {})
        parent = glass if kit.get("translucent") and glass is not None else (masked if kit.get("masked") and masked is not None else mat)
        MEL.set_material_instance_parent(mi, parent)
        for prm, k in (("BaseColorTex", "D"), ("NormalTex", "N"), ("RoughnessTex", "R"), ("EmissiveTex", "E")):
            t = tex.get(f"T_{name}_{k}")
            if t is not None:
                MEL.set_material_instance_texture_parameter_value(mi, prm, t)
        if f"T_{name}_D" not in tex:                                            # water, markers: plain colour
            white = EAL.load_asset("/Engine/EngineResources/WhiteSquareTexture")
            if white is not None:
                MEL.set_material_instance_texture_parameter_value(mi, "BaseColorTex", white)
            MEL.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(c[0], c[1], c[2], 1.0))
        if name == "GB_WinLit":
            MEL.set_material_instance_scalar_parameter_value(mi, "Emissive", 6.0)
        if name == "GB_Metal":
            MEL.set_material_instance_scalar_parameter_value(mi, "Metallic", 0.7)
        if kit.get("metallic"):
            MEL.set_material_instance_scalar_parameter_value(mi, "Metallic", float(kit["metallic"]))
        if kit.get("emissive") and not kit.get("translucent"):
            MEL.set_material_instance_scalar_parameter_value(mi, "Emissive", float(kit["emissive"]))
        if kit.get("two_sided"):                                              # single-sided shells seen from inside
            try:
                ov = mi.get_editor_property("base_property_overrides")
                ov.set_editor_property("override_two_sided", True)
                ov.set_editor_property("two_sided", True)
                mi.set_editor_property("base_property_overrides", ov)
            except Exception as ex:
                warn(f"MI_{name}: two-sided override not set ({ex}); tick Two Sided in its details panel")
        pm = phys.get(PHYS[name])
        if pm is not None:
            try:
                mi.set_editor_property("phys_material", pm)
            except Exception:
                pass
        EAL.save_loaded_asset(mi)
        mis[name] = mi
    log(f"{len(mis)} material instances (textured), physical materials found: {sorted(phys)}")
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


MOTION = {}                                                              # name -> extra tags (sliding pieces)
for _m in (load_json_opt("ue_extra.json") or {}).get("movable", []):
    if _m.get("motion") == "slide":
        MOTION[_m["name"]] = ["Slide", "SlideOffsetCm_" + "_".join(str(int(round(v * 100))) for v in _m["offset"])]
ZONE = {"Environment/Lodge": "GV/Lodge", "Environment/Library": "GV/Lodge/Library", "Environment/Castle": "GV/Castle", "Environment/City": "GV/City", "Environment/Church": "GV/City/Church",
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
            tags = ["ScriptedDoor"] + MOTION.get(r["name"], [])
            a.set_editor_property("tags", [unreal.Name(t) for t in tags])
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


# ------------------------------------------------------------------ 3b. asset packs: kit meshes, placements, lights
def import_kit():
    kit = load_json_opt("kit_report.json") or []
    if kit:
        import_all(kit)
    return kit


ZONE_OF = {"placements_lodge.json": "GV/Lodge", "placements_castle.json": "GV/Castle"}


def place_kit(mis):
    import glob
    done = {}
    for f in sorted(glob.glob(os.path.join(DATA, "placements_*.json"))):
        zone = ZONE_OF.get(os.path.basename(f), "GV/Props")
        n = 0
        for p in load_json(os.path.basename(f)):
            key = f"{DEST}/{p['folder']}/{p['mesh']}"
            mesh = done.get(key)
            if mesh is None:
                mesh = EAL.load_asset(key)
                if mesh is None:
                    warn("missing kit mesh after import: " + p["mesh"])
                    continue
                assign_materials(mesh, mis)
                done[key] = mesh
            a = ACT.spawn_actor_from_object(mesh, ue(p["loc"]), unreal.Rotator(0.0, 0.0, p["yaw"]))
            a.set_actor_scale3d(unreal.Vector(*p["scale"]))
            a.set_folder_path(zone + "/" + p["folder"].split("/")[-1])
            smc = a.get_component_by_class(unreal.StaticMeshComponent)
            if p.get("collision") == "complex":                                 # big shells (castle): per-polygon collision
                try:
                    bs = mesh.get_editor_property("body_setup")
                    bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
                    EAL.save_loaded_asset(mesh)
                except Exception as ex:
                    warn(f"{p['mesh']}: set Collision Complexity to 'Use Complex Collision As Simple' by hand ({ex})")
            else:
                smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)  # the SM_GB_ UCX hulls are the collision
            n += 1
        REPORT["placed"] += n
        log(f"{n} kit pieces placed from {os.path.basename(f)}")


def lights():
    n = 0
    for L in load_json_opt("lights.json") or []:
        a = spawn(unreal.PointLight, ue(L["xyz"]), label="LIGHT_" + L["name"], folder="GV/Lights")
        c = a.get_component_by_class(unreal.PointLightComponent)
        try:
            c.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
        except Exception:
            pass
        c.set_editor_property("intensity", float(L["lumens"]))
        c.set_editor_property("attenuation_radius", float(L["radius"]) * 100.0)
        c.set_editor_property("source_radius", 4.0)
        c.set_editor_property("cast_shadows", bool(L["shadows"]))
        c.set_light_color(unreal.LinearColor(L["color"][0], L["color"][1], L["color"][2], 1.0))
        n += 1
    if n:
        log(f"{n} point lights (candles, chandeliers, torches)")


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
    cmo = load_json_opt("castle_meta.json") or {}                       # castle model: spawn heights, re-aimed hero views
    spo, hvo = cmo.get("spawn_overrides", {}), cmo.get("hero_views", {})
    for s in manifest["spawn_markers"]:
        spawn(unreal.TargetPoint, ue(spo.get(s["id"], s["xyz"])), label=f"SPAWN_{s['id']}", folder="GV/Spawns",
              tags=["Spawn"] + (["DefaultSpawn"] if s.get("default") else []))
    for v in [dict(v, **hvo.get(v["id"], {})) for v in manifest["hero_views"]]:
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
                       ("NAV_Approach", (450, -60, 120), (330, 200, 120)), ("NAV_Valley", (-250, 0, 40), (1250, 1300, 220)),
                       ("NAV_LodgeLibrary", (-1391, -610, 62), (40, 105, 30))):
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
def landscape_material(tex):
    """Auto material: grass, then mud (banks, fen), road, paving (town, castle), rock (slopes over ~35 deg) and snow
    (above +385 m), blended by T_GV_Splat / T_GV_Splat2 sampled in world space (they cover -1512..+1512 m), layers tiled
    every 4 m."""
    path = f"{DEST}/Materials"
    mp = f"{path}/M_GV_Landscape"
    if EAL.does_asset_exist(mp):
        return EAL.load_asset(mp)
    mat = AT.create_asset("M_GV_Landscape", path, unreal.Material, unreal.MaterialFactoryNew())
    E = lambda cls, x, y: MEL.create_material_expression(mat, cls, x, y)
    wp = E(unreal.MaterialExpressionWorldPosition, -2400, 0)
    rg = E(unreal.MaterialExpressionComponentMask, -2200, 0)
    for ch, on in (("r", True), ("g", True), ("b", False), ("a", False)):
        rg.set_editor_property(ch, on)
    MEL.connect_material_expressions(wp, "", rg, "")
    tile = E(unreal.MaterialExpressionDivide, -2000, -200); tile.set_editor_property("const_b", 400.0)
    MEL.connect_material_expressions(rg, "", tile, "A")
    off = E(unreal.MaterialExpressionAdd, -2000, 200); off.set_editor_property("const_b", 151200.0)
    MEL.connect_material_expressions(rg, "", off, "A")
    suv = E(unreal.MaterialExpressionDivide, -1850, 200); suv.set_editor_property("const_b", 302400.0)
    MEL.connect_material_expressions(off, "", suv, "A")

    def sample(t, kind, uv, x, y):
        n = E(unreal.MaterialExpressionTextureSample, x, y)
        n.set_editor_property("texture", t)
        n.set_editor_property("sampler_type", SAMPLER.get(kind, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR))
        n.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
        MEL.connect_material_expressions(uv, "", n, "UVs")
        return n
    sp = sample(tex["T_GV_Splat"], "S", suv, -1600, 600)
    sp.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_FROM_TEXTURE_ASSET)   # clamped, never repeats
    sp2 = sample(tex["T_GV_Splat2"], "S", suv, -1600, 850)
    sp2.set_editor_property("sampler_source", unreal.SamplerSourceMode.SSM_FROM_TEXTURE_ASSET)
    layers = ["L_Grass", "L_Mud", "L_Road", "L_Paving", "L_Rock", "L_Snow"]
    alpha = {"L_Mud": (sp, "B"), "L_Road": (sp, "G"), "L_Paving": (sp2, "R"), "L_Rock": (sp, "R"), "L_Snow": (sp, "A")}
    outs = {}
    for j, (k, pin) in enumerate((("D", "RGB"), ("N", "RGB"), ("R", "R"))):
        cur = sample(tex[f"T_L_Grass_{k}"], k, tile, -1400, -900 + j * 900)
        cur_pin = pin
        for i, L in enumerate(layers[1:]):
            s_ = sample(tex[f"T_{L}_{k}"], k, tile, -1100 + i * 250, -800 + j * 900)
            lp = E(unreal.MaterialExpressionLinearInterpolate, -950 + i * 250, -700 + j * 900)
            MEL.connect_material_expressions(cur, cur_pin, lp, "A")
            MEL.connect_material_expressions(s_, pin, lp, "B")
            MEL.connect_material_expressions(alpha[L][0], alpha[L][1], lp, "Alpha")
            cur, cur_pin = lp, ""
        outs[k] = cur
    macro_uv = E(unreal.MaterialExpressionDivide, -2000, -500); macro_uv.set_editor_property("const_b", 25000.0)
    MEL.connect_material_expressions(rg, "", macro_uv, "A")
    macro = sample(tex["T_L_Grass_R"], "R", macro_uv, -1600, -1300)            # large-scale tone variation, breaks the tiling
    mm = E(unreal.MaterialExpressionMultiply, -1300, -1300); mm.set_editor_property("const_b", 1.4)
    MEL.connect_material_expressions(macro, "R", mm, "A")
    col = E(unreal.MaterialExpressionMultiply, -200, -700)
    MEL.connect_material_expressions(outs["D"], "", col, "A"); MEL.connect_material_expressions(mm, "", col, "B")
    MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(outs["N"], "", unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(outs["R"], "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat)
    return mat


def landscape_checks(tex):
    lands = [a for a in ACT.get_all_level_actors() if isinstance(a, unreal.LandscapeProxy)]
    if not lands:
        warn("no Landscape in the level yet: import Heightmap/heightmap_base_4033.png first (see the top of this script), then run again")
        return
    mat = landscape_material(tex)
    for l in lands:
        cur = l.get_editor_property("landscape_material")
        if cur is None or cur.get_name() == "M_GB_Landscape":                   # never overrides a material of yours
            l.set_editor_property("landscape_material", mat)
            log(f"landscape material: {mat.get_name()}")
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
    with unreal.ScopedSlowTask(7, "Gothic Vampire Map - greybox") as task:
        task.make_dialog(True)
        task.enter_progress_frame(1, "Import FBX")
        import_all(report)
        import_kit()
        task.enter_progress_frame(1, "Textures and materials")
        tex = import_textures()
        mis = build_materials(tex)
        task.enter_progress_frame(1, "Placement")
        clear_previous()
        place_meshes(report, mis)
        task.enter_progress_frame(1, "Asset packs: placements and lights")
        place_kit(mis)
        lights()
        task.enter_progress_frame(1, "Markers, cameras, volumes, water")
        markers(manifest, extra)
        water(manifest)
        task.enter_progress_frame(1, "World settings and sky")
        world_settings()
        task.enter_progress_frame(1, "Landscape")
        landscape_checks(tex)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log(f"done: {REPORT['imported']} meshes imported, {REPORT['placed']} placed, {len(REPORT['warnings'])} warning(s)")
    for w in REPORT["warnings"]:
        unreal.log_warning("GV | " + w)


main()
