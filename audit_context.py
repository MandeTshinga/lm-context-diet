#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_context.py — garde-fou pour degraisser un fichier de contexte
(CLAUDE.md, AGENTS.md, .cursorrules...) sans perdre de regle de comportement.

Le probleme qu'il resout : deplacer du contenu d'un fichier de contexte vers
des README ne casse rien quand ca se passe mal. Une regle disparue ne produit
aucune erreur, elle cesse simplement de s'appliquer. On ne s'en apercoit que
le jour ou le modele fait le mauvais choix.

La parade : compter les lignes portant un imperatif de comportement AVANT
chaque extraction, recompter APRES, et lister nommement ce qui a disparu.

    python audit_context.py measure  CLAUDE.md
    python audit_context.py baseline CLAUDE.md -o .ctx-baseline.json
    #   ... extraire UNE section vers un README ...
    python audit_context.py check    CLAUDE.md .ctx-baseline.json
    python audit_context.py links    CLAUDE.md

`check` sort en code retour 1 si une empreinte a disparu. C'est ce qui en
fait un test et non un rapport.

IMPORTANT : mesurer apres CHAQUE extraction, jamais une seule fois a la fin.
Sur le cas reel qui a produit cet outil, la comparaison globale entre l'etat
initial et l'etat final rendait 111 lignes disparues a examiner, dont la
quasi-totalite etaient des deplacements legitimes. Mesuree section par
section, la meme detection rendait 3 lignes, et les 3 se relisaient a la main.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

# --------------------------------------------------------------------------
# Sortie console : Windows ouvre stdout en cp1252 et leve UnicodeEncodeError
# sur le moindre accent. On force UTF-8 avant toute impression.
# --------------------------------------------------------------------------
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------
# Marqueurs d'imperatif de comportement, FR + EN.
#
# Le critere n'a pas besoin d'etre parfait, il a besoin d'etre COMPTABLE.
# Un faux positif coute une ligne relue. Un faux negatif coute une regle.
# En cas de doute, elargir la liste plutot que la restreindre.
# --------------------------------------------------------------------------
MARKERS = [
    # --- francais ---
    r"\bobligatoire",
    r"\btoujours\b",
    r"\bjamais\b",
    r"\bavant de\b",
    r"\bavant tout\b",
    r"en cas de conflit",
    r"\bpar d[ée]faut\b",
    r"\bne pas\b",
    r"\bdoit\b",
    r"\bdoivent\b",
    r"\bil faut\b",
    r"\binterdit",
    r"R[èe]gle",
    r"\bR[ée]flexe\b",
    r"\bPi[èe]ge\b",
    r"\bprime\b",
    # --- anglais ---
    r"\bmandatory\b",
    r"\bnever\b",
    r"\balways\b",
    r"\bmust\b",
    r"\bdo not\b",
    r"\bdon't\b",
    r"\brequired\b",
    r"\bbefore you\b",
    r"\bby default\b",
    r"\bRule\b",
]
RX = re.compile("|".join(MARKERS), re.I)

# Un lien markdown relatif : [texte](chemin) sans schema http(s):// ni ancre seule.
RX_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

# Estimation grossiere, calibree sur du markdown francais accentue.
# A retenir comme un ordre de grandeur, jamais comme une mesure.
BYTES_PER_TOKEN = 3.7


def read(path: str) -> str:
    return io.open(path, encoding="utf-8").read()


def fingerprint(line: str) -> str:
    """Empreinte stable d'une ligne : 60 premiers caracteres alphanumeriques.

    Insensible a la ponctuation, a la casse et aux accents. Une ligne
    reformulee superficiellement (gras deplace, virgule ajoutee) reste
    reconnue. Une ligne supprimee ressort. C'est exactement le compromis
    voulu : on cherche les disparitions, pas les retouches.
    """
    return re.sub(r"[^a-z0-9]", "", line.lower())[:60]


def imperatives(text: str) -> dict:
    """{empreinte: (numero de ligne, texte)} pour chaque ligne imperative."""
    out = {}
    for i, raw in enumerate(text.split("\n"), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if not RX.search(s):
            continue
        fp = fingerprint(s)
        if len(fp) > 20:  # sous ce seuil l'empreinte n'est plus discriminante
            out[fp] = (i, s)
    return out


def sections(text: str) -> list:
    """[(titre, octets)] par section de niveau ##, dans l'ordre du fichier."""
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith("## ")]
    out = []
    for k, i in enumerate(idx):
        end = idx[k + 1] if k + 1 < len(idx) else len(lines)
        out.append((lines[i][3:].strip(), len("\n".join(lines[i:end]))))
    return out


