# Module Import: Status and Handoff

**Status:** Working importer, three increments in. Producer-side only — no
release, no bundle change, nothing new for consumers to read.

**Related:** [Discovery](module_content_discovery.md) ·
[Comparison](module_content_comparison.md) ·
[Prototype FINDINGS](module_content_prototype/FINDINGS.md)

This document exists so the work can be resumed without re-deriving the reasoning.
It records what is built, what was decided and why, what is deliberately not
built, and what to do next.

## How to run it

The source publication is a third-party commercial product. It lives outside the
repository and is named by configuration:

```bash
export SRD_MODULE_SOURCE="/path/to/Grimmsgate (5e) 2020.pdf"
pytest -q tests/test_module_import.py
```

Without it, the pure tests still run and the live tests skip with a clear reason
— the same pattern as the `srd_5_1_pdf` fixture. CI needs no publication.

Compiling a location:

```python
from srd_builder.module_import.compile import compile_location_slice, write_package
from srd_builder.module_import.profile import GRIMMSGATE_5E
from srd_builder.module_import.source import resolve_source_path
from pathlib import Path

package = compile_location_slice(resolve_source_path(), GRIMMSGATE_5E, "G-3")
write_package(package, Path("build/module_packages/g3.json"))
```

Core creature resolution reads `dist/srd_5_1/`. Without a built bundle it
degrades to appendix-only resolution rather than failing.

## Non-negotiable boundaries

These are the rules that constrain every future change. They exist because
breaking them is silent and permanent.

1. **No publication content in the repository.** Compiled packages carry the
   source's prose and go under `build/` (gitignored). Notes that quote a
   publication use the `*.local.md` suffix (gitignored anywhere).
2. **Tests assert structure, never prose.** Counts, ids, types, audience,
   ordering. This has been violated twice by accident — once with room names,
   once with creature names, both as "convenient sample input" in unit tests.
   Use synthetic names; they exercise the same code paths.
3. **Source paths are configuration.** Never a path baked into `src/`.
   Resolution refuses rather than defaulting: silently importing the wrong
   publication is worse than importing none.
4. **Nothing inferred may be load-bearing.** Marked with `stance` and, for
   individual attributes, `inferred_fields`. Strip everything not
   `source_explicit` and the package must still validate and still run.

## What is built

```
src/srd_builder/module_import/
  profile.py     per-source typography as data, not logic
  source.py      I/O boundary: path resolution, identity probe, reading order
  spine.py       pure: outline -> publication records, keyed entries, stable ids
  blocks.py      pure: ordered lines -> typed content blocks
  statblocks.py  source-specific statblock extraction
  creatures.py   creature mention resolution
  package.py     pure: records -> package envelope
  compile.py     the one orchestration point
```

Against the Grimmsgate 5e publication, all 60 keyed locations compile with zero
schema errors: 92 publication nodes, 8 appendix supplements, 82 creature
relationships, 10 actor groups, 54 core rules references.

Coverage of body text by keyed locations is 52,082 of 75,896 characters. The
remainder is introduction, background, section prose, and the appendix — none of
which are keyed locations.

## Decisions, with the evidence behind them

### The reusable seam sits below the SRD prose path

Confirmed. The layout and span primitives in `utils/pdf_probe` generalize; the
SRD prose path does not. A `SourceProfile` sits above them holding typography as
data, so adding a publication should add a profile rather than a branch.

**Still unfalsified.** Only one publication has been imported. The Chaosium slice
is what tests this claim properly.

### Font roles are region-scoped, not document-wide

The first cut mapped fonts to roles across the whole document. The appendix
falsified it: `CenturySchoolbook` carries read-aloud prose in a keyed location
and statblock body text in the appendix; `TimesNewRomanPSMT` carries GM detail in
one and ability scores in the other. Read with the wrong map, the appendix parses
as eight pages of text to be read aloud at the table.

`statblock_roles` is keyed by `(font, size)` because the display face marks both a
creature name at 13pt and section headers at 11pt.

### The ruleset lens already existed

`parse.parse_monsters` splits exactly where D2 predicted:
`parse_monster_from_blocks` is SRD-layout-specific, `normalize_monster(raw)` is
publisher-agnostic. The importer does source-specific extraction and hands off to
the same normalizer SRD monster extraction uses. **No monster normalization was
written for this work.** A module supplement and an SRD monster are produced by
one contract.

