# PDF Extraction Solution Plan (v0.3.0)

> **Status:** Enhanced with critical questions and decision points
> **Last Updated:** Post-GPT review + Claude analysis
> **Philosophy:** "Select the best path forward, not just the easy path"

---

## 🚨 Executive Summary: Critical Decisions Needed

Before implementing v0.3.0, we must answer these foundational questions:

### 1. **Extraction Scope** (BLOCKING)
- [x] Targeted monsters section (pages 302-384?) vs. whole-PDF extraction → **Start targeted; design APIs to accept arbitrary page iterables so whole-PDF is a config flip later.**
- [ ] Document exact monster section page range in SRD 5.1 *(still requires manual confirmation, see Quick Wins)*
- [x] Decision impacts: speed, reusability, maintainability → **Captured in Section 2 guidance.**

### 2. **Raw JSON Schema** (BLOCKING)
- [x] Define exact structure of `monsters_raw.json` → **See Section 2 + Phase 1 schemas for recommended shape.**
- [x] Granularity: block-level, line-level, or word-level? → **Adopt PyMuPDF block/span granularity with ordered tokens.**
- [x] Metadata: bbox coords, font info, column markers? → **Store `bbox`, `font`, `font_size`, `color`, `column`, and derived `is_header`.**
- [ ] Create `schemas/raw_monster.schema.json` BEFORE coding *(schema template provided below; needs commit)*

### 3. **Reference Data Strategy** (BLOCKING)
- [x] How to use 14MB `srd_cc_v5.1_rules_tabyltop.json`? → **Treat as comparison-only; use for name/count recall, never as authoritative stats.**
- [x] Extract monster names/count for validation → **Script skeleton below extracts canonical monster IDs and counts.**
- [x] Trust as ground truth or just comparison baseline? → **Baseline only; flag mismatches but do not fail build automatically.**
- [ ] Create `scripts/analyze_reference.py` for inspection *(skeleton provided; still needs implementation/test)*

### 4. **PDF Layout Analysis** (BLOCKING)
- [ ] What font size threshold distinguishes headers? (Measure actual PDF)
- [ ] What X-coordinate divides columns? (Measure actual PDF)
- [x] Test PyMuPDF extraction options: `layout=True` vs `sort=True` → **Use `page.get_text("dict")` / `page.get_textpage().extractDICT()`; avoid `layout=True` flag confusion.**
- [ ] Create `scripts/explore_pdf.py` for experimentation *(skeleton provided; still needs data capture)*

### 5. **Bridge Strategy** (Design Decision)
- [x] How to connect extraction → existing parser? → **Introduce lightweight bridge transformer for v0.3.0.**
- [x] Option A: Extract → `monsters_raw.json` → `monsters.json` (bridge) → **Chosen for compatibility.**
- [ ] Option B: Update `parse_monsters.py` to read raw format directly *(defer to v0.4.0 refactor)*
- [x] Impacts v0.3.0 scope and v0.4.0 refactoring → **Documented in Sections 3 & Appendix.**

---

## 📋 Original GPT Solution Plan

Perfect — that's the right step.
Now that you've closed **v0.2.0 (fixture pipeline)** and are planning **v0.3.0 (PDF Extraction)**, this is where we turn the **EXTRACTION_CHALLENGES.md** doc from "problem catalog" → "solution plan."

Below is a structured outline that (1) **summarizes what you have**, (2) **adds the new technical and procedural improvements** that emerged in my review, and (3) **proposes roadmap adjustments** for both near-term and later stages.

---

## 🧭 1. Reframing the Extraction Problem

The *challenges doc* correctly highlights three broad categories:

1. **Segmentation & detection** – Where monsters begin and end.
2. **Structure & fidelity** – How to preserve visual layout, sections, and ordering.
3. **Repeatability & maintenance** – How to ensure deterministic, maintainable results.

Those categories remain valid — but the next step is turning each into an **engineering track** with measurable deliverables.

### **Critical Clarification: Two-Phase vs. Whole-PDF Extraction**

**Current Understanding:** Extract *only the monsters section* as raw → parse → normalize

**Alternative Approach:** Extract *entire PDF* as raw → filter monsters → parse → normalize

**Decision Point:**
- **Targeted extraction (monsters only):**
  - ✅ Faster, less noise
  - ✅ Easier to validate
  - ❌ Need to know page boundaries of monster section
  - ❌ Harder to extend to spells/items later (different page ranges)

- **Whole-PDF extraction:**
  - ✅ Generic approach works for all sections
  - ✅ Can reuse same raw output for multiple entity types
  - ✅ No need to maintain page-range configs
  - ❌ Larger intermediate files
  - ❌ More processing overhead

**Recommendation:** Start with targeted (monsters section only) for v0.3.0, but design the extractor to be extensible to whole-PDF in v0.5.0.

**Required:** Document monster section page range in SRD 5.1 (approximate: pages 302-387?)

---

## ⚙️ 2. Technical Approach — Updated Recommendations

| Challenge                | Recommended Approach                                                                                                                                                                                  | Why This Change Improves Quality                                                                                                                   |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Boundary detection**   | Use `page.get_text("dict")` → iterate `blocks → lines → spans`. Detect headers via span `size` spikes, `font` flags (contains `Bold`), and the canonical type-line ("size, type, alignment") span. Maintain fallback keyword anchors (`Armor Class`, `Hit Points`, etc.) when font heuristics fail. | More robust than line-only parsing; avoids PyMuPDF ordering surprises because `dict` preserves reading order. Works even if the PDF mixes embedded fonts. |

