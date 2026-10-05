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
    vkeys = ("UUID", "SlotName", "VisualResource", "DisplayName", "BodyType", "BodyShape", "DefaultSkinColor",
             "IconIdOverride", "RootTemplate")
    pkeys = ("BodyType", "BodyShape", "RootTemplate", "CloseUpA", "CloseUpB", "Overview", "VOLinesTableUUID")

    def split(v):
        return [x for x in (v or "").split(";") if x]

    def lists_of(r, skin_fallback=False):
        out_l = {k: split(r.get(k)) for k in LISTS if split(r.get(k))}
        if skin_fallback and "SkinColors" not in out_l:
            out_l["SkinColors"] = split(races[HUMANOID].get("SkinColors"))
        return out_l

    def visuals_of(uuid):
        return [{k: v[k] for k in vkeys if k in v} for v in visuals.values() if v.get("RaceUUID") == uuid]

    def bodies(race, sub):
        seen = {}
        for p in presets.values():
            if p.get("RaceUUID") == race and p.get("SubRaceUUID", zero) == (sub or zero):
                seen.setdefault((p["BodyType"], p.get("BodyShape", "0")), {k: p[k] for k in pkeys if k in p})
        return list(seen.values())

    for bnom, prefix in bases.items():
        race = next(u for u in races if u.startswith(prefix))
        base = races[race]
        subs = [u for u, r in races.items() if r.get("ParentUUID") == race and r.get("ProgressionTableUUID")]
        has_subs = bool(subs)
        out[bnom] = {
            "race": race, "nom_jeu": base.get("DisplayName"), "RaceEquipment": base.get("RaceEquipment"),
            "RaceSoundSwitch": base.get("RaceSoundSwitch"),
            "listes": lists_of(base, skin_fallback=not has_subs or not any(split(races[s].get("SkinColors")) for s in subs)),
            "visuels": visuals_of(race), "corps": [] if has_subs else bodies(race, None),
            "sous_races": [{"uuid": s, "code": races[s]["RaceName"], "nom_jeu": races[s].get("DisplayName"),
                            "RaceEquipment": races[s].get("RaceEquipment"),
                            "RaceSoundSwitch": races[s].get("RaceSoundSwitch"),
                            "listes": lists_of(races[s]), "visuels": visuals_of(s), "corps": bodies(race, s)}
                           for s in subs]}
        print(f"{bnom:10s} visuels={len(out[bnom]['visuels'])} corps={len(out[bnom]['corps'])} sous-races=" +
              ", ".join(f"{x['code']}({len(x['corps'])} corps, {len(x['visuels'])} vis)" for x in out[bnom]["sous_races"]))
    dest = os.path.join(os.path.dirname(__file__), "donnees_jeu.json")
    json.dump(out, open(dest, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("écrit :", dest)


if __name__ == "__main__":
    main(sys.argv[1])
