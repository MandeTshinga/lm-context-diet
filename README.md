# lm-context-diet

**Shrink a bloated `CLAUDE.md` without silently losing behavioural rules.**

*[Version française plus bas](#version-française). Full article: [English](https://www.langagemachine.be/decryptage/en/silent-loss-trimming-claude-md-without-losing-rules) · [français](https://www.langagemachine.be/decryptage/perte-silencieuse-degraisser-claude-md-sans-perdre-de-regles).*

I cut my working repository's `CLAUDE.md` from 222,864 bytes to 52,392 bytes, a **76.5 % reduction**, worth roughly **46,000 tokens per conversation**.

Four rules disappeared in the process. Nothing broke. No error fired. I only recovered them because a counter was running at every step.

That counter is what this repository is about. It comes in two forms:

- **`lm-context-diet.py`**, a single Python file with no dependency (Python 3.8+);
- **a Claude Code skill**, in [`skill/lm-context-diet/`](skill/lm-context-diet/SKILL.md), that walks the model through the whole procedure.

---

## The failure mode

A context file is loaded in full at the start of every conversation. It grows by accretion: every incident adds a line, every component adds a paragraph of history, nobody ever deletes anything.

The obvious fix is to move content into per-element README files. The fix is right. The danger is elsewhere.

**When a behavioural rule vanishes during the move, nothing breaks.** No error, no failing test, no warning. The rule simply stops applying, and you find out weeks later when the model makes a call you would have rejected, with no way to trace it back to the line you moved on a Tuesday evening.

Compare with code. Delete a function that is used elsewhere and the application crashes within seconds. A rule has none of those mechanisms.

## The sorting criterion

**A line stays in the context file if it carries a behavioural imperative. Otherwise it moves to a README.**

Markers: `must`, `always`, `never`, `before you`, `by default`, `required`, `do not`, and their French equivalents.

This criterion is not accurate. It catches lines that could have left and misses some that should have stayed. That is not what it is for.

It is for being **countable**. Count the imperative lines before an extraction, count again after, and if the number drops you know exactly what to go and re-read. An imperfect but measurable criterion beats a subtle but unverifiable judgement, because the second one does not survive the fourth section at three in the morning.

The fingerprint is one line:

```python
fingerprint = re.sub(r'[^a-z0-9]', '', line.lower())[:60]
```

Only the first sixty alphanumeric characters survive. Punctuation, case and accents are dropped. A line whose bold markers moved is still recognised. A deleted line stands out. That is exactly the trade you want, because you are hunting for disappearances and not for edits.

## Usage

```bash
python lm-context-diet.py measure  CLAUDE.md
python lm-context-diet.py baseline CLAUDE.md -o .ctx-baseline.json
#   ... move ONE section into a README ...
python lm-context-diet.py check    CLAUDE.md .ctx-baseline.json
python lm-context-diet.py links    CLAUDE.md
```

| Command | What it does |
|---|---|
| `measure` | Bytes, lines, estimated tokens, and every `##` section's weight **per rule it carries** |
| `baseline` | Records the fingerprint of every imperative line |
| `check` | Recounts and **names** the fingerprints that disappeared. Exits 1 on loss |
| `links` | Flags relative markdown links that no longer resolve |

`check` exiting non-zero is what makes it a test rather than a report.

### Use it as a Claude Code skill

Copy the `skill/lm-context-diet/` folder into `~/.claude/skills/` (all projects) or `.claude/skills/` (one project), and put `lm-context-diet.py` where the skill can run it. Then ask Claude Code to "slim my CLAUDE.md" or type `/lm-context-diet`. The skill applies the procedure below, one section at a time, and runs the check after each extraction.

### Don't sort by weight. Sort by bytes per rule.

A big section can be perfectly legitimate. The signal is the last column of `measure`:

```
                                           size   rules     B/rule
Components                               80.8 KB      63       1313
Skills                                   39.9 KB      18       2268
Version journal                          10.4 KB       2       5320  <-- a story
```

A few hundred bytes per rule means the section is dense and earns its place. Several thousand means it is a story with a rule buried in it, and that is what to extract first. The script flags anything above 3,000 bytes per rule, and any section over 4 KB carrying none at all.

After extraction, the same sections read very differently:

| Section | Before | After | |
|---|---|---|---|
| Components | 1,313 B/rule | 612 | 2.1× denser |
| Skills | 2,268 B/rule | 461 | 4.9× denser |
| MCP servers | 1,510 B/rule | 483 | 3.1× denser |
| Version journal | 5,320 B/rule | 878 | 6.1× denser |

The file did not merely shrink. Every remaining kilobyte carries three to five times more rules than before.

Treat the ratio as an indicator, not a verdict. A navigational section such as a directory tree will always score badly and may legitimately stay.

## ⚠️ Granularity is the whole game

**One section at a time. Never a batch.**

Measured with this exact tool, on the real commits of my own cleanup:

| Scope of the check | Disappeared lines to arbitrate | Usable? |
|---|---|---|
| One section | 3 | Yes, one minute of reading |
| One commit covering two sections | 78 | No |
| The entire cleanup at once | 120 | No |

At 120 disappearances, the one real lost rule is buried under 119 legitimate moves and nobody will ever see it. The script warns past 12: when that warning fires, it is not a result, it is a signal to re-baseline and cut finer.

## ⚠️ Move the rule verbatim, never reword it in the same pass

The least intuitive constraint of the procedure, and it demonstrates itself in one command.

On the example set in `examples/`, an extraction where the rules were reworded while being moved reports **9 disappeared and 9 new**, which carries no usable information. The same extraction with the rule sentences copied verbatim reports **5 disappeared**, each classifiable in seconds.

Every rule survived in both cases. In the first one the check could no longer prove it.

Practical corollary: you can **trim the tail** of a line without breaking its fingerprint, since only the first sixty alphanumeric characters are read. A line that opens with the rule and closes with an anecdote cuts cleanly. A line that opens with the anecdote and closes with the rule will show as disappeared, and you will have to confirm by hand that the rule reappeared elsewhere.

If a rule needs rewording, make it a **separate pass** with its own baseline.

## ⚠️ The retrieval constraint

This is the part everyone gets wrong.

**A README is not loaded automatically.** It is reached because a link makes it visible at the right moment. And what triggers the read is not the link. It is the text around the link.

Unreachable in practice:

```markdown
See [`MCP/README.md`](MCP/README.md) for details.
```

Nothing says when to open that file. It will only be opened by someone already looking for MCP details, which is never the moment the rule matters.

Reachable:

```markdown
**📖 Mandatory call order, publishing rule, routing pitfalls:**
[`MCP/README.md`](MCP/README.md)
```

The index line must announce **what the rule is about**, not merely where it lives. It works as a table of contents that triggers a read, not as a footnote.

Corollary: if a rule is too important to depend on that trigger, it does not move. It stays in the context file, in full.

## What the counter actually caught

After extracting the MCP block, the count went from 81 to 78. One of the three missing lines should never have left:

> **Always use the native Joomla `Table\Category`, `Table\Content` and `Table\Menu` classes through a CLI script. Never raw SQL** to create menus, categories or articles.

Joomla's `#__menu` table is a nested set. Its `lft` and `rgt` bounds must be recomputed on every insert, and a direct `INSERT` does not recompute them. The menu corrupts with no SQL error, and the symptom shows up later, elsewhere, unrecognisable.

The detail that gives the check all its value: **the rule still existed**, in a gotchas file at the other end of the repository, perfectly written. It was simply no longer on the automatic loading path, so it no longer fired.

**Checking whether the text still exists somewhere proves nothing. The only question is whether it is still reached.**

## What a successful cleanup looks like

It does not shrink uniformly. On my repository, while the file lost 76.5 %:

| Section | Before | After | Δ |
|---|---|---|---|
| Components | 80.8 KB | 19.1 KB | −76.3 % |
| Skills | 39.9 KB | 5.4 KB | −86.4 % |
| Tools | 45.0 KB | 2.8 KB | −93.8 % |
| MCP servers | 17.7 KB | 4.7 KB | −73.3 % |
| Version journal | 10.4 KB | 1.7 KB | −83.5 % |
| **Absolute rules** | 6.3 KB | **6.7 KB** | **+7.6 %** |
| **Security** | 1.3 KB | **1.7 KB** | **+31.1 %** |

The last two grew, because that is where the recovered rules went back.

**If all your sections shrink at the same rate, you are losing rules.**

## Limits

These percentages come from **one repository**, whose context file had grown abnormally over more than a year. A file that is already clean will not yield 76 %.

The token estimate assumes roughly 3.7 bytes per token, calibrated on accented French markdown. Treat it as an order of magnitude, never as billing.

The criterion is a **lexical filter**, not comprehension. It catches rules written with a verb of obligation. A rule phrased without a marker slips through, and no counting protects it. Which is one more reason to write rules with explicit obligation verbs, making them clearer for humans too.

---

## Contents

```
lm-context-diet.py          the tool
skill/lm-context-diet/      the Claude Code skill (SKILL.md)
examples/
  CLAUDE.before.md          a generic bloated context file (7.2 KB, 14 imperative lines)
  CLAUDE.after.md           the same file, correctly extracted
  CLAUDE.after-broken.md    the same extraction, with one rule accidentally dropped
  docs/                     the README files produced by the extraction
ARTICLE-fr.md               the long-form French version of this text
tests/                      unit tests run against the examples (python -m unittest discover tests)
CONTRIBUTING.md             how to report, discuss and propose changes
```

### Run the demo

```bash
python lm-context-diet.py measure  examples/CLAUDE.before.md
python lm-context-diet.py baseline examples/CLAUDE.before.md -o demo.json

python lm-context-diet.py check    examples/CLAUDE.after.md        demo.json
#   → before 14 -> after 13, disappeared 5: all legitimate history.
#     Read them, classify them, move on.

python lm-context-diet.py check    examples/CLAUDE.after-broken.md demo.json
#   → before 14 -> after 12, disappeared 6, exit code 1.
#     The extra one is the webhook signature rule.
#     That is the failure this tool exists to catch.
```

The `-broken` file is what a normal, careful extraction looks like when one rule slips through. Nothing about it is obviously wrong on reading. That is the whole point.

---

## Version française

**Dégraisser un `CLAUDE.md` trop lourd sans perdre de règle en silence.**

J'ai réduit le `CLAUDE.md` de mon dépôt de travail de 222 864 à 52 392 octets, soit **76,5 % de moins** et environ **46 000 tokens économisés à chaque conversation**. Quatre règles ont disparu en route, sans la moindre erreur. Je ne les ai récupérées que parce qu'un compteur tournait à chaque étape. Ce dépôt contient ce compteur, sous deux formes : le script `lm-context-diet.py` (un seul fichier Python, sans dépendance) et un skill Claude Code dans [`skill/lm-context-diet/`](skill/lm-context-diet/SKILL.md).

L'outil et sa documentation sont en anglais. L'article complet en français : [La perte silencieuse : dégraisser un CLAUDE.md sans perdre de règles](https://www.langagemachine.be/decryptage/perte-silencieuse-degraisser-claude-md-sans-perdre-de-regles) (également dans [`ARTICLE-fr.md`](ARTICLE-fr.md)).

### Le principe en cinq points

1. **Une ligne reste dans le fichier de contexte si elle porte un impératif** (`toujours`, `jamais`, `obligatoire`, `doit`, `ne pas`, et leurs équivalents anglais). Sinon, elle part vers un README. Le critère n'est pas parfait : il est **comptable**, et c'est ce qui compte.
2. **On compte avant, on recompte après.** `baseline` enregistre l'empreinte de chaque ligne impérative ; `check` liste nommément celles qui ont disparu et sort en code 1.
3. **Une section à la fois, jamais un lot.** Une section rend 3 lignes à relire ; tout le dégraissage d'un coup en rend 120, où la vraie règle perdue est noyée.
4. **On déplace la phrase de règle telle quelle**, sans la reformuler dans la même passe, sinon le contrôle ne peut plus rien prouver.
5. **Un README n'est atteint que si la ligne d'index annonce de quoi parle la règle.** « Voir MCP/README.md » ne sera jamais ouvert au bon moment ; « Ordre d'appel obligatoire, règle de publication : MCP/README.md » le sera.

### Utilisation

```bash
python lm-context-diet.py measure  CLAUDE.md
python lm-context-diet.py baseline CLAUDE.md -o .ctx-baseline.json
#   ... déplacer UNE section vers un README ...
python lm-context-diet.py check    CLAUDE.md .ctx-baseline.json
python lm-context-diet.py links    CLAUDE.md
```

Dans la sortie de `measure`, la dernière colonne (`B/rule`, octets par règle) est le signal : quelques centaines, la section est dense et se défend ; plusieurs milliers, c'est une histoire avec une règle dedans, à sortir en premier.

Pour le skill : copier le dossier `skill/lm-context-diet/` dans `~/.claude/skills/` (tous les projets) ou `.claude/skills/` (un projet), puis demander à Claude Code de « dégraisser mon CLAUDE.md » ou taper `/lm-context-diet`.

La démo des exemples (`examples/`) montre en une commande le contrôle attraper une règle perdue : voir « Run the demo » plus haut.

## Feedback, stars and contributions

- **Found it useful?** A star helps others find it: [★ Star the repository](https://github.com/MandeTshinga/lm-context-diet).
- **Questions, results, ideas:** start a [discussion](https://github.com/MandeTshinga/lm-context-diet/discussions). Bugs go in an [issue](https://github.com/MandeTshinga/lm-context-diet/issues).
- **Want to change something?** Read [CONTRIBUTING.md](CONTRIBUTING.md), then open a pull request. The tests run with `python -m unittest discover tests`.
- **Share it:** the full article is [in English](https://www.langagemachine.be/decryptage/en/silent-loss-trimming-claude-md-without-losing-rules) and [in French](https://www.langagemachine.be/decryptage/perte-silencieuse-degraisser-claude-md-sans-perdre-de-regles).

## Retours, étoiles et contributions

- **Utile ?** Une étoile aide d'autres à le trouver : [★ Mettre une étoile au dépôt](https://github.com/MandeTshinga/lm-context-diet).
- **Questions, résultats, idées :** ouvrez une [discussion](https://github.com/MandeTshinga/lm-context-diet/discussions). Les bogues vont dans une [issue](https://github.com/MandeTshinga/lm-context-diet/issues).
- **Une modification ?** Lisez [CONTRIBUTING.md](CONTRIBUTING.md) (en anglais), puis ouvrez une pull request. Les tests se lancent avec `python -m unittest discover tests`.
- **Partager :** l'article complet est [en français](https://www.langagemachine.be/decryptage/perte-silencieuse-degraisser-claude-md-sans-perdre-de-regles) et [en anglais](https://www.langagemachine.be/decryptage/en/silent-loss-trimming-claude-md-without-losing-rules).

## License

MIT. See [LICENSE](LICENSE).
