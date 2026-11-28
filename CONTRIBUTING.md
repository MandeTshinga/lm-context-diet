# Contributing to lm-context-diet

Thank you for taking the time. This project is small on purpose: one Python file, one skill, one article. Contributions are welcome if they keep it that way.

## Where to talk

| What you want to do | Where |
|---|---|
| Ask a question, share how you used it | [Discussions](https://github.com/MandeTshinga/lm-context-diet/discussions) |
| Report a bug | [New issue, bug report](https://github.com/MandeTshinga/lm-context-diet/issues/new?template=bug_report.md) |
| Suggest a change | [New issue, feature request](https://github.com/MandeTshinga/lm-context-diet/issues/new?template=feature_request.md) |
| Propose a concrete change | A pull request, see below |

A short idea is best as a discussion first. A bug is best as an issue with a minimal file that reproduces it.

## Before a pull request

1. Open an issue or a discussion first for anything larger than a typo or a small fix, so that effort is not lost.
2. Run the tests from the repository root:

   ```bash
   python -m unittest discover tests
   ```

3. Run the demo and check that the expected results still hold (see the README, "Run the demo").

## Rules for changes

- **Standard library only.** The script has no dependency and must stay that way.
- **Keep the tool countable.** A change must not make a lost rule harder to detect. If it changes how `check` matches lines, explain why in the pull request.
- **Examples are part of the contract.** If you change the output format, update the README excerpts and the expected numbers in `tests/`.
- **English for the tool, the skill and the README.** The French article lives in `ARTICLE-fr.md` and is updated separately.
- **No personal data, no client names, no local paths** in examples or test files.

## Licence

By contributing, you agree that your contribution is released under the MIT licence of this repository.