**Open Questions for Boundary Detection:**
- What font size threshold? (Need to analyze PDF to determine)
- What if monster name uses same font as body text? (Some PDFs do this)
- How to handle variants like "Adult Black Dragon (Variant)"?
- Do all monsters have the "size, type, alignment" pattern? (Need verification)
- Fallback strategy if both methods fail?

**Action Required:** Write exploratory script to analyze font sizes/styles in monsters section.

**Updated Guidance:**
- Expect header spans around 13–16 pt vs body 8–9 pt based on SRD typography; script above will confirm and set thresholds in config.
- If header font matches body size, rely on the type-line ("size, type, alignment") span plus capitalized text and zero leading spaces.
- Variants retain the type-line pattern; treat full span text as header even if parentheses appear.
- Rare monsters (e.g., lair actions) still include type-line; fallback to `Armor Class` sentinel ensures boundary.
- If both font + pattern fail, fall back to referencing previous header and emit `warnings.append("header_inference_failed")`.

| **Two-column layout**    | Derive column split per page from `page.rect.width` (midpoint) or by clustering span `bbox[0]` values. Assign spans to `column` via midpoint and sort by `(column, bbox[1], bbox[0])`. When a span crosses midpoint, duplicate it into both columns and merge downstream so monsters that wrap columns remain contiguous.                                                                                                     | Handles SRD column breaks deterministically; avoids brittle reliance on `layout=True` and reduces manual fixes for cross-column flows.                                                          |

**Open Questions for Two-Column Handling:**
- What is the X-coordinate threshold for column boundaries? (Need to measure)
- How do we handle monsters that span column boundaries mid-stat-block?
- What about single-column title pages or full-width content?
- Should we store bounding box data in raw JSON for debugging?
- How to validate correct column ordering? (Left→Right expected)

**Action Required:** Analyze page layouts in monsters section; test PyMuPDF dict/blocks extraction.
**Updated Guidance:**
- Midpoint will be ~306 pt on US Letter; derive automatically per page so rulebooks with different trim sizes work.
- When a block crosses columns, duplicate the span assignment and let parser dedupe by `bbox`; also emit warning for manual review.
- Detect single-column pages by measuring standard deviation of `bbox[0]`; if < 40 pt, treat as single column and set `column = 0` for all spans.
- Yes—store `bbox` and column per span (already in schema) for deterministic debugging.
- Validate ordering by comparing extracted monster sequence to reference JSON names; mismatches flag layout issues.
| **Output structure**     | Save a "verbatim + metadata" format (`monsters_raw.json`): each monster keeps ordered text blocks, page/column data, and section offsets. Persist spans as `{ "text": str, "bbox": [x0,y0,x1,y1], "font": str, "size": float, "color": [r,g,b], "flags": int, "column": int }`.                                                             | Separates *capture* from *parsing*. Enables diffing, re-extraction, and incremental parser improvements without re-scraping the PDF.               |

**Critical Design Question: Raw JSON Schema**
What exactly goes in `monsters_raw.json`? Need to define:
```json
{
  "name": "Aboleth",
  "pages": [123, 124],
  "blocks": [
    {"page": 123, "column": 1, "y": 72.5, "text": "Aboleth", "font_size": 14, "bold": true},
    {"page": 123, "column": 1, "y": 85.2, "text": "Large aberration, lawful evil", "font_size": 9}
  ],
  "sections": {
    "header": {"start_block": 0, "end_block": 1},
    "stats": {"start_block": 2, "end_block": 15}
  },
  "markers": ["Armor Class", "Hit Points", "Speed"],
  "warnings": ["possible_column_break_mid_block"]
}
```
**Questions:**
- Do we capture font names or just sizes?
- How granular: per-line, per-word, per-character?
- Do we preserve exact PDF coordinates or just relative ordering?
- Should sections be auto-detected or left for v0.4.0 parser?

**Action Required:** Define `schemas/raw_monster.schema.json` BEFORE implementing extraction.
**Updated Guidance:** Capture font names and sizes; store per-span coordinates (`bbox`) and derived column; postpone automatic section detection to v0.4.0 but store sentinel markers (first index of `Armor Class`, `Actions`, etc.) to help parser.
| **Parsing depth**        | v0.3.0 = surface capture (no field parsing); v0.4.0 = structured parsing via section-state machine.                                                                                                   | Keeps milestones clean. Extraction is validated independently of normalization.                                                                    |
| **Error handling**       | Always succeed if ≥1 monster extracted. Record `extraction_warnings` per monster and a top-level `extraction_report`.                                                                                 | Prevents total-pipeline failure while maintaining auditability.                                                                                    |
| **Determinism**          | Round coordinates to two decimals, strip non-breaking spaces (`\u00a0`), collapse multi-space runs, and sort spans by `(page, column, bbox[1], bbox[0])`. Embed PDF SHA-256, extractor version, and PyMuPDF version in `_meta`.                                                                                                        | Allows byte-identical re-runs, enabling CI regression tests and caching; rounding insulates against PyMuPDF float jitter between releases.                                                                           |
| **Incremental builds**   | Re-extract only if `pdf_sha256` differs from saved `meta.json`.                                                                                                                                       | Prevents unnecessary reprocessing during repeated builds.                                                                                          |
| **Extensibility**        | Keep raw JSON schema minimal and generic: `name`, `pages`, `blocks`, `sections`, `markers`, `warnings`.                                                                                               | Works for monsters now, spells/classes later, and for SRD 5.2.1 / Pathfinder ORC.                                                                  |
| **Testing & validation** | Snapshot test small PDFs; add coverage metric comparing extracted monster names against reference dataset.                                                                                            | Converts "qualitative correctness" into measurable regression metric.                                                                              |

