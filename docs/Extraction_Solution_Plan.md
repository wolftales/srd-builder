# PDF Extraction Solution Plan (v0.3.0)

> **Status:** Enhanced with critical questions and decision points
> **Last Updated:** Post-GPT review + Claude analysis
> **Philosophy:** "Select the best path forward, not just the easy path"

---

## 🚨 Executive Summary: Critical Decisions Needed

Before implementing v0.3.0, we must answer these foundational questions:

### 1. **Extraction Scope** (BLOCKING)
- [ ] Targeted monsters section (pages 302-384?) vs. whole-PDF extraction
- [ ] Document exact monster section page range in SRD 5.1
- [ ] Decision impacts: speed, reusability, maintainability

### 2. **Raw JSON Schema** (BLOCKING)
- [ ] Define exact structure of `monsters_raw.json`
- [ ] Granularity: block-level, line-level, or word-level?
- [ ] Metadata: bbox coords, font info, column markers?
- [ ] Create `schemas/raw_monster.schema.json` BEFORE coding

### 3. **Reference Data Strategy** (BLOCKING)
- [ ] How to use 14MB `srd_cc_v5.1_rules_tabyltop.json`?
- [ ] Extract monster names/count for validation
- [ ] Trust as ground truth or just comparison baseline?
- [ ] Create `scripts/analyze_reference.py` for inspection

### 4. **PDF Layout Analysis** (BLOCKING)
- [ ] What font size threshold distinguishes headers? (Measure actual PDF)
- [ ] What X-coordinate divides columns? (Measure actual PDF)
- [ ] Test PyMuPDF extraction options: `layout=True` vs `sort=True`
- [ ] Create `scripts/explore_pdf.py` for experimentation

### 5. **Bridge Strategy** (Design Decision)
- [ ] How to connect extraction → existing parser?
- [ ] Option A: Extract → `monsters_raw.json` → `monsters.json` (bridge)
- [ ] Option B: Update `parse_monsters.py` to read raw format directly
- [ ] Impacts v0.3.0 scope and v0.4.0 refactoring

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
| **Boundary detection**   | Combine text + font data. Detect headers by *font-size spikes* and confirm with the canonical "size, type, alignment" line. Maintain fallback to section markers (`Armor Class`, `Hit Points`, etc.). | More robust than line-only parsing; less false positives than regex-only approaches. Gives repeatable boundaries even if PDF fonts shift slightly. |

**Open Questions for Boundary Detection:**
- What font size threshold? (Need to analyze PDF to determine)
- What if monster name uses same font as body text? (Some PDFs do this)
- How to handle variants like "Adult Black Dragon (Variant)"?
- Do all monsters have the "size, type, alignment" pattern? (Need verification)
- Fallback strategy if both methods fail?

**Action Required:** Write exploratory script to analyze font sizes/styles in monsters section.

| **Two-column layout**    | Use PyMuPDF's structured "dict" output (blocks/spans) and compute two-column thresholds per page.                                                                                                     | Handles SRD column breaks deterministically; no layout heuristics or line-wrap confusion.                                                          |

**Open Questions for Two-Column Handling:**
- What is the X-coordinate threshold for column boundaries? (Need to measure)
- How do we handle monsters that span column boundaries mid-stat-block?
- What about single-column title pages or full-width content?
- Should we store bounding box data in raw JSON for debugging?
- How to validate correct column ordering? (Left→Right expected)

**Action Required:** Analyze page layouts in monsters section; test PyMuPDF dict/blocks extraction.
| **Output structure**     | Save a "verbatim + metadata" format (`monsters_raw.json`): each monster keeps ordered text blocks, page/column data, and section offsets.                                                             | Separates *capture* from *parsing*. Enables diffing, re-extraction, and incremental parser improvements without re-scraping the PDF.               |

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
| **Parsing depth**        | v0.3.0 = surface capture (no field parsing); v0.4.0 = structured parsing via section-state machine.                                                                                                   | Keeps milestones clean. Extraction is validated independently of normalization.                                                                    |
| **Error handling**       | Always succeed if ≥1 monster extracted. Record `extraction_warnings` per monster and a top-level `extraction_report`.                                                                                 | Prevents total-pipeline failure while maintaining auditability.                                                                                    |
| **Determinism**          | Sort lines by (page, y, x). Normalize whitespace/hyphenation. Embed PDF SHA-256 in `_meta`.                                                                                                           | Allows byte-identical re-runs, enabling CI regression tests and caching.                                                                           |
| **Incremental builds**   | Re-extract only if `pdf_sha256` differs from saved `meta.json`.                                                                                                                                       | Prevents unnecessary reprocessing during repeated builds.                                                                                          |
| **Extensibility**        | Keep raw JSON schema minimal and generic: `name`, `pages`, `blocks`, `sections`, `markers`, `warnings`.                                                                                               | Works for monsters now, spells/classes later, and for SRD 5.2.1 / Pathfinder ORC.                                                                  |
| **Testing & validation** | Snapshot test small PDFs; add coverage metric comparing extracted monster names against reference dataset.                                                                                            | Converts "qualitative correctness" into measurable regression metric.                                                                              |

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
| � P0    | **Find monster section page range** in SRD_CC_v5.1.pdf (manual inspection)             | Document exact pages (e.g., 302-384)           | 30 min    |
| 🔴 P0    | **Analyze reference JSON** (`scripts/analyze_reference.py`)                            | Monster count, name list, structure understanding | 1 hour  |
| 🔴 P0    | **Define raw JSON schema** (`schemas/raw_monster.schema.json`)                         | Clear contract for extraction output           | 1 hour    |
| 🔴 P0    | **Explore PDF with PyMuPDF** (`scripts/explore_pdf.py`)                                | Font sizes, column boundaries, layout options  | 2 hours   |

