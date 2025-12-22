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

### Code Changes
- Always check [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for module boundaries and patterns
- Follow the modular pattern (Extract → Parse → Postprocess) for new datasets
- Preserve function purity: no I/O in parse/postprocess modules
- Run tests after changes: `pytest -q`

### Testing
- Create golden tests for new datasets: `tests/test_golden_{dataset}.py`
- Use fixture-based tests (raw + normalized)
- See ARCHITECTURE.md for golden test patterns and examples

### Documentation
- Update ARCHITECTURE.md for design decisions
- Update release notes for user-facing changes
- Keep AGENTS.md focused on agent behavior only

## Quick Reference
- Module boundaries: see ARCHITECTURE.md § "Module Boundaries"
- Testing patterns: see ARCHITECTURE.md § "Testing Guidelines"
- Architectural patterns: see ARCHITECTURE.md § "Pipeline Architecture"