### PyMuPDF Implementation Notes

* **Primary APIs:**
  * `fitz.open(pdf_path)` – open once per extraction run; reuse document handle to avoid file descriptor churn.
  * `page = doc.load_page(index)` – zero-based; wrap in generator that yields configured page range.
  * `textpage = page.get_textpage(flags=fitz.TEXTFLAGS_TEXT)` – stable text layout without enabling expensive image parsing.
  * `page.get_text("dict", textpage=textpage)` – returns `{"blocks": [...]}` with nested `lines`/`spans` plus font metadata.
  * `page.get_fonts()` – enumerate fonts per page if we need to map font IDs to readable names.
  * `page.get_images()` – skip for now; monsters section is text-only.
* **Python gotchas:**
  * Coordinates are floats in PDF points; rounding before serialization prevents meaningless diffs.
  * PyMuPDF reuses internal buffers – do not hold on to `dict` objects after mutating; convert to plain `dict`/`list` via `copy.deepcopy` or comprehension.
  * Fonts with spaces require quoting when comparing; normalize to lowercase to avoid platform-specific casing.
  * Avoid `page.get_text("text")` because it discards bounding boxes and merges hyphenated words; stick to `dict`.
  * Use `with fitz.open(...) as doc:` to guarantee document close even if extraction raises.

### Alternative / Complementary Libraries

* **pdfplumber** – built on pdfminer.six; slower but offers table detection. Keep as fallback for corner cases where PyMuPDF mis-orders spans. No change needed for v0.3.0.
* **pdfminer.six** – provides low-level layout; heavier API and more boilerplate. Only worth exploring if PyMuPDF cannot expose needed metadata (unlikely here).
* **pypdf / PyPDF2** – good for page splitting/merging but lacks layout context; not recommended for extraction.
* **layoutparser + Detectron** – overkill unless we hit image-based PDFs. Defer.
* **tabula / camelot** – table-specific; monster stat blocks are not tables. Skip.
* **fitz (PyMuPDF) textpage XML** – if we need to debug reading order, `page.get_text("xml")` can visualize structure without extra dependencies.

**Recommendation:** Stick with PyMuPDF for core extraction; keep pdfplumber bookmarked as a validation tool if we encounter pathological layouts. No additional dependencies for v0.3.0.

**Critical Question: How to Use the 14MB Reference JSON?**
We have `rulesets/srd_5_1/raw/srd_cc_v5.1_rules_tabyltop.json` (entire PDF extraction).

**Validation Strategy Options:**
1. **Extract monster names** from reference JSON → compare against our extraction (recall metric)
2. **Use as quality baseline** → our normalized output should be "at least as good"
3. **Compare field completeness** → check we're capturing all stat blocks
4. **Create diff reports** → highlight where we diverge

**Questions:**
- What's the structure of the reference JSON? (Need to inspect)
- Can we trust it as ground truth, or just a comparison point?
- Should we create a `scripts/analyze_reference.py` to understand its schema?
- Do we validate during extraction (v0.3.0) or normalization (v0.4.0)?

**Action Required:** Analyze reference JSON structure; create comparison script.
**Updated Guidance:** The dataset is a flat list of entries with `category` and `content` keys; treat monsters as entries where `category == "monster"`. Use it for recall metrics only. Run validation during v0.3.0 as a non-blocking report and enforce thresholds in v0.4.0 when normalization catches up.

---

## 🧩 3. Structural / Architectural Improvements

1. **Extraction as an isolated stage**

   * Create `/src/srd_builder/extract/` package.
   * `pdf_monsters.py` outputs to `raw/extracted/`.
   * Future: `extract/pdf_spells.py`, `extract/pdf_items.py`, etc.

   **Design Question:** Should extraction be a sub-package or top-level module?
   - Option A: `src/srd_builder/extract/pdf_monsters.py` (better namespace isolation)
   - Option B: `src/srd_builder/extract_monsters.py` (simpler, matches existing pattern)

   **Recommendation:** Start with Option B for v0.3.0, refactor to Option A in v0.5.0 when adding spells/items.

2. **Bridge Pattern for Back-compatibility**

   * Write a lightweight `raw/monsters.json` as a compatibility shim for the existing parser until v0.4.0 rewrites normalization.

   **Critical Decision: What Goes in the Bridge?**
   - Option A: Extract → `monsters_raw.json` (full verbatim) → `monsters.json` (minimal bridge for parser)
   - Option B: Extract → `monsters_raw.json` only; update `parse_monsters.py` to read it directly

   **Questions:**
   - Does current `parse_monsters.py` expect specific structure?
   - Can we make it work with raw extraction, or do we need preprocessing?
   - Should v0.3.0 include basic field parsing to generate compatible bridge?

   **Action Required:** Review `parse_monsters.py` dependencies; decide on bridge schema.

3. **Metadata Tracking**

   * Extend `raw/meta.json` with `{ "pdf_sha256": "...", "build_time": "...", "tool_version": "0.3.0" }` for provenance.

4. **Quality Metrics**

   * Include extraction report fields: `monster_count`, `pages_processed`, `warnings_count`, `elapsed_seconds`.
   * Enables CI assertions like “must extract ≥ 320 monsters”.

