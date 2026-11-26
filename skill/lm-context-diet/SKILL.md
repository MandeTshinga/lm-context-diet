---
name: lm-context-diet
description: >
  Slim a bloated context file (CLAUDE.md, AGENTS.md, .cursorrules) without
  silently losing a behavioural rule. Measures size and token cost, sorts each
  section by whether it carries an imperative or only history, moves the rest
  into per-element README files, and proves with a before/after count that no
  rule disappeared. Use when the CLAUDE.md is too big or costs too many tokens,
  "slim CLAUDE.md", "context file too big", "split AGENTS.md", "too many tokens
  per session", "context budget", "dégraisser le CLAUDE.md", "alléger le
  contexte", or to audit whether documented rules still actually apply.
---

# lm-context-diet: slim a context file without losing a rule

## The failure mode, and why this skill exists

A context file is loaded **in full at the start of every conversation**. It grows by accretion: every incident adds a line, every component adds a paragraph, nobody ever deletes anything. After a year it costs tens of thousands of tokens per session.

The obvious fix is to move content into README files. The fix is right. The danger is elsewhere.

**When a behavioural rule vanishes during the move, nothing breaks.** No error, no failing test, no warning. The rule simply stops applying, and you find out weeks later when the model makes the wrong call, with no way to connect cause and effect.

That is what happened on the real case that produced this skill. Four rules disappeared across the extractions. All four were recovered, but only because a counter was running at every step.

## The sorting criterion

**A line stays in the context file if it carries a behavioural imperative. Otherwise it moves to a README.**

Imperative markers: `must`, `always`, `never`, `before you`, `by default`, `required`, `do not`, `in case of conflict`, and their French equivalents (`obligatoire`, `toujours`, `jamais`, `doit`, `ne pas`...).

The criterion is not accurate, and that is not what it is asked for. It is asked to be **countable**. A criterion you can count before and after an extraction turns an intuition into a test. A false positive costs one reread line. A false negative costs a rule. When in doubt, widen the marker list rather than narrow it.

## What stays, what moves

| Stays in the context file | Moves to a README |
|---|---|
| Orchestration rules: which tool, when, in what order | History: why it was built, in what order, with what feedback |
| Arbitration: which source wins in a conflict | Catalogues: the list of what exists and what it does |
| Hard technical constraints: what breaks if it moves | Gotchas specific to **a single** element |
| Defaults: what applies without being asked | Dated logs, release notes, changelog |
| Security and privacy reflexes | Implementation details, APIs, parameters |

A successful cleanup **does not shrink evenly**. It empties the catalogue sections and leaves the rule sections intact, sometimes denser. On the reference case the file lost 76.5 % while the "Absolute rules" section grew 7.6 % and "Security" grew 31.1 %. If all your sections shrink at the same rate, you are losing rules.

## Procedure

The script is `lm-context-diet.py`, in the root of the repository. Adjust the path to wherever you put it.

### 1. Measure

```bash
python lm-context-diet.py measure CLAUDE.md
```

Returns size, line count, a token estimate and, section by section, **the weight divided by the number of rules the section carries**.

**Never attack by weight alone.** A big section can be perfectly legitimate. The signal is the last column, in bytes per imperative line:

```
                                             size   rules     B/rule
Components                                80.8 KB      63       1313
Skills                                    39.9 KB      18       2268
Version journal                           10.4 KB       2       5320  <-- a story
```

A few hundred bytes per rule: the section is dense and earns its place. Several thousand: it is a story with a rule buried in it, and that is what to extract first. The script flags anything above 3,000 bytes per rule, and any section over 4 KB carrying none.

The ratio is an **indicator, not a verdict**. A navigation section (directory tree, index) will always score badly and may legitimately stay.

### 2. Take a baseline

```bash
python lm-context-diet.py baseline CLAUDE.md -o .ctx-baseline.json
```

### 3. Extract ONE section, and only one