# --------------------------------------------------------------------------
# Sous-commandes
# --------------------------------------------------------------------------
def cmd_measure(args) -> int:
    text = read(args.file)
    size = len(text.encode("utf-8"))
    nlines = text.count("\n") + 1
    imps = imperatives(text)

    print("%s" % args.file)
    print("  %-22s %s octets" % ("poids", format(size, ",d").replace(",", " ")))
    print("  %-22s %d" % ("lignes", nlines))
    print("  %-22s ~%s (estimation)" % (
        "tokens",
        format(int(size / BYTES_PER_TOKEN), ",d").replace(",", " ")))
    print("  %-22s %d" % ("lignes imperatives", len(imps)))

    secs = sections(text)
    if secs:
        print("\n  Sections (## ), de la plus lourde a la plus legere :")
        for title, n in sorted(secs, key=lambda s: -s[1]):
            pct = 100.0 * n / size if size else 0
            bar = "#" * max(1, int(pct / 2))
            print("    %-44s %7.1f Ko  %5.1f%%  %s" % (title[:44], n / 1024.0, pct, bar))
    return 0


def cmd_baseline(args) -> int:
    imps = imperatives(read(args.file))
    payload = {
        "source": os.path.basename(args.file),
        "count": len(imps),
        "lines": {fp: txt for fp, (_, txt) in imps.items()},
    }
    io.open(args.out, "w", encoding="utf-8").write(
        json.dumps(payload, ensure_ascii=False, indent=1))
    print("baseline : %d lignes imperatives -> %s" % (len(imps), args.out))
    print("Extrayez UNE section, puis relancez `check`.")
    return 0


def cmd_check(args) -> int:
    base = json.loads(read(args.baseline))
    before = base["lines"]
    after = imperatives(read(args.file))

    lost = [fp for fp in before if fp not in after]
    gained = [fp for fp in after if fp not in before]

    print("avant %d  ->  apres %d" % (len(before), len(after)))
    print("disparues %d  |  nouvelles ou reformulees %d" % (len(lost), len(gained)))

    if len(lost) > 12:
        print()
        print("!! %d disparitions : trop pour etre relues une par une." % len(lost))
        print("   Ce n'est pas un resultat exploitable. Reposez une baseline")
        print("   et extrayez UNE SEULE section avant de recontroler.")

    if lost:
        print("\n--- disparues, a arbitrer une par une ---")
        for fp in lost:
            print("  %s" % before[fp][:150])
        print("\nPour chacune : soit c'est de l'historique parti legitimement")
        print("vers un README, soit c'est une regle a restaurer dans le fichier.")

    if gained and args.verbose:
        print("\n--- nouvelles ou reformulees ---")
        for fp in gained:
            print("  %s" % after[fp][1][:150])

    if not lost:
        print("\nOK : aucune ligne imperative perdue.")
        return 0
    return 1


def cmd_links(args) -> int:
    """Un lien d'index mort rend un README inatteignable, donc la regle muette."""
    text = read(args.file)
    root = os.path.dirname(os.path.abspath(args.file)) or "."
    dead = []
    for i, raw in enumerate(text.split("\n"), 1):
        for target in RX_LINK.findall(raw):
            t = target.split("#")[0].strip()
            if not t or "://" in t or t.startswith("mailto:"):
                continue
            if not os.path.exists(os.path.join(root, t)):
                dead.append((i, t))

    if not dead:
        print("OK : aucun lien relatif mort.")
        return 0
    print("%d lien(s) mort(s) :" % len(dead))
    for i, t in dead:
        print("  L%-5d %s" % (i, t))
    return 1


def main() -> int:
    p = argparse.ArgumentParser(
        description="Degraisser un fichier de contexte sans perdre de regle.")
    sub = p.add_subparsers(dest="cmd")

    m = sub.add_parser("measure", help="poids, lignes, tokens, poids par section")
    m.add_argument("file")
    m.set_defaults(func=cmd_measure)

    b = sub.add_parser("baseline", help="enregistrer les lignes imperatives")
    b.add_argument("file")
    b.add_argument("-o", "--out", default=".ctx-baseline.json")
    b.set_defaults(func=cmd_baseline)

    c = sub.add_parser("check", help="recompter et lister ce qui a disparu")
    c.add_argument("file")
    c.add_argument("baseline")
    c.add_argument("-v", "--verbose", action="store_true")
    c.set_defaults(func=cmd_check)

    l = sub.add_parser("links", help="liens markdown relatifs qui ne resolvent pas")
    l.add_argument("file")
    l.set_defaults(func=cmd_links)

    args = p.parse_args()
    if not getattr(args, "cmd", None):
        p.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
