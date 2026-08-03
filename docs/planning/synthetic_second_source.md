# Synthetic Second Source: Specification

**Status:** Specification for work not yet started. Written by the author of the
importer, to be built by someone else. That separation is deliberate — see
"Why independent authorship".

**Related:** [Entity Identity](entity_identity.md) ·
[Module Import Status](module_import_status.md)

## Purpose

Every defect found in the importer so far came from a real publication doing
something the code did not expect. That is discovery, and it needs real sources.
This fixture is for the opposite job: **guarding the assumptions we now know we
make**, in CI, forever, without a commercial product.

Specifically, it exercises what a single-source producer structurally cannot test
about itself — whether content from more than one source **composes**.

### What it is not for

- **Not a discovery tool.** A synthetic fixture only contains problems its author
  already thought of. It cannot find unknown unknowns; only real publications do
  that. Grimmsgate stays the discovery instrument, and the Chaosium slice is next.
- **Not a replacement for the live tests.** Those still run against a real
  publication when one is configured.
- **Not a benchmark.** Coverage percentages and extraction quality are not the
  subject. Composition is.

## Why independent authorship

If the person who wrote the importer also writes the fixture, the fixture encodes
that person's assumptions. It then verifies the code does what its author
believed, which is not the same as verifying it does what is required. The
failure mode is silent: everything passes, and the blind spots are identical in
both artifacts.

Two rules follow, and they matter more than any individual requirement below.

1. **This document names categories of variation, not instances.** Where it says
   "a creature whose plural form is irregular", it deliberately does not say
   which. The author chooses. Preserving that surprise inside a known scope is
   the entire mechanism.

2. **Expected outcomes are authored from the source, never from a run.** Write
   down what the fixture contains — how many locations, which links should exist,
   what each block's audience is — by reading your own source description. Do not
   produce it by running the importer and recording the output. Output-derived
   expectations are a change detector, not a test: they will happily enshrine a
   bug the moment one exists.

## What it must contain

Two artifacts that collide with each other on purpose.

### Artifact A: a second ruleset bundle

A small stand-in for `dist/srd_5_1/`, in the same shape (a `items` array of
records with `id` and `name`). A dozen records is plenty.

It must make these situations real:

- **A1.** A local id that also exists in the primary bundle, denoting a different
  thing.
- **A2.** Two records in the *same* bundle sharing a display name but not an id.
  This already bit the project once — `by_name` was first-write-wins and 85
  feature names collided.
- **A3.** A display name that also exists in the primary bundle, denoting a
  different thing.
- **A4.** At least one record whose id prefix is one this project does not use.
  The claim under test is that local ids are opaque; a bundle that only uses our
  own prefixes cannot falsify it.

### Artifact B: a synthetic publication

A small adventure — a handful of keyed locations and a short appendix. It must
exercise the structural cases, each of which corresponds to a defect already
found or an assumption not yet tested:

- **B1.** A keyed entry that is the **last** one in the document.
- **B2.** A keyed entry whose content **runs past its starting page**.
- **B3.** A section whose **children appear on later pages** than the section
  heading itself.
- **B4.** **Repeated titles** at different points in the outline.
- **B5.** A **single-column** page. Every page tested so far has been two-column.
- **B6.** A region where **the same font means something different** than it does
  elsewhere in the document.
- **B7.** An appendix creature **referenced from a keyed location**, with a
  stated count, and another referenced **without** a count.
- **B8.** A creature name that is a **substring of another** creature's name.
- **B9.** A creature whose **plural form is irregular**.
- **B10.** A supplement whose slug **collides with a core record's** slug.

### Artifact C: the expected-outcome manifest

The fixture is not complete without a declaration of what it should produce. At
minimum, per the source description:

- how many keyed locations exist, and their keys
- for each, which blocks it should yield and each block's audience
- how many appendix creatures, and their names
- every location-to-creature link that should exist, and whether the publication
  *states* it or merely implies it
- every collision from A1–A4 and B10, and which record each reference should
  resolve to

This is the artifact that makes "the tester is not writing the tests" real. Write
it before running anything.

## Leeway

