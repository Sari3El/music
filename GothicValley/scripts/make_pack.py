# Assemble the deliverable: FBX tree, heightmap, data for the Unreal script, docs, renders, Nanos World export template.
import sys, os, re, json, shutil, glob, zipfile
from PIL import Image

ROOT = sys.argv[1]
OUT = sys.argv[2]                         # pack folder (zipped next to it)
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(f"{OUT}/Data", exist_ok=True)
shutil.copytree(f"{ROOT}/export/Content", f"{OUT}/Content")
os.makedirs(f"{OUT}/Heightmap", exist_ok=True)
shutil.copy(f"{ROOT}/terrain/heightmap_base_4033.png", f"{OUT}/Heightmap/heightmap_base_4033.png")
os.makedirs(f"{OUT}/Unreal", exist_ok=True)
shutil.copy(f"{ROOT}/pack/Unreal/setup_map.py", f"{OUT}/Unreal/setup_map.py")
os.makedirs(f"{OUT}/Textures", exist_ok=True)                                  # generated surface textures + splat map
for f in sorted(glob.glob(f"{ROOT}/textures/T_*")) + [f"{ROOT}/textures/textures.json"]:
    shutil.copy(f, f"{OUT}/Textures/")
# build report (all parts) -> one list
rep = []
for part in ("castle", "city", "sites"):
    rep += json.load(open(f"{ROOT}/greybox/build_report_{part}.json"))
json.dump(rep, open(f"{OUT}/Data/build_report.json", "w"), indent=1)
shutil.copy(f"{ROOT}/data/layout_manifest.json", f"{OUT}/Data/layout_manifest.json")
shutil.copy(f"{ROOT}/data/roads_final.json", f"{OUT}/Data/roads_final.json")
sites = json.load(open(f"{ROOT}/greybox/sites_meta.json"))
json.dump(dict(blockers=sites["blockers"], markers=sites["markers"]), open(f"{OUT}/Data/ue_extra.json", "w"), indent=1)
json.dump([dict(name="castle crag top", x=720, y=310, z=203.85, tol=1.0), dict(name="barbican terrace", x=700, y=-40, z=199.0, tol=1.5),
           dict(name="market square", x=-470, y=-470, z=33.9, tol=1.5), dict(name="fen basin", x=-1230, y=-1230, z=3.4, tol=2.0),
           dict(name="ravine under the bridge", x=742, y=145, z=108.3, tol=6.0)], open(f"{OUT}/Data/landscape_checks.json", "w"), indent=1)
for part in ("castle", "city", "sites"):
    shutil.copy(f"{ROOT}/greybox/{part}_meta.json", f"{OUT}/Data/{part}_meta.json")
os.makedirs(f"{OUT}/Checks", exist_ok=True)
for f in (glob.glob(f"{ROOT}/terrain/phase1_checks.json") + glob.glob(f"{ROOT}/greybox/gb_checks.json") + glob.glob(f"{ROOT}/greybox/audit.json") + glob.glob(f"{ROOT}/greybox/nav/nav_*.json")
          + glob.glob(f"{ROOT}/terrain/*_master_map.png") + glob.glob(f"{ROOT}/terrain/topview_phase1.png") + glob.glob(f"{ROOT}/greybox/city_overlay_plan.png")):
    shutil.copy(f, f"{OUT}/Checks/")
if os.path.isdir(f"{ROOT}/renders/hero"):
    shutil.copytree(f"{ROOT}/renders/hero", f"{OUT}/Screenshots")
for f in ("README_FR.md", "BUILD_LOG.md"):
    if os.path.exists(f"{ROOT}/pack/{f}"):
        txt = re.sub(r"\b\d+ maillages", f"{len(rep)} maillages", open(f"{ROOT}/pack/{f}").read())
        open(f"{OUT}/{f}", "w").write(txt)
# Nanos World export template: Assets.toml + .webp thumbnail beside the .umap
os.makedirs(f"{OUT}/NanosWorld", exist_ok=True)
open(f"{OUT}/NanosWorld/Assets.toml", "w").write('''# Nanos World asset pack: copy the cooked folder into the server's Assets/ as "gothic-valley"
[assets_pack]
    name = "Gothic Valley"
    author = ""
    version = "0.2.0"

[assets.maps]
    # key = path of the .umap inside the cooked pack (no extension)
    gothic_valley = "Maps/GothicValley"

[assets.static_meshes]

[assets.blueprints]
''')
thumb = sorted(glob.glob(f"{ROOT}/renders/hero/V1*.png")) or sorted(glob.glob(f"{ROOT}/renders/hero/*.png"))
if thumb:
    Image.open(thumb[0]).convert("RGB").resize((512, 288)).save(f"{OUT}/NanosWorld/GothicValley.webp", "WEBP", quality=88)
# zip
zp = OUT.rstrip("/") + ".zip"
if os.path.exists(zp):
    os.remove(zp)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for dp, dn, fn in os.walk(OUT):
        for f in fn:
            full = os.path.join(dp, f)
            z.write(full, os.path.relpath(full, os.path.dirname(OUT)))
print("pack", zp, round(os.path.getsize(zp) / 1e6, 1), "MB")
