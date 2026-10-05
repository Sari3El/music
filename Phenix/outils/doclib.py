"""Briques de base du générateur : identifiants stables, textes traduits,
entrées de stats et écriture des fichiers .lsx / .txt / .loca.xml.

Tous les UUID et toutes les clés de traduction sont dérivés du nom interne
de l'objet (uuid5). Relancer le générateur redonne donc exactement les mêmes
identifiants : les sauvegardes des joueurs restent compatibles d'une version
à l'autre, tant qu'on ne renomme pas un objet.
"""
import uuid
from xml.sax.saxutils import escape, quoteattr

NAMESPACE = uuid.UUID("f3276bfe-7396-5e79-a2f1-1f8fda3053a3")  # propre au mod Phénix
LSX_VERSION = '<version major="4" minor="0" revision="9" build="331"/>'


def U(key):
    """UUID stable pour une clé."""
    return str(uuid.uuid5(NAMESPACE, key))


def H(key):
    """Clé de traduction (handle) stable : h + 32 hexa séparés par des g."""
    x = uuid.uuid5(NAMESPACE, "loca:" + key).hex
    return f"h{x[:8]}g{x[8:12]}g{x[12:16]}g{x[16:20]}g{x[20:]}"


class Loca:
    """Textes du mod, indexés par handle. Une seule langue source (français)."""

    def __init__(self):
        self.texts = {}

    def add(self, key, text):
        h = H(key)
        old = self.texts.get(h)
        if old is not None and old != text:
            raise ValueError(f"Texte différent pour la même clé {key!r}")
        self.texts[h] = text
        return h

    def ref(self, key, text):
        """Handle au format des fichiers de stats : 'hxxxx;1'."""
        return self.add(key, text) + ";1"

    def xml(self):
        lines = ['<?xml version="1.0" encoding="utf-8"?>', "<contentList>"]
        for h, t in self.texts.items():
            lines.append(f'\t<content contentuid="{h}" version="1">{escape(t)}</content>')
        lines.append("</contentList>")
        return "\n".join(lines) + "\n"


class Entry:
    """Une entrée de stats (sort, passif, statut, réaction...)."""

    def __init__(self, name, typ, using=None, **data):
        self.name = name
        self.type = typ
        self.using = using
        self.data = {}
        for k, v in data.items():
            if v is not None:
                self.data[k] = str(v)

    def set(self, **data):
        for k, v in data.items():
            if v is not None:
                self.data[k] = str(v)
        return self

    def text(self):
        out = [f'new entry "{self.name}"', f'type "{self.type}"']
        # SpellType / StatusType doivent précéder "using", comme dans les fichiers du jeu
        lead = [k for k in ("SpellType", "StatusType") if k in self.data]
        for k in lead:
            out.append(f'data "{k}" "{self.data[k]}"')
        if self.using:
            out.append(f'using "{self.using}"')
        for k, v in self.data.items():
            if k in lead:
                continue
            if '"' in v:
                raise ValueError(f"Guillemet interdit dans {self.name}.{k}")
            out.append(f'data "{k}" "{v}"')
        return "\n".join(out)


def stats_file(entries):
    return "\n\n".join(e.text() for e in entries) + "\n"


# ---------------------------------------------------------------- LSX
class Node:
    def __init__(self, node_id, attrs=None, children=None):
        self.id = node_id
        self.attrs = attrs or []  # (id, type, value) ou (id, "TranslatedString", handle)
        self.children = children or []

    def render(self, indent):
        pad = " " * indent
        out = [f'{pad}<node id="{self.id}">']
        for aid, atype, val in self.attrs:
            if atype == "TranslatedString":
                out.append(f'{pad}    <attribute id="{aid}" type="TranslatedString" handle="{val}" version="1"/>')
            else:
                out.append(f'{pad}    <attribute id="{aid}" type="{atype}" value={quoteattr(str(val))}/>')
        if self.children:
            out.append(f"{pad}    <children>")
            for c in self.children:
                out.extend(c.render(indent + 8))
            out.append(f"{pad}    </children>")
        out.append(f"{pad}</node>")
        return out


def lsx(region, nodes):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<save>", "    " + LSX_VERSION,
           f'    <region id="{region}">', '        <node id="root">', "            <children>"]
    for n in nodes:
        out.extend(n.render(16))
    out += ["            </children>", "        </node>", "    </region>", "</save>"]
    return "\n".join(out) + "\n"


def guid_list_node(container_id, item_id, guids):
    """<node id="SubClasses"><children><node id="SubClass" Object=.../>..."""
    return Node(container_id, children=[Node(item_id, [("Object", "guid", g)]) for g in guids])
