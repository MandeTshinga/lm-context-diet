#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lm-context-diet.py: a safety net for slimming a context file
(CLAUDE.md, AGENTS.md, .cursorrules...) without losing behavioural rules.

The problem it solves: moving content out of a context file into README
files breaks nothing when it goes wrong. A rule that disappears raises no
error, it simply stops applying. You only notice the day the model makes
the wrong call.

The fix: count the lines that carry a behavioural imperative BEFORE each
extraction, count again AFTER, and name every line that disappeared.

    python lm-context-diet.py measure  CLAUDE.md
    python lm-context-diet.py baseline CLAUDE.md -o .ctx-baseline.json
    #   ... move ONE section into a README ...
    python lm-context-diet.py check    CLAUDE.md .ctx-baseline.json
    python lm-context-diet.py links    CLAUDE.md

`check` exits with code 1 when a fingerprint has disappeared. That is what
makes it a test rather than a report.

IMPORTANT: measure after EVERY extraction, never once at the end. On the
real case that produced this tool, comparing the initial and final states
in one go returned 111 disappeared lines to review, almost all of them
legitimate moves. Measured section by section, the same detection returned
3 lines, and all 3 could be reread by hand.

Part of the Langagemachine tools (LM). MIT licence.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

# --------------------------------------------------------------------------
# Console output: Windows opens stdout in cp1252 and raises
# UnicodeEncodeError on the first accented character. Force UTF-8 before
# printing anything.
# --------------------------------------------------------------------------
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------
# Behavioural imperative markers, English + French.
#
# The criterion does not need to be perfect, it needs to be COUNTABLE.
# A false positive costs one reread line. A false negative costs a rule.
# When in doubt, widen the list rather than narrow it.
# --------------------------------------------------------------------------
MARKERS = [
    # --- French ---
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
    # --- English ---
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

# A relative markdown link: [text](path) without an http(s):// scheme.
RX_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

# Rough estimate, calibrated on accented French markdown.
# Read it as an order of magnitude, never as a measurement.
BYTES_PER_TOKEN = 3.7


def read(path: str) -> str:
    return io.open(path, encoding="utf-8").read()


def fingerprint(line: str) -> str:
    """Stable fingerprint of a line: its first 60 alphanumeric characters.

    Ignores punctuation, case and accents. A line that was only lightly
    edited (bold moved, comma added) is still recognised. A deleted line
    stands out. That is exactly the trade we want: we are hunting for
    disappearances, not for edits.
    """
    return re.sub(r"[^a-z0-9]", "", line.lower())[:60]


def imperatives(text: str) -> dict:
    """{fingerprint: (line number, text)} for every imperative line."""
    out = {}
    for i, raw in enumerate(text.split("\n"), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        if not RX.search(s):
            continue
        fp = fingerprint(s)
        if len(fp) > 20:  # below this length a fingerprint stops discriminating
            out[fp] = (i, s)
    return out


def sections(text: str) -> list:
    """[(title, bytes, imperative count)] per ## section, in file order.

    Bytes per imperative is the real signal: a section dense in rules
    earns its place, a heavy section that carries none is a story.
    """
    lines = text.split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith("## ")]
    out = []
    for k, i in enumerate(idx):
        end = idx[k + 1] if k + 1 < len(idx) else len(lines)
        chunk = "\n".join(lines[i:end])
        out.append((lines[i][3:].strip(), len(chunk), len(imperatives(chunk))))
    return out


def thousands(n: int) -> str:
    return format(n, ",d")


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------
def cmd_measure(args) -> int:
    text = read(args.file)
    size = len(text.encode("utf-8"))
    nlines = text.count("\n") + 1
    imps = imperatives(text)

    print("%s" % args.file)
    print("  %-22s %s bytes" % ("size", thousands(size)))
    print("  %-22s %d" % ("lines", nlines))
    print("  %-22s ~%s (estimate)" % ("tokens", thousands(int(size / BYTES_PER_TOKEN))))
    print("  %-22s %d" % ("imperative lines", len(imps)))

    secs = sections(text)
    if secs:
        print("\n  Sections, heaviest first.")
        print("  The last column is the signal: bytes per imperative line.")
        print("  %-38s %8s %7s %10s" % ("", "size", "rules", "B/rule"))
        worst = []
        for title, n, imp in sorted(secs, key=lambda s: -s[1]):
            ratio = (n / imp) if imp else None
            flag = ""
            if ratio is None and n > 4096:
                flag = "  <-- no rule"
                worst.append(title)
            elif ratio is not None and ratio > 3000:
                flag = "  <-- a story"
                worst.append(title)
            print("  %-38s %6.1f KB %7s %10s%s" % (
                title[:38], n / 1024.0, imp,
                ("%d" % ratio) if ratio else "-", flag))
        if worst:
            print("\n  Extract first: " + ", ".join(worst[:4]))
            print("  A heavy section with no rule is history or a catalogue.")
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
    print("baseline: %d imperative lines -> %s" % (len(imps), args.out))
    print("Move ONE section, then run `check`.")
    return 0


def cmd_check(args) -> int:
    base = json.loads(read(args.baseline))
    before = base["lines"]
    after = imperatives(read(args.file))

    lost = [fp for fp in before if fp not in after]
    gained = [fp for fp in after if fp not in before]

    print("before %d  ->  after %d" % (len(before), len(after)))
    print("disappeared %d  |  new or reworded %d" % (len(lost), len(gained)))

    if len(lost) > 12:
        print()
        print("!! %d disappearances: too many to review one by one." % len(lost))
        print("   This is not a usable result. Take a new baseline")
        print("   and move ONE SINGLE section before checking again.")

    if lost:
        print("\n--- disappeared, decide on each one ---")
        for fp in lost:
            print("  %s" % before[fp][:150])
        print("\nFor each: either it is history that legitimately moved")
        print("to a README, or it is a rule to restore in the file.")

    if gained and args.verbose:
        print("\n--- new or reworded ---")
        for fp in gained:
            print("  %s" % after[fp][1][:150])

    if not lost:
        print("\nOK: no imperative line lost.")
        return 0
    return 1


def cmd_links(args) -> int:
    """A dead index link makes a README unreachable, so the rule goes silent.

    Fenced code blocks (```) are skipped: a file that documents the right
    and the wrong way to write an index line contains illustrative links
    that have no reason to resolve.
    """
    text = read(args.file)
    root = os.path.dirname(os.path.abspath(args.file)) or "."
    dead = []
    in_fence = False
    for i, raw in enumerate(text.split("\n"), 1):
        if raw.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for target in RX_LINK.findall(raw):
            t = target.split("#")[0].strip()
            if not t or "://" in t or t.startswith("mailto:"):
                continue
            if not os.path.exists(os.path.join(root, t)):
                dead.append((i, t))

    if not dead:
        print("OK: no dead relative link.")
        return 0
    print("%d dead link(s):" % len(dead))
    for i, t in dead:
        print("  L%-5d %s" % (i, t))
    return 1


def main() -> int:
    p = argparse.ArgumentParser(
        prog="lm-context-diet",
        description="Slim a context file without losing a rule.")
    sub = p.add_subparsers(dest="cmd")

    m = sub.add_parser("measure", help="size, lines, tokens, weight per section")
    m.add_argument("file")
    m.set_defaults(func=cmd_measure)

    b = sub.add_parser("baseline", help="record the imperative lines")
    b.add_argument("file")
    b.add_argument("-o", "--out", default=".ctx-baseline.json")
    b.set_defaults(func=cmd_baseline)

    c = sub.add_parser("check", help="recount and list what disappeared")
    c.add_argument("file")
    c.add_argument("baseline")
    c.add_argument("-v", "--verbose", action="store_true")
    c.set_defaults(func=cmd_check)

    l = sub.add_parser("links", help="relative markdown links that do not resolve")
    l.add_argument("file")
    l.set_defaults(func=cmd_links)

    args = p.parse_args()
    if not getattr(args, "cmd", None):
        p.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
