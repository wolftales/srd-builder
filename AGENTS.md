# AGENTS.md — Agent Behavior Guidelines

## Purpose
This document defines behavioral guidelines for AI coding agents working on srd-builder.
For software architecture and design patterns, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Workflow
- **Branch model:** This is a solo project. Direct commits to `main` are the
  norm, not the exception. The "never commit to main" rule applies if and when
  additional contributors join — at that point switch to feature branches and
  PR review. Until then, the goal is fast iteration with the safety nets below
  doing the work that a reviewer would otherwise do.
- **Every commit must leave the tree green.** Before committing:
  - `pre-commit run -a` (ruff, ruff-format, mypy, sync-doc-tables, no-srd-pdf, pretty-json)
  - `pytest -q` (full suite, including the `package` marker)
  - For releases: `make verify-ci` (adds the strict bundle validator as step 5/5)
- **CI / container environments (no pre-commit available):**
  - `ruff check .`
  - `ruff format --check .`
  - `pytest -q`
- **Pushing:** Pushing to `origin/main` makes the change visible to consumers
  (e.g. the Blackmoor integration). Push when a logical chunk of work is done
  and tested; don't push WIP. Tagged releases (`vX.Y.Z`) should always be
  pushed alongside the commit they tag.
- **Determinism:** No timestamps or environment-dependent values in dataset files.

## Agent Behavior

### Code Quality (Non-Negotiable)
- **Fix all linting errors:** Do NOT ignore or suppress ruff warnings without explicit justification
- **Fix all test failures:** Tests must pass, but sometimes the fix is updating the test
  - **Bug in code:** Fix the implementation to match test expectations
  - **Intentional behavior change:** Update test to match new behavior (document why in commit)
  - **Outdated test:** Remove or update tests that no longer apply
- **Exceptions are rare:** Only ignore linting/tests when:
  - User explicitly requests it
  - There is a documented technical limitation (add TODO comment)
  - It's a known issue being tracked separately
- **Default behavior:** Fix the problem (code OR test), don't bypass the check

### Code Changes
- Always check [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for module boundaries and patterns
- Follow the modular pattern (Extract → Parse → Postprocess) for new datasets
- Preserve function purity: no I/O in parse/postprocess modules
- Run tests after changes: `pytest -q`

### Testing
- Create golden tests for new datasets: `tests/test_golden_{dataset}.py`
- Use fixture-based tests (raw + normalized)
- See ARCHITECTURE.md for golden test patterns and examples

### Validation
- Validate all generated JSON against schemas: see [docs/VERIFICATION_CHECKLIST.md](docs/VERIFICATION_CHECKLIST.md)
- Run full verification before commits: `pytest tests/test_golden_*.py -v`
- Check file sizes and structure match expected values
- Schema validation catches 90% of parsing bugs early

### PDF extraction discipline (no magic wands)

Historically, several hand-curated data files in this repo were created
with a vague "PDF text is corrupted" justification, and two of them
(lineages, spell-class lists) have already been mechanically disproved
by reproducer tests — the text was never corrupted, just not
whitespace-normalized. Treat "corruption" as a hypothesis, never a
conclusion.

Before declaring any PDF region "corrupted," "unreadable," or
"unextractable":

1. Add a reproducer test in [tests/test_pdf_provenance.py](tests/test_pdf_provenance.py)
   using [src/srd_builder/utils/pdf_probe.py](src/srd_builder/utils/pdf_probe.py).
   The test must assert what specifically is *not* extractable (which
   page index, which call, what bytes came back).
2. If you cannot write a reproducer that fails on real PDF behavior,
   the region is not corrupted — it is just unparsed. Write the parser.
3. Hand-curated overrides (`*_targets.py`, `*_manual.py`) are a last
   resort, not a default. Each requires an entry in
   [docs/PROVENANCE.md](docs/PROVENANCE.md) with a `reason_code`, and
   any `pdf_corruption` entry must link a passing reproducer.
4. New page-text extraction MUST consume `utils.pdf_probe` and
   [src/srd_builder/utils/page_index.py](src/srd_builder/utils/page_index.py)
   rather than introducing fresh `fitz.open()` calls or hardcoded page
   constants.

This rule exists because the prior path — declare corrupted, transcribe
by hand, move on — quietly accumulated ~2,000 lines of hand-curated
data across the codebase, most of which now appears to be needless.

### Version Control
- **Commit granularity:** One logical change per commit
- **Commit messages:** Follow conventional commits (FEAT:, FIX:, REFACTOR:, DOC:)
- **Breaking changes:** Document in commit message body
- **Schema version bumps:** Coordinate with package version (see ARCHITECTURE.md § Version Management)
- **No WIP commits:** Each commit should leave the codebase in a working state

### Documentation
- Update ARCHITECTURE.md for design decisions
- Update release notes for user-facing changes
- Keep AGENTS.md focused on agent behavior only

## Quick Reference
- Module boundaries: see ARCHITECTURE.md § "Module Boundaries"
- Testing patterns: see ARCHITECTURE.md § "Testing Guidelines"
- Architectural patterns: see ARCHITECTURE.md § "Pipeline Architecture"
- Validation process: see docs/VERIFICATION_CHECKLIST.md
