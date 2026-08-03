# Module Content Prototype

This directory is an executable design experiment for the module-content work
described in the adjacent planning documents. It is intentionally isolated from
the production `schemas/` and `dist/` trees.

It contains:

- candidate JSON Schemas for a compiled module slice, split across `common`,
  `content`, `situations`, `relationships`, `assets`, `rules`, and the
  `module-package` envelope, plus the assembled scene context and the optional
  review companion;
- a synthetic fixture shaped to exercise the same structural pressures found in
  the selected Grimmsgate slice, without committing publication-derived content;
- an alarm-room scene-context example; and
- pytest coverage for schema validation and cross-file layering, reference
  integrity, canonical on-disk serialization, audience and warrant handling, and
  the retrieval scenarios.

Reference integrity and warrant checks are derived from the schemas rather than
hand-listed, so adding a reference-bearing or stance-carrying field extends the
checks automatically.

See `FINDINGS.md` for the conclusions and revisions exposed by the executable
fixture.

The experiment is successful when the fixtures answer the scenarios without
source-key-specific code. It is not yet a promise that these exact fields or file
boundaries will become the production package contract.

Run the focused checks with:

```bash
pytest -q tests/test_module_content_prototype.py
```

## Fixture boundary

The fixture contains complete synthetic records and the direct dependencies needed
by its scenarios. It is not a reproduction or conversion of the source publication.
The paper prototype (`docs/planning/module_content_paper_prototype.local.md`)
records the source-specific design observations. It is gitignored because it
quotes publication content; this fixture tests content shape, linkage, and
retrieval behavior safely in the public repository.
