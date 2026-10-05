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

# apparence -> (race du jeu, sous-race dont on prend les corps / couleurs complémentaires)
APPARENCES = {
    "Humain": ("0eb594cb-8820-4be6-a58d-8be7a1a98fba", None),
    "Elfe": ("6c038dcb-7eb5-431d-84f8-cecfaf1c0c5a", "4fda6bce-0b91-4427-901f-690c2d091c47"),
    "Drow": ("4f5d1434-5175-4fa9-b7dc-ab24fba37929", "c5f8ebdd-f4a5-4d2d-9eab-4a8d1b1dd724"),
    "DemiElfe": ("45f4ac10-3c89-4fb2-b37d-f973bb9110c0", "30fafb0b-7c8b-4917-bd2a-536233b35d3c"),
    "Nain": ("0ab2874d-cfdc-405e-8a97-d37bfbb23c52", "78f5e3e8-a9f8-4249-8007-84dc922640b2"),
    "Halfelin": ("78cd3bcc-1c43-4a2a-aa80-c34322c16a04", "a8828cb9-589d-489e-8373-6495eb31ffc1"),
    "Gnome": ("f1b3f884-4029-4f0f-b158-1f9fe0ae5a0d", "2cf6c770-24ab-4608-9617-d1e46c11ab55"),
    "Tieffelin": ("b6dccbed-30f3-424b-a181-c4540cf38197", "3f30547c-248c-4781-b0e3-6ef2ab99426b"),
    "Githyanki": ("bdf9b779-002c-4077-b377-8ea7c1faa795", None),
    "Drakeide": ("9c61a74a-20df-4119-89c5-d996956b6c66", "61a2c59d"),  # préfixe : drakéide rouge
    "DemiOrque": ("5c39a726-71c8-4748-ba8d-f768b3c11a91", None),
}


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

    def find_race(prefix):
        return next(u for u in races if u.startswith(prefix))

    out = {}
    for nom, (race, sub) in APPARENCES.items():
        if sub:
            sub = find_race(sub)
        base = races[race]
        lists = {}
        for k in LISTS:
            vals = [v for v in (base.get(k) or "").split(";") if v]
            if not vals and k == "SkinColors" and race.startswith("9c61a74a"):
                for r in races.values():  # drakéides : couleurs de toutes les sous-races (rouge, bleu, or...)
                    if r.get("ParentUUID") == race:
                        vals += [v for v in (r.get("SkinColors") or "").split(";") if v and v not in vals]
            if not vals and sub:
                vals = [v for v in (races[sub].get(k) or "").split(";") if v]
            if not vals and k == "SkinColors":
                vals = [v for v in (races[HUMANOID].get("SkinColors") or "").split(";") if v]
            if vals:
                lists[k] = vals
        ps = [p for p in presets.values() if p.get("RaceUUID") == race and
              p.get("SubRaceUUID", "00000000-0000-0000-0000-000000000000") in (sub or "00000000-0000-0000-0000-000000000000",)]
        if not ps:
            ps = [p for p in presets.values() if p.get("RaceUUID") == race]
        corps = {}
        for p in ps:
            corps[(p["BodyType"], p.get("BodyShape", "0"))] = {k: p[k] for k in
                                                                ("BodyType", "BodyShape", "RootTemplate", "CloseUpA",
                                                                 "CloseUpB", "Overview", "VOLinesTableUUID") if k in p}
        vis = [{k: v[k] for k in ("UUID", "SlotName", "VisualResource", "DisplayName", "BodyType", "BodyShape",
                                  "DefaultSkinColor", "IconIdOverride", "RootTemplate") if k in v}
               for v in visuals.values() if v.get("RaceUUID") == race]
        out[nom] = {"race": race, "sous_race": sub, "RaceEquipment": base.get("RaceEquipment"),
                    "RaceSoundSwitch": base.get("RaceSoundSwitch"), "listes": lists,
                    "corps": list(corps.values()), "visuels": vis}
        print(f"{nom:10s} corps={len(corps)} visuels={len(vis)} listes={ {k: len(v) for k, v in lists.items()} }")
    dest = os.path.join(os.path.dirname(__file__), "donnees_jeu.json")
    json.dump(out, open(dest, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("écrit :", dest)


if __name__ == "__main__":
    main(sys.argv[1])