5. **Cross-ruleset Compatibility**

   * Make extractor configurable via `ruleset_config.yaml` (page size, column widths, known font names).
   * Future: supports SRD 5.2.1 or Pathfinder PDFs without code change.

   **Configuration Design Question:**
   ```yaml
   # rulesets/srd_5_1/config.yaml
   extraction:
     pdf_path: "raw/SRD_CC_v5.1.pdf"
     monsters:
       page_range: [302, 384]  # or "auto" to scan whole PDF
       header_font_size_min: 13
       column_boundary_x: 306  # midpoint between columns
       expected_count_min: 320
   ```

   **Questions:**
   - Should config be YAML or JSON?
   - Where should defaults live? (extractor code vs base config)
   - How to handle "auto" page detection for future rulesets?

   **Recommendation:** Start with hardcoded values in v0.3.0, extract to config.yaml in v0.4.0.

6. **Repeatability & Debugability**

   * Provide `--visualize` CLI option that overlays bounding boxes in an output PNG for manual review (optional dev mode).

   **Implementation Question:**
   - Use PyMuPDF's built-in annotation features?
   - Or generate separate debug PNGs with Pillow/matplotlib?
   - Should visualization be CLI flag or separate script?

   **Recommendation:** Defer to v0.4.0; focus v0.3.0 on core extraction. Add as `scripts/visualize_extraction.py` when needed for debugging.

---

## 🧪 4. Process and Team Hygiene Upgrades

| Area                   | Upgrade                                                                                             |
| ---------------------- | --------------------------------------------------------------------------------------------------- |
| **Testing discipline** | Create `tests/extract/test_pdf_monsters_basic.py` (fixture PDF → count & section assertions).       |
| **CI**                 | Add extraction smoke test under GitHub Actions with an embedded mini-PDF (so no license issues).    |
| **Docs**               | Add `docs/reference/extraction.md` summarizing algorithm and schema.                                |
| **Version gating**     | Begin tagging extractor versions (`extract_version: 1`) inside output to guarantee reproducibility. |
| **Error visibility**   | During build, print summary table (monsters found / skipped / warnings).                            |

---

## 🗺️ 5. Proposed ROADMAP Additions / Adjustments

### 📍 v0.3.0 — PDF Extraction (current)

**Goal:** deterministic `monsters_raw.json` generation from SRD PDF.

**CRITICAL PRE-WORK (Must Complete First):**
1. **Determine monster section page range** in SRD_CC_v5.1.pdf
   - Manual inspection or ToC parsing?
   - Document exact pages (e.g., "p. 302-384")
   - Add to `rulesets/srd_5_1/config.yaml` or hardcode in extractor?

2. **Define raw JSON schema** (`schemas/raw_monster.schema.json`)
   - Block-level granularity? Line-level?
   - What metadata: bbox coords, fonts, column info?
   - Section markers or leave unstructured?

3. **Analyze reference JSON** (`scripts/analyze_reference.py`)
   - Extract monster list for validation
   - Understand field completeness
   - Create baseline metrics

4. **Test PyMuPDF extraction** (`scripts/explore_pdf.py`)
   - Font size analysis (determine header threshold)
   - Column boundary detection (X-coord thresholds)
   - Layout options comparison (layout=True vs sort=True)

**Deliverables**

* `src/srd_builder/extract_monsters.py` (implemented)
* `schemas/raw_monster.schema.json` (defines verbatim format)
* Integration in `build.py` (calls extractor before parser)
* `rulesets/srd_5_1/raw/monsters_raw.json` (extracted output)
* `extraction_report.json` (counts, warnings, timing)
* Snapshot tests for single-monster fixture
* `scripts/analyze_reference.py` (validation helper)
* `scripts/explore_pdf.py` (dev/debug tool)

**Exit criteria**

* Deterministic JSON generation (identical SHA256 on re-run)
* ≥ 320 monsters detected from SRD 5.1 PDF (based on reference count)
* ≥ 95% name match rate vs. reference JSON
* Zero build failures on re-run with identical PDF
* All extracted monsters include: name, pages, blocks
* Extraction report includes: monster_count, pages_processed, warnings

---

### 📍 v0.4.0 — Normalization Fidelity

**Goal:** structured parsing of `monsters_raw.json` → normalized schema.

**New Tracks**

1. **State-machine parser**: split traits, actions, reactions, legendary actions.
   - **Question:** How to handle edge cases like "Lair Actions" vs "Legendary Actions"?
   - **Question:** What about monsters with non-standard sections (e.g., "Variant:" blocks)?

2. **Heuristic repair**: fix hyphenation & list detection.
   - **Question:** Regex-based or ML-based dehyphenation?
   - **Question:** How to handle bulleted lists vs. comma-separated lists?

3. **Coverage comparison**: name+AC+HP fields match ≥ 95 % of reference JSON.
   - **Question:** What if reference JSON is wrong? How do we validate the validator?
   - **Question:** Should we prioritize correctness over coverage?

4. **Refactor build**: replace bridge file with direct raw→parsed pipeline.
   - **Breaking change:** `parse_monsters.py` will need significant rewrite
   - **Migration path:** Keep old parser as `parse_monsters_legacy.py` during transition?

---

### 📍 v0.5.0 — Cross-Ruleset Generalization

**Goal:** parameterize extractor to support SRD 5.2.1, Pathfinder ORC, etc.

* Introduce `extract_config.yaml` per ruleset (page size, columns, fonts).

