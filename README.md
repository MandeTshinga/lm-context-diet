# Context Diet

**Shrink a bloated `CLAUDE.md` without silently losing behavioural rules.**

I cut my working repository's `CLAUDE.md` from 222,864 bytes to 52,392 bytes, a **76.5 % reduction**, worth roughly **46,000 tokens per conversation**.

Four rules disappeared in the process. Nothing broke. No error fired. I only recovered them because a counter was running at every step.

That counter is what this repository is about.

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
python audit_context.py measure  CLAUDE.md
python audit_context.py baseline CLAUDE.md -o .ctx-baseline.json
#   ... move ONE section into a README ...
python audit_context.py check    CLAUDE.md .ctx-baseline.json
python audit_context.py links    CLAUDE.md
```

| Command | What it does |
|---|---|
| `measure` | Bytes, lines, estimated tokens, and the weight of every `##` section |
| `baseline` | Records the fingerprint of every imperative line |
| `check` | Recounts and **names** the fingerprints that disappeared. Exits 1 on loss |
| `links` | Flags relative markdown links that no longer resolve |

`check` exiting non-zero is what makes it a test rather than a report.

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
audit_context.py            the tool
examples/
  CLAUDE.before.md          a generic bloated context file (7.2 KB, 14 imperative lines)
  CLAUDE.after.md           the same file, correctly extracted
  CLAUDE.after-broken.md    the same extraction, with one rule accidentally dropped
  docs/                     the README files produced by the extraction
ARTICLE-fr.md               the long-form French version of this text
```

### Run the demo

```bash
python audit_context.py measure  examples/CLAUDE.before.md
python audit_context.py baseline examples/CLAUDE.before.md -o /tmp/demo.json

python audit_context.py check    examples/CLAUDE.after.md        /tmp/demo.json
#   → 5 disappeared, all legitimate history. Read them, classify them, move on.

python audit_context.py check    examples/CLAUDE.after-broken.md /tmp/demo.json
#   → 6 disappeared. The extra one is the webhook signature rule.
#     That is the failure this tool exists to catch.
```

The `-broken` file is what a normal, careful extraction looks like when one rule slips through. Nothing about it is obviously wrong on reading. That is the whole point.

> **Note on `audit_context.py`.** The canonical copy lives in the authoring workspace at
> `skills/context-diet/scripts/audit_context.py`. The copy here is a duplicate and will drift.
> Re-synchronise it before any publication. That workspace has been bitten by drifting
> duplicates before, so the risk is named here rather than hidden behind a sync script nobody runs.

## License

MIT. See [LICENSE](LICENSE).