Create or extend the README of the element concerned, move the history and details there, and leave in the context file an index line that respects the retrieval constraint below.

⚠️ **Move the rule sentence verbatim. Never reword it in the same pass.**

This is the least intuitive constraint of the procedure, and it demonstrates itself in one command. On the example set, an extraction where the rules were reworded while being moved reports **9 disappeared and 9 new**, which carries no usable information. The same extraction with the rule sentences copied verbatim reports **5 disappeared**, each classifiable in seconds.

Every rule survived in both cases. In the first one, the check could no longer prove it.

Practical corollary: you can **trim the tail** of a line without breaking its fingerprint, since only the first 60 alphanumeric characters are read. A line that opens with the rule and closes with an anecdote cuts cleanly. A line that opens with the anecdote and closes with the rule will show as disappeared, and you will have to confirm by hand that the rule reappeared elsewhere.

If a rule needs rewording, make it a **separate pass** with its own baseline.

### 4. Recount immediately

```bash
python lm-context-diet.py check CLAUDE.md .ctx-baseline.json
```

Exits with code 1 when a fingerprint disappeared, and names each one. For every listed line, decide: history that legitimately moved, or a rule to restore.

### 5. Loop

Take a new baseline, move on to the next section. When everything is extracted, check the links:

```bash
python lm-context-diet.py links CLAUDE.md
```

A dead index link makes the README unreachable, so the rule goes silent. Same failure, different path.

## ⚠️ Granularity is the critical point

**One section at a time. Never a batch.**

Measured on the reference case, with the same tool:

| Scope of the check | Disappeared lines to arbitrate | Usable? |
|---|---|---|
| One section | 3 | Yes, one minute of reading |
| One commit covering two sections | 78 | No |
| The entire cleanup at once | 120 | No |

At 120 disappearances, the one real lost rule is buried under 119 legitimate moves and nobody will see it. The script warns past 12: when that fires, it is not a result, it is the signal to re-baseline and cut finer.

## ⚠️ The retrieval constraint

This is the part everyone gets wrong.

**A README is not loaded automatically.** It is reached because a link in the context file makes it visible at the right moment. What decides is not the link, it is **the text around the link**.

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

## Check that the script really detects

Before trusting the tool on a repository, prove it on its own history:

```bash
git show <commit-before>:CLAUDE.md > /tmp/before.md
python lm-context-diet.py baseline /tmp/before.md -o /tmp/b.json
python lm-context-diet.py check CLAUDE.md /tmp/b.json
```

If the listed lines look like what was really moved, the tool is calibrated for this repository. Otherwise, adjust the `MARKERS` list.

## Lessons learned

**A rule can survive elsewhere and still stop applying.** The loss caught on the reference case (81 to 78 imperative lines after extracting one block) was the obligation to create database records through the framework's native classes rather than raw SQL. The knowledge still existed, in a gotchas file. But it was no longer on the automatic loading path, so it no longer fired. **Checking whether the text still exists somewhere proves nothing.** The only question is whether it is still reached.

**A heavily reworded line shows as both "disappeared" and "new".** The fingerprint keeps only 60 alphanumeric characters; a translation or deep rewrite changes it. That is a false positive, so the error goes the right way: you reread one line for nothing. Do not make the fingerprint more tolerant, it would destroy the detection of real deletions.

**Windows console output.** The script forces UTF-8 on `stdout`, otherwise the first accented character raises `UnicodeEncodeError` in cp1252. If you rewrite it, keep that guard.

## Limits

The percentages in this document come from **one repository**, whose context file had grown abnormally (222 KB). A file that is already clean will not yield 76 %.

The token estimate assumes roughly 3.7 bytes per token, calibrated on accented French markdown. It is an order of magnitude to arbitrate with, never billing.

The sorting criterion is a **lexical filter**, not comprehension. It catches rules written with a verb of obligation. A rule phrased without a marker slips through, and no count will protect it.