**Design Challenge: Abstraction Level**
- **Option A:** One extractor with config variations per ruleset
- **Option B:** Base extractor class + ruleset-specific subclasses
- **Option C:** Plugin architecture for different PDF layouts

**Questions:**
- How different are Pathfinder layouts vs D&D 5e?
- Can we abstract "two-column monster stat block" as a universal pattern?
- What about non-Latin scripts or RTL languages?

**Recommendation:** Start with Option A (config-driven), refactor to Option B if needed.
* Expand test suite with alternate PDFs.

---

## 🛡️ High-Confidence Implementation Practices

1. **One-pass extraction pipeline** – Load each page once, emit spans immediately, and stream-write JSON to disk to avoid high memory usage.
2. **Typed configuration** – Define an `ExtractionConfig` dataclass (page range, header size min, column tolerance) and pass it to helpers; default config lives in code, overrides in `ruleset_config.yaml` later.
3. **Deterministic rounding** – Apply `round(value, 2)` for coordinates and font size; convert to integers where possible (pages, columns) before serialization.
4. **Warning-first error handling** – Capture warnings per monster (e.g., `missing_type_line`, `column_split_guess`) and aggregate them in `extraction_report.json` instead of aborting extraction.
5. **Unit + snapshot coverage** – Add fixture PDF with two monsters, assert entire `monsters_raw.json`, and unit-test boundary detection on synthetic spans.
6. **CLI ergonomics** – Expose `--pages`, `--limit-monsters`, and `--output` flags so contributors can iterate quickly and produce proof-of-concepts.
7. **Data provenance** – Include `_meta = {"pdf_sha256": str, "page_range": [start, end], "extracted_at": iso8601, "extractor_version": "0.3.0"}` in final JSON for auditing.

## ⚠️ Risk Assessment

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| **Reading order drift** when PyMuPDF changes algorithms | Medium – could reorder spans and break diff-based tests | Pin PyMuPDF version; add regression snapshot; round coordinates. |
| **Headers without bold fonts** (variants, lair actions) | Medium – header detection fails causing merged monsters | Combine font heuristics with keyword anchors and uppercase detection; emit warning when heuristics disagree. |
| **Multi-column wrap mid-stat-block** | High – sections may interleave | Duplicate spans that straddle column midpoint and merge using y-order; mark monsters needing manual review. |
| **PDF errata releases** | Medium – thresholds drift | Re-run Phase 1 scripts when PDF SHA changes; keep config-driven approach. |
| **Reference JSON mismatches** | Low – false alarms | Treat reference metrics as advisory; rely on internal consistency for pass/fail. |
| **Memory spikes on full extraction** | Low – PyMuPDF is efficient but JSON serialization can grow | Stream output using `json.dump` with incremental writes or chunked buffers. |

## 🔁 Prioritization & Parallelization Check

* `scripts/analyze_reference.py` and schema drafting can proceed simultaneously.
* `scripts/explore_pdf.py` depends only on knowing approximate page range; once first few pages confirmed, run it.
* Extraction prototype (`extract_monsters.py`) can start once schema + header threshold baseline exist; integration with `build.py` waits until JSON shape is stable.
* Tests and docs (P1/P4) can be prepared while extraction polishing continues; no hard dependency on final counts.
* Validation tasks (P5–P7) require both extractor output and reference summary but can iterate in parallel with bug fixes.

## 🚀 Quick Wins (Do Today)

1. **Confirm page bounds** – Open PDF, record first/last monster page, and log in `docs/reference/monster_page_range.md`.
2. **Run `scripts/explore_pdf.py --pages 302 303`** – Capture header font sizes + column midpoint; check into repo as JSON artifact for regression.
3. **Proof-of-concept extraction** – Hard-code first monster's pages, dump raw JSON, and run through schema validator to prove pipeline end-to-end.
4. **Reference baseline** – Execute `scripts/analyze_reference.py` and stash output for comparison; adds guardrail for name recall.
5. **Automated schema check** – Add `python -m jsonschema --instance raw/monsters_raw.json schemas/raw_monster.schema.json` to local checklist.

## 🧱 6. Optional Enhancements (Future Ideas)

* **Parallel extraction:** page-level multiprocessing for speed on large PDFs.
  - **Question:** Is extraction CPU-bound or I/O-bound?
  - **Question:** How to handle cross-page monster stat blocks in parallel?

* **Chunked rebuilds:** store per-page intermediate JSON; re-combine via indexer.
  - **Question:** Does this actually save time for incremental builds?
  - **Question:** How to invalidate chunks when PDF changes?

* **OCR fallback:** integrate `pdf2image + Tesseract` if PDF lacks text layer.
  - **Note:** SRD 5.1 has text layer, but good for scanned PDFs
  - **Question:** Quality threshold before triggering OCR fallback?

* **Metrics dashboard:** auto-generate `dist/<ruleset>/build_report.html` summarizing extraction stats and warnings.
  - **Question:** Worth the complexity vs. just reading JSON report?
  - **Recommendation:** Add in v0.6.0 if user feedback requests it.

---

## ✅ 7. Immediate Next Actions (Revised with Pre-Work)

### Phase 1: Research & Design (Must Complete Before Coding)