### Cross-bundle namespaces are looked up, never constructed

**Superseded in principle — see [Entity Identity](entity_identity.md).** Lookup is
the correct workaround for the bundle as it exists, but the underlying id scheme
is defective and the proposal is to fix it rather than keep resolving around it.

This settles the open question, and the data allows only one answer. The bundle
files creatures under `monster:`, `npc:` and `creature:` with no rule connecting
a name to its namespace. Emitting `monster:<slug>` by convention produces
dangling references for every NPC and beast in the document.

### Warrant distinguishes what the source said from what we read

The publication marks its own creatures with "(see Appendix)" — those links are
`source_explicit`. A core creature found by matching a name against the bundle is
`source_inferred`: prose mentioning a skeleton is not necessarily an encounter
with one. `audience` on every block is inferred, because it comes from typography
rather than a stated label — which is exactly the case `inferred_fields` was
designed for, arriving from a real document rather than a hypothesis.

### Quantity is never invented

An `actor_group` is built only when the publication prints a count. A location
naming a creature without one still records the link, as a `reference`-view
relationship, rather than being dropped or given a made-up number.

## Bugs found by running it, and what they teach

Four defects, all found by execution rather than review. Three produced
**plausible-looking wrong output** rather than errors, which is the class worth
hunting.

| Defect | Symptom | Lesson |
| --- | --- | --- |
| Last keyed entry read only its starting page | T-43 truncated to 1 block | Boundaries need a rule for the final element |
| Appendix bounded by page | 6 of 8 creatures | The appendix's own children are on later pages; bound by outline *level* |
| Negative modifiers use an en dash (U+2013) | `9 (–1)` parsed as +1 | Typographic characters, not ASCII |
| `-man`/`-men` as an alternative to `-s` | "cursed humans" undetected, no error | Both plural forms, always |

The overprint finding belongs here too: display-face lines are drawn twice at an
identical bbox, so naive extraction doubles every heading. Measured at 125 of
2040 lines, all display faces, zero body text.

## What to do next

In the order I would take them.

1. **Entity identity** ([proposal](entity_identity.md)). Qualify supplement
   payload ids, make `rulesReference` structured, and decide on bundle id
   normalization. Ordered first because a breaking change is already implied by
   the reference work, and doing bundle normalization separately makes consumers
   migrate twice.

2. **Wire situations and objects.** The locations have prose describing traps,
   alarms, and treasure, and the schema has `active_features`, `situations`, and
   `objects` sitting empty. This is the largest remaining gap between "content
   extracted" and "content runnable", and it will exercise the structured
   predicate and state vocabulary against real text for the first time.

3. **A second source profile (Chaosium).** The claim that typography-as-data
   means "add a profile, not a branch" is the central architectural bet and only
   one publication has tested it. A structurally different source — an
   investigation, not a dungeon — is the honest falsification test. This also
   unblocks the information layer and R3.

4. **Assets and map regions.** Both maps are GM-owned and one carries secrets.
   Paper prototype 17.6 says page extraction alone cannot recover region links,
   so this is where human-assisted review enters the pipeline. Expect
   `inferred_fields: ["regions"]` to be the normal case, not the exception.

5. **Whole-package compile.** Everything currently compiles one location at a
   time and re-reads the appendix each call. A single pass emitting one package
   for the whole publication is straightforward but should wait until the
   collections above stop changing shape.

### Watch items

- **The assembled scene context leans on inference.** Generated summaries and
  inferred map regions already. A third instance would argue the view needs its
  own warrant summary rather than making consumers walk every record.
- **`compile_location_slice` re-reads the appendix per call.** Fine at this size,
  wasteful at whole-publication scale. Fix when doing (4), not before.
- **Coverage is 69% and unexplained beyond a plausible account.** Worth a proper
  reconciliation before claiming the importer is complete for this source.

## Still deliberately not built

- **The information layer and R3** — deferred to the investigation slice. The
  `information` value is reserved in the relationship view enum so the omission
  stays visible.
- **Dependency-edge annotations for scene assembly** — a property of the
  assembler, which does not exist yet.
- **Number words for quantity** — only digits are evidenced in this source.
- **Group display names** — a consumer refers to a group by role plus the
  creature its `rules_ref` resolves to. Sufficient here; probably not for a
  module with two bands of the same creature in one room.