The fixture stands in for a publisher we have not met. So the leeway it has
should mirror the leeway a real publisher has — and wherever this spec constrains
it, we are implicitly claiming "no real publication does that". Those claims
should be visible and challengeable, not buried.

### Free rein, no permission needed

- **Names, slugs and prefixes.** Anything valid. Deliberately unfamiliar is
  better than familiar.
- **Typography.** Any font names, any sizes, any number of faces. The importer
  reads these from a profile; a fixture that reuses the existing font names tests
  nothing about the profile abstraction.
- **Page layout.** Column counts, margins, ordering of headings against body.
- **Punctuation and whitespace.** En dashes, em dashes, curly quotes,
  non-breaking spaces, ligatures, hyphenation across line breaks. One real
  publication has already broken the importer with a typographic character.
- **Document structure.** Outline depth, section ordering, whether outline order
  matches page order. It does not, in the one real source examined.
- **Ways of expressing a count.** Digits, number words, ranges, dice
  expressions, or a count stated in prose. The importer currently handles digits
  only. That is a known gap, not a fixture restriction — see adjudication.

### Constrained, and why

- **It must be synthetic.** No text, names, or statistics from any real
  publication. This fixture is committed to the repository; that is the whole
  advantage of it being synthetic, and it is lost the moment real content enters.
- **It must be internally consistent.** The manifest must match the source. A
  fixture that contradicts itself produces failures nobody can adjudicate.
- **It must be small.** Large enough to contain the cases above, small enough to
  read in one sitting and to keep CI fast. If it is not obvious at a glance what
  a failure means, it is too big.
- **It must be deterministic.** No timestamps, no randomness, no dependence on
  locale or on fonts installed on the machine.

## Adjudication

When the importer fails against the fixture, the default is that **the importer
is wrong**. That default exists so the fixture is free to be inconvenient.

The rule for the genuinely arguable cases:

> If a real publication could plausibly do it, the fixture may do it, and a
> failure is a finding.

So a count written as a number word is a legitimate fixture choice and a
legitimate importer gap, even though this spec records that gap as known. The
fixture author's job is to stay inside "plausible real publication", not inside
"what the importer currently handles".

The fixture is wrong only when it is internally inconsistent, non-deterministic,
or contains real publication content.

If a case is arguable in a way this rule does not settle, record it in the
manifest as disputed and let it fail loudly. An argued-about failure is more
useful than a quietly adjusted expectation.

## Form factor

The importer's I/O boundary is `open_source` → document → `page_lines`. Where the
fixture plugs in determines what gets tested.

| Option | Tests | Cost |
| --- | --- | --- |
| Render a real PDF | the whole path, including PDF parsing | must control fonts; needs a build step |
| Declarative source description rendered to PDF at test time | the whole path, author writes intent | small builder to write |
| Feed `page_lines`-shaped data directly | everything above PDF parsing | cannot catch PDF-layer regressions |

**Recommended: the middle option.** The author writes a declarative description
of pages, blocks, fonts and text; a small builder renders it to a real PDF during
the test run. Intent stays readable and reviewable, and the real parsing path is
still exercised. Fonts must be ones available everywhere, or embedded, so CI does
not depend on the machine.

This is a recommendation, not a requirement. If building it another way makes the
cases above easier to express, that is the author's call.

## Definition of done

- Both artifacts and the manifest are committed and synthetic.
- Every case A1–A4 and B1–B10 is present and identifiable in the manifest.
- The suite runs in CI with no configured publication and no built bundle.
- Failures name the case they came from, so a red test is diagnostic rather than
  a puzzle.
- Cases the importer does not yet satisfy are **left failing or explicitly
  marked**, with the gap recorded. They are not quietly removed to get to green.

That last point is the one most likely to be eroded under time pressure, and it
is the one carrying the value.

## Out of scope

- Extraction quality or coverage percentages.
- Performance.
- The identity normalization itself — that is
  [its own backlog entry](../BACKLOG.md). This fixture should make that change
  *verifiable*, and should be authored so it does not have to be rewritten
  when ids change: assert on links resolving, not on literal id strings, wherever
  the manifest can express it that way.
