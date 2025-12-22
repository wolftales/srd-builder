# AGENTS.md — Agent Behavior Guidelines

## Purpose
This document defines behavioral guidelines for AI coding agents working on srd-builder.
For software architecture and design patterns, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Workflow
- **Branch:** one feature per PR. Never commit to main.
- **Local development:**
  - pre-commit run -a
  - pytest -q
- **CI and container environments (no pre-commit available):**
  - ruff check .
  - ruff format --check .
  - pytest -q
- **Determinism:** No timestamps or environment-dependent values in dataset files.

## Agent Behavior

### Code Quality (Non-Negotiable)
- **Fix all linting errors:** Do NOT ignore or suppress ruff warnings without explicit justification
- **Fix all test failures:** Tests exist to catch bugs - they must pass
- **Exceptions are rare:** Only ignore linting/tests when:
  - User explicitly requests it
  - There is a documented technical limitation (add TODO comment)
  - It's a known issue being tracked separately
- **Default behavior:** Fix the problem, don't bypass the check

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