**Why P0?** Cannot write extractor without knowing: where monsters are, what success looks like, what output format is, how PDF is structured.

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

## 📝 Appendix: All Open Questions Consolidated

### A. Extraction Scope & Strategy
1. Targeted extraction (monsters only, pages 302-384?) vs whole-PDF extraction?
2. What exact page range contains monsters in SRD 5.1?
3. How to detect section boundaries if doing whole-PDF?

### B. Boundary Detection
4. What font size threshold distinguishes monster names from body text?
5. What if monster names use same font as body text?
6. How to handle monster name variants like "Adult Black Dragon (Variant)"?
7. Do ALL monsters have the "size, type, alignment" pattern?
8. Fallback strategy if both font-size AND pattern matching fail?

### C. Two-Column Layout
9. What X-coordinate threshold divides columns?
10. How to handle monsters spanning multiple columns/pages?
11. Do all monster pages use two columns? (title pages may differ)
12. PyMuPDF: `layout=True` vs `sort=True` vs manual bbox sorting?
13. Should we store bbox data in raw JSON for debugging?
14. How to validate correct column ordering (left→right)?

### D. Raw JSON Schema Design
15. Block-level, line-level, or word-level granularity?
16. Capture font names or just sizes?
17. Store exact PDF coordinates or just relative ordering?
18. Should sections be auto-detected or left for v0.4.0 parser?
19. What metadata: page, column, bbox, font, warnings?

### E. Reference JSON Usage
20. What's the structure of the 14MB tabyltop JSON?
21. Can we trust it as ground truth, or just a comparison point?
22. How many monsters are in it? (establishes baseline count)
23. Should we validate during extraction (v0.3.0) or normalization (v0.4.0)?

### F. Bridge Strategy
24. What does current `parse_monsters.py` expect as input?
25. Can we make it work with raw extraction, or need preprocessing?
26. Extract → raw JSON → bridge JSON → parser? Or update parser?
27. Should v0.3.0 include basic field parsing to generate compatible bridge?

### G. Module Structure
28. `src/srd_builder/extract_monsters.py` (simple) vs `src/srd_builder/extract/pdf_monsters.py` (package)?
29. When to refactor from simple module to package structure?

### H. Configuration Management
30. Hardcode extraction params (v0.3.0) or use config file?
31. If config: YAML or JSON?
32. Where do defaults live: code or base config?
33. How to handle "auto" page detection for future rulesets?

### I. Visualization & Debugging
34. Use PyMuPDF annotation vs Pillow/matplotlib for bbox visualization?
35. CLI flag or separate script?
36. Worth implementing in v0.3.0 or defer to v0.4.0?

### J. v0.4.0 Normalization Fidelity
37. How to handle edge cases like "Lair Actions" vs "Legendary Actions"?
38. Non-standard sections like "Variant:" blocks?
39. Regex-based or ML-based dehyphenation?
40. Bulleted lists vs comma-separated lists?
41. What if reference JSON is wrong? Validate the validator how?
42. Prioritize correctness over coverage?
43. Migration path: keep `parse_monsters_legacy.py` during transition?

### K. v0.5.0 Cross-Ruleset Support
44. How different are Pathfinder layouts vs D&D 5e?
45. Can we abstract "two-column monster stat block" as universal pattern?
46. What about non-Latin scripts or RTL languages?
47. Config-driven (Option A), subclasses (Option B), or plugins (Option C)?

### L. Optional Enhancements
48. Is extraction CPU-bound or I/O-bound? (affects parallel strategy)
49. How to handle cross-page monsters in parallel extraction?
50. Does chunked rebuild actually save time?
51. How to invalidate chunks when PDF changes?
52. Quality threshold before triggering OCR fallback?
53. Is metrics dashboard worth the complexity?

---

## 🎯 Next Steps for User

**Recommendation:** Focus on Phase 1 (Research & Design) first:

1. **Create `scripts/explore_pdf.py`** - Analyze font sizes, column boundaries, layout
2. **Create `scripts/analyze_reference.py`** - Extract monster list from 14MB JSON
3. **Create `schemas/raw_monster.schema.json`** - Define extraction output format
4. **Document monster page range** - Manual inspection of SRD 5.1

These four artifacts will answer 20+ of the 53 open questions and unblock implementation.

**After that:** Proceed with extraction implementation using evidence-based decisions rather than guesses.

---

## 🤖 Collaboration Notes

**Review History:**
- GPT: Initial solution plan (technical approach, architecture, roadmap)
- Claude: Added 53 critical questions, decision points, pre-work phase
- Codex: [PENDING] - Review technical approach, validate Python implementation strategy
- Gemini: [DEFERRED to Phase 1 completion] - Evidence-based validation with actual PDF data

**Current Status:** Ready for Codex review focusing on implementation practicality and tooling.
