"""Extrait des tables du Toolkit (.tbl) les données d'apparence des races jouables du jeu.

Usage : python3 tools/extraire_donnees_jeu.py <dossier contenant les .tbl>
Fichiers attendus (noms libres, repérés par leur contenu) : Races*.tbl,
CharacterCreationPresets*.tbl, CharacterCreationAppearanceVisuals*.tbl.
Écrit tools/donnees_jeu.json, utilisé par build_mod.py pour les sous-races d'apparence.
"""
import glob
import json
import os
import sys
import xml.etree.ElementTree as ET

HUMANOID = "899d275e-9893-490a-9cd5-be856794929f"
LISTS = ["SkinColors", "EyeColors", "HairColors", "HairHighlightColors", "HairGrayingColors", "TattooColors",
         "MakeupColors", "LipsMakeupColors", "HornColors", "HornTipColors", "Visuals", "Tags"]

def read_tbl(path):
    rows = []
    root = ET.parse(path).getroot()
    for so in root.iter("stat_object"):
        rows.append({f.get("name"): (f.get("value") if f.get("value") is not None else f.get("handle"))
                     for f in so.iter("field")})
    return root.get("stat_object_definition_id"), rows


def main(folder):
    races, presets, visuals = {}, {}, {}
    files = sorted(glob.glob(os.path.join(folder, "*.tbl")), key=lambda p: os.path.getsize(p))
    for path in files:
        _, rows = read_tbl(path)
        if not rows:
            continue
        keys = set(rows[0])
        for r in rows:
            if "RaceName" in keys or "RaceName" in r:
                races.setdefault(r["UUID"], {}).update(r)
            elif "VOLinesTableUUID" in r:
                presets.setdefault(r["UUID"], {}).update(r)
            elif "VisualResource" in r:
                visuals.setdefault(r["UUID"], {}).update(r)

    out = {}
    bases = {"Humain": "0eb594cb", "Elfe": "6c038dcb", "Drow": "4f5d1434", "DemiElfe": "45f4ac10",
             "Nain": "0ab2874d", "Halfelin": "78cd3bcc", "Gnome": "f1b3f884", "Tieffelin": "b6dccbed",
             "Githyanki": "bdf9b779", "Drakeide": "9c61a74a", "DemiOrque": "5c39a726"}
    zero = "00000000-0000-0000-0000-000000000000"

    def split(v):
        return [x for x in (v or "").split(";") if x]

    for bnom, prefix in bases.items():
        race = next(u for u in races if u.startswith(prefix))
        base = races[race]
        subs = [u for u, r in races.items() if r.get("ParentUUID") == race and r.get("ProgressionTableUUID")]
        for sub in (subs or [None]):
            src = races[sub] if sub else base
            nom = f"{bnom}_{src['RaceName']}" if sub else bnom
            lists = {}
            for k in LISTS:
                vals = split(src.get(k)) if sub else []
                if not vals:
                    vals = split(base.get(k))
                if not vals and k == "SkinColors":
                    vals = split(races[HUMANOID].get("SkinColors"))
                if vals:
                    lists[k] = vals
            ps = [p for p in presets.values() if p.get("RaceUUID") == race and p.get("SubRaceUUID", zero) == (sub or zero)]
            if not ps:
                ps = [p for p in presets.values() if p.get("RaceUUID") == race and p.get("SubRaceUUID", zero) == zero]
            if not ps:
                ps = [p for p in presets.values() if p.get("RaceUUID") == race]
            corps = {}
            for p in ps:
                corps.setdefault((p["BodyType"], p.get("BodyShape", "0")), {k: p[k] for k in (
                    "BodyType", "BodyShape", "RootTemplate", "CloseUpA", "CloseUpB", "Overview", "VOLinesTableUUID")
                    if k in p})
            own = [v for v in visuals.values() if sub and v.get("RaceUUID") == sub]
            own_slots = {v["SlotName"] for v in own}
            vis = own + [v for v in visuals.values() if v.get("RaceUUID") == race and v["SlotName"] not in own_slots]
            vis = [{k: v[k] for k in ("UUID", "SlotName", "VisualResource", "DisplayName", "BodyType", "BodyShape",
                                      "DefaultSkinColor", "IconIdOverride", "RootTemplate") if k in v} for v in vis]
            out[nom] = {"race": race, "sous_race": sub, "nom_jeu": src.get("DisplayName"),
                        "RaceEquipment": src.get("RaceEquipment") or base.get("RaceEquipment"),
                        "RaceSoundSwitch": src.get("RaceSoundSwitch") or base.get("RaceSoundSwitch"),
                        "listes": lists, "corps": list(corps.values()), "visuels": vis}
            print(f"{nom:28s} corps={len(corps)} visuels={len(vis)} peaux={len(lists.get('SkinColors', []))}")
    dest = os.path.join(os.path.dirname(__file__), "donnees_jeu.json")
    json.dump(out, open(dest, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("écrit :", dest)


if __name__ == "__main__":
    main(sys.argv[1])