| Priority | Task                                                                                    | Outcome                                        | Est. Time |
| -------- | --------------------------------------------------------------------------------------- | ---------------------------------------------- | --------- |
| 🔴 P0    | **Find monster section page range** in SRD_CC_v5.1.pdf (manual inspection)             | Document exact pages (e.g., 302-384)           | 30 min    |
| 🔴 P0    | **Analyze reference JSON** (`scripts/analyze_reference.py`)                            | Monster count, name list, structure understanding | 1 hour  |
| 🔴 P0    | **Define raw JSON schema** (`schemas/raw_monster.schema.json`)                         | Clear contract for extraction output           | 1 hour    |
| 🔴 P0    | **Explore PDF with PyMuPDF** (`scripts/explore_pdf.py`)                                | Font sizes, column boundaries, layout options  | 2 hours   |

**Why P0?** Cannot write extractor without knowing: where monsters are, what success looks like, what output format is, how PDF is structured.

#### Phase 1 Script & Schema Skeletons (Ready to Implement)

```python
# scripts/explore_pdf.py
"""Dump font/column metrics for a sample of pages."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from statistics import mean

import fitz  # PyMuPDF


def inspect_page(page: fitz.Page) -> dict:
    textpage = page.get_textpage()
    data = page.get_text("dict", textpage=textpage)
    fonts = Counter()
    column_edges: list[float] = []
    for block in data["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "")
                font = span.get("font", "")
                size = span.get("size", 0.0)
                fonts[(font, round(size, 2))] += len(text)
                if not (bbox := span.get("bbox")) or len(bbox) < 4:
                    continue
                column_edges.append(bbox[0])
    midpoint = page.rect.width / 2
    left = [value for value in column_edges if value < midpoint]
    right = [value for value in column_edges if value >= midpoint]
    return {
        "page": page.number + 1,
        "midpoint": midpoint,
        "fonts": list(fonts.most_common(10)),
        "left_sample": mean(left) if left else 0,
        "right_sample": mean(right) if right else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", help="Path to SRD PDF")
    parser.add_argument("--pages", nargs="*", type=int, help="1-based page numbers to inspect")
    args = parser.parse_args()

    with fitz.open(args.pdf) as doc:
        pages = args.pages or range(1, doc.page_count + 1)
        report = [inspect_page(doc.load_page(page_number - 1)) for page_number in pages]
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
```

```python
# scripts/analyze_reference.py
"""Summarize the TabylTop JSON reference dataset."""

from __future__ import annotations

import argparse
import json
from collections import Counter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", help="Path to srd_cc_v5.1_rules_tabyltop.json")
    args = parser.parse_args()

    with open(args.json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    monsters = [entry for entry in data if entry.get("category") == "monster"]
    names = [entry.get("name", "").strip() for entry in monsters]
    duplicates = {name: count for name, count in Counter(names).items() if count > 1}

    summary = {
        "total_entries": len(data),
        "monster_count": len(monsters),
        "monster_names": sorted(name for name in names if name),
        "duplicates": duplicates,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
```

```json
// schemas/raw_monster.schema.json (draft)
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://srd-builder.dev/schemas/raw_monster.schema.json",
  "type": "object",
  "required": ["name", "pages", "blocks"],
  "additionalProperties": {
    "description": "Forward-compatible extension hook (e.g., _meta, extraction_info, debug stats)"
  },
  "properties": {
    "name": {"type": "string", "minLength": 1},
    "simple_name": {"type": "string"},
    "pages": {
      "type": "array",
      "items": {"type": "integer", "minimum": 1},
      "minItems": 1,
      "uniqueItems": true
    },
    "blocks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["page", "column", "bbox", "text"],
        "additionalProperties": false,
        "properties": {
          "page": {"type": "integer", "minimum": 1},
          "column": {"type": "integer", "minimum": 0},
          "bbox": {
            "type": "array",
            "items": {"type": "number"},
            "minItems": 4,
            "maxItems": 4
          },
          "text": {"type": "string"},
          "font": {"type": "string"},
          "size": {"type": "number"},
          "color": {
            "type": "array",
            "items": {"type": "integer", "minimum": 0},
            "minItems": 3,
            "maxItems": 3
          },
          "flags": {
            "type": "integer",
            "description": "PyMuPDF text flags bitmask; encodes text extraction properties (e.g., bold, italic, etc.)"
          },
          "is_header": {"type": "boolean"}
        }
      }
    },
    "markers": {
      "type": "array",
      "items": {"type": "string"}
    },
    "warnings": {
      "type": "array",
      "items": {"type": "string"}
    },
    "_meta": {
      "type": "object",
      "description": "Optional debug or provenance metadata retained for forward compatibility"
    }
  }
}
```

> **Note:** Scripts intentionally avoid side effects and print JSON to stdout so they can double as data sources for snapshot tests.

### Phase 2: Implementation (After Pre-Work Complete)

| Priority | Task                                                                                    | Outcome                                        | Est. Time |
| -------- | --------------------------------------------------------------------------------------- | ---------------------------------------------- | --------- |
| 🔹 P1    | Update **EXTRACTION_CHALLENGES.md** with solutions from this document                  | Turn "problem catalog" → "design spec"         | 30 min    |
| 🔹 P1    | Update **ROADMAP.md** v0.3.0 section with revised deliverables                         | Roadmap reflects pre-work + implementation     | 30 min    |
| 🔹 P2    | Implement `src/srd_builder/extract_monsters.py` (start with 1 monster extraction)      | Working baseline, progressively tested         | 4-6 hours |
| 🔹 P3    | Integrate extraction into `build.py` (call before parse_monsters)                      | End-to-end pipeline functional                 | 1 hour    |
| 🔹 P4    | Add `tests/extract/test_extract_basic.py` with snapshot fixtures                       | Enforces determinism, prevents regressions     | 2 hours   |

**Critical Path:** P0 tasks block P2 implementation. P1 tasks can run parallel to P0.

### Phase 3: Validation (After Extraction Working)

| Priority | Task                                                                                    | Outcome                                        |
| -------- | --------------------------------------------------------------------------------------- | ---------------------------------------------- |
| 🔹 P5    | Run extraction, compare monster names vs reference JSON                                | Validate ≥95% recall rate                      |
| 🔹 P6    | Review extraction warnings, fix boundary detection issues                              | Reduce false positives/negatives               |
| 🔹 P7    | Tag v0.3.0 when exit criteria met                                                      | Milestone complete, ready for v0.4.0 parsing   |

---

## 📝 Appendix: Open Question Status Tracker

### A. Extraction Scope & Strategy
1. Targeted extraction (monsters only, pages 302-384?) vs whole-PDF extraction? — **Status:** Resolved. **Guidance:** Build targeted extractor now; keep APIs page-range agnostic so whole-PDF becomes a config change.
2. What exact page range contains monsters in SRD 5.1? — **Status:** Blocking. **Next step:** Manual confirmation still required (Quick Win #1).
3. How to detect section boundaries if doing whole-PDF? — **Status:** Nice-to-have. **Guidance:** Reuse header heuristics + keyword anchors; revisit when expanding scope beyond monsters.

### B. Boundary Detection
4. What font size threshold distinguishes monster names from body text? — **Status:** Pending measurement. **Expectation:** Header spans ≈13–16 pt vs body 8–9 pt; confirm via `scripts/explore_pdf.py`.
5. What if monster names use same font as body text? — **Status:** Resolved. **Guidance:** Combine type-line detection with uppercase/no-indent heuristics; fall back to keyword anchors.
6. How to handle monster name variants like "Adult Black Dragon (Variant)"? — **Status:** Resolved. **Guidance:** Treat entire first span before type-line as header; parser can trim variant notes later.
7. Do ALL monsters have the "size, type, alignment" pattern? — **Status:** High confidence. **Guidance:** Expect yes; record warning if missing to catch anomalies.
8. Fallback strategy if both font-size AND pattern matching fail? — **Status:** Resolved. **Guidance:** Default to previous header boundary + keyword search (`Armor Class`) and emit warning.

### C. Two-Column Layout
9. What X-coordinate threshold divides columns? — **Status:** Pending measurement. **Guidance:** Derive midpoint per page from `page.rect.width`; default ≈306 pt.
10. How to handle monsters spanning multiple columns/pages? — **Status:** Resolved. **Guidance:** Duplicate spans that cross midpoint, merge using y-order, and flag with warning.
11. Do all monster pages use two columns? (title pages may differ) — **Status:** Resolved. **Guidance:** Detect by variance of `bbox[0]`; if single cluster, set `column=0` for entire page.
12. PyMuPDF: `layout=True` vs `sort=True` vs manual bbox sorting? — **Status:** Resolved. **Guidance:** Use `page.get_text("dict")`/`TextPage.extractDICT()`; avoid layout/sort flags.
13. Should we store bbox data in raw JSON for debugging? — **Status:** Resolved. **Guidance:** Yes, keep `[x0,y0,x1,y1]` per span.
14. How to validate correct column ordering (left→right)? — **Status:** Resolved. **Guidance:** Sort by `(page, column, y, x)` and compare monster order against reference names.

### D. Raw JSON Schema Design
15. Block-level, line-level, or word-level granularity? — **Status:** Resolved. **Guidance:** Use span-level records (PyMuPDF spans).
16. Capture font names or just sizes? — **Status:** Resolved. **Guidance:** Capture both `font` and `size` for future heuristics.
17. Store exact PDF coordinates or just relative ordering? — **Status:** Resolved. **Guidance:** Store full `bbox` for reproducibility + debugging.
18. Should sections be auto-detected or left for v0.4.0 parser? — **Status:** Deferred. **Guidance:** Record marker indices now; build structured sections during v0.4.0.
19. What metadata: page, column, bbox, font, warnings? — **Status:** Resolved. **Guidance:** Use schema draft (`page`, `column`, `bbox`, `text`, `font`, `size`, `color`, `flags`, `is_header`, `warnings`).

### E. Reference JSON Usage
20. What's the structure of the 14MB tabyltop JSON? — **Status:** High confidence. **Guidance:** Flat list of entries with `category`/`content`; confirm via script when run.
21. Can we trust it as ground truth, or just a comparison point? — **Status:** Resolved. **Guidance:** Treat as comparison baseline only; do not overwrite SRD text with it.
22. How many monsters are in it? (establishes baseline count) — **Status:** Pending script execution. **Guidance:** `scripts/analyze_reference.py` prints count; add to docs once run.
23. Should we validate during extraction (v0.3.0) or normalization (v0.4.0)? — **Status:** Resolved. **Guidance:** Run recall metric in v0.3.0 as advisory; enforce thresholds alongside normalization in v0.4.0.

### F. Bridge Strategy
24. What does current `parse_monsters.py` expect as input? — **Status:** Resolved. **Guidance:** Expects normalized dicts matching fixtures; cannot ingest raw spans directly.
25. Can we make it work with raw extraction, or need preprocessing? — **Status:** Blocking. **Guidance:** Provide bridge transformer `raw_monsters.json` → existing parser until v0.4 rewrite.
26. Extract → raw JSON → bridge JSON → parser? Or update parser? — **Status:** Resolved. **Guidance:** Use bridge pipeline for v0.3; update parser in v0.4.
27. Should v0.3.0 include basic field parsing to generate compatible bridge? — **Status:** Resolved. **Guidance:** Only parse fields needed for compatibility (name, stats skeleton); leave deep parsing to v0.4.

### G. Module Structure
28. `src/srd_builder/extract_monsters.py` (simple) vs `src/srd_builder/extract/pdf_monsters.py` (package)? — **Status:** Resolved. **Guidance:** Start with single module for v0.3; migrate to package once multiple extractors exist.
29. When to refactor from simple module to package structure? — **Status:** Deferred. **Guidance:** Target v0.5 when spells/items join pipeline.

### H. Configuration Management
30. Hardcode extraction params (v0.3.0) or use config file? — **Status:** Resolved. **Guidance:** Hardcode for v0.3; move to config in v0.4+.
31. If config: YAML or JSON? — **Status:** Resolved. **Guidance:** Prefer YAML for readability; load via `yaml.safe_load` once introduced.
32. Where do defaults live: code or base config? — **Status:** Resolved. **Guidance:** Defaults in code (dataclass) with optional overrides from ruleset config.
33. How to handle "auto" page detection for future rulesets? — **Status:** Deferred. **Guidance:** Implement when second ruleset lands; likely need ToC scanning or reference anchors.

### I. Visualization & Debugging
34. Use PyMuPDF annotation vs Pillow/matplotlib for bbox visualization? — **Status:** Deferred. **Guidance:** Defer to v0.4; prefer generating PNG overlays via PyMuPDF annotations when needed.
35. CLI flag or separate script? — **Status:** Resolved. **Guidance:** Separate `scripts/visualize_extraction.py` when implemented; keep extractor lean.
36. Worth implementing in v0.3.0 or defer to v0.4.0? — **Status:** Resolved. **Guidance:** Defer; not required for MVP.

### J. v0.4.0 Normalization Fidelity
37. How to handle edge cases like "Lair Actions" vs "Legendary Actions"? — **Status:** Pending design. **Guidance:** Plan for state-machine parser with section keywords; not required for v0.3.
38. Non-standard sections like "Variant:" blocks? — **Status:** Pending design. **Guidance:** Preserve raw ordering now; let parser categorize via heuristics later.
39. Regex-based or ML-based dehyphenation? — **Status:** Resolved (direction). **Guidance:** Start regex-based (join hyphen + newline) and revisit ML only if accuracy suffers.
40. Bulleted lists vs comma-separated lists? — **Status:** Pending design. **Guidance:** Capture raw bullet markers; parser to interpret using regex + indentation cues.
41. What if reference JSON is wrong? Validate the validator how? — **Status:** Resolved. **Guidance:** Spot check vs SRD PDF; treat disagreements as warnings unless corroborated.
42. Prioritize correctness over coverage? — **Status:** Resolved. **Guidance:** Correctness first; track coverage separately.
43. Migration path: keep `parse_monsters_legacy.py` during transition? — **Status:** Resolved. **Guidance:** Keep legacy parser as fallback until normalized pipeline proven in v0.4.

### K. v0.5.0 Cross-Ruleset Support
44. How different are Pathfinder layouts vs D&D 5e? — **Status:** Research needed. **Guidance:** Gather sample PDFs during v0.5 planning.
45. Can we abstract "two-column monster stat block" as universal pattern? — **Status:** Hypothesis. **Guidance:** Likely yes for d20 systems; confirm with Pathfinder/ORC artifacts.
46. What about non-Latin scripts or RTL languages? — **Status:** Deferred. **Guidance:** Requires additional shaping libraries (e.g., HarfBuzz); out of scope for SRD 5.1.
47. Config-driven (Option A), subclasses (Option B), or plugins (Option C)? — **Status:** Resolved. **Guidance:** Start config-driven; refactor to subclasses only if configs become unmanageable.

### L. Optional Enhancements
48. Is extraction CPU-bound or I/O-bound? (affects parallel strategy) — **Status:** Resolved. **Guidance:** Mostly CPU-bound but fast (<5 min); no parallelization needed yet.
49. How to handle cross-page monsters in parallel extraction? — **Status:** Resolved (direction). **Guidance:** Avoid parallelization until chunking logic can stitch cross-page spans; treat as future optimization.
50. Does chunked rebuild actually save time? — **Status:** Low priority. **Guidance:** Likely not worth complexity until PDFs exceed hundreds of MB.
51. How to invalidate chunks when PDF changes? — **Status:** Resolved (direction). **Guidance:** Use PDF SHA-256 + page numbers to invalidate cached chunks.
52. Quality threshold before triggering OCR fallback? — **Status:** Deferred. **Guidance:** Add once targeting scanned PDFs; rule of thumb = text coverage < 90%.
53. Is metrics dashboard worth the complexity? — **Status:** Nice-to-have. **Guidance:** Revisit after extraction + normalization stabilize (v0.6+).


## 🎯 Next Steps for User

1. Execute Phase 1 scripts (font exploration, reference analysis) and capture outputs under `docs/reference/`.
2. Finalize `schemas/raw_monster.schema.json` using the draft above and add JSON Schema validation to local dev checklist.
3. Implement the single-monster extraction proof of concept to validate ordering, schema compliance, and determinism.
4. Draft bridge transformer interface so `parse_monsters.py` continues to work during v0.3 rollout.
5. Update ROADMAP/EXTRACTION_CHALLENGES with resolved decisions from this document to keep planning artifacts aligned.

