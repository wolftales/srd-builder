# PDF Extraction Challenges & Decisions (v0.3.0)

## Context

**Goal:** Extract monster stat blocks from `SRD_CC_v5.1.pdf` and produce structured JSON matching our current pipeline input format.

**Philosophy:** "If there are problems, I want them to be my problems" - own the extraction, don't rely on someone else's data.

**Available Resources:**
- Source PDF: `rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf`
- Raw unprocessed JSON: 14MB file from previous extraction (bootstrap reference)
- Current fixture: 6 monsters in `tests/fixtures/srd_5_1/raw/monsters.json`
- Working pipeline: Parse → Postprocess → Index → Validate

---

## Critical Questions

### 1. **Monster Boundary Detection**

**Challenge:** How do we identify where one monster starts and another ends in the PDF?

**Potential Approaches:**
- **Header detection** - Look for monster name in large/bold font at top
- **Pattern matching** - "Size Type, Alignment" pattern (e.g., "Huge dragon, chaotic evil")
- **Page structure** - Assume monsters don't split across columns (validate this)
- **Blank space** - Significant whitespace between monsters
- **Font changes** - Monster names typically in different font/size

**Questions:**
- Are all monster names consistently formatted?
- Do any monsters span multiple columns or pages?
- Are there non-monster sections we need to skip?
- How do we handle variant monsters (e.g., "Adult Black Dragon (Variant)")?

**Decision needed:** Primary + fallback detection strategy

---

### 2. **Text Extraction Strategy**

**Challenge:** PyMuPDF offers multiple extraction modes - which gives best results?

**Options:**

**A) Block-based (`page.get_text("blocks")`)**
```python
# Returns: (x0, y0, x1, y1, "text", block_no, block_type)
# Pro: Preserves layout, good for multi-column
# Con: May break mid-word on columns
```

**B) Line-based (`page.get_text("dict")` → lines)**
```python
# Returns structured dict with spans, fonts, positions
# Pro: Fine-grained control, font info available
# Con: More complex to reconstruct blocks
```

**C) Text-based (`page.get_text("text")`)**
```python
# Returns plain text string
# Pro: Simplest
# Con: Loses all positioning/layout info
```

**Questions:**
- Do monsters span multiple columns consistently?
- Are stat block sections (AC, HP, Actions) consistently positioned?
- Can we use coordinates to separate columns?

**Decision needed:** Extraction mode + reconstruction approach

---

### 3. **Field Parsing Strategy**

**Challenge:** Convert extracted text into structured fields.

**Example Raw Text:**
```
Adult Black Dragon
Huge dragon, chaotic evil
Armor Class 19 (natural armor)
Hit Points 195 (17d12 + 85)
Speed 40 ft., fly 80 ft., swim 40 ft.
STR  DEX  CON  INT  WIS  CHA
23   14   21   14   13   17
(+6) (+2) (+5) (+2) (+1) (+3)
```

**Approaches:**

**A) Regex-based parsing**
```python
ac_match = re.search(r"Armor Class (\d+)", text)
hp_match = re.search(r"Hit Points (\d+) \(([^)]+)\)", text)
```
- Pro: Fast, explicit patterns
- Con: Brittle, needs pattern for every field

**B) Structured parsing (state machine)**
```python
# Track current section: header, stats, traits, actions, etc.
# Parse based on current state
```
- Pro: Handles variations better
- Con: More complex

**C) Hybrid (sections + regex)**
```python
# Split into sections (Traits, Actions, Legendary Actions)
# Use regex within each section
```
- Pro: Balanced flexibility/simplicity
- Con: Needs section detection

**Questions:**
- How consistent is the field ordering?
- Are there optional fields that appear inconsistently?
- How do we handle special cases (legendary actions, lair actions)?

**Decision needed:** Parsing approach + error handling strategy

---

### 4. **Quality & Validation**

**Challenge:** How do we know if extraction was successful?

**Validation Levels:**

**Level 1 - Structural Validation**
- Required fields present (name, size, type, AC, HP, etc.)
- Field types correct (integers for AC/HP, strings for names)
- Schema validation passes

**Level 2 - Semantic Validation**
- Ability scores in valid range (3-30)
- CR matches expected progression
- Action attack bonuses reasonable for CR

**Level 3 - Cross-validation**
- Compare against raw 14MB JSON (if available)
- Compare against test fixtures
- Manual spot-check of known monsters

**Questions:**
- What's our acceptable error rate? (100% perfect? 95%? 90%?)
- Do we fail the whole build if one monster fails, or skip it?
- How do we report extraction issues?

**Decision needed:** Quality threshold + error handling policy

---

### 5. **Fallback & Hybrid Strategies**

**Challenge:** What if extraction fails or is partial?

**Options:**

**A) All-or-nothing**
- Extract all monsters or fail
- Pro: Clean, deterministic
- Con: Brittle, one bad monster blocks everything

**B) Best-effort with reporting**
- Extract what we can, log failures
- Pro: Partial success better than none
- Con: Non-deterministic output

**C) Hybrid fixture + extraction**
- Use fixtures for known-problematic monsters
- Extract the rest
- Pro: Practical, progressive improvement
- Con: Defeats "own our problems" philosophy

**D) Two-phase extraction**
- Phase 1: Extract to raw JSON (like 14MB file)
- Phase 2: Parse/normalize (current pipeline)
- Pro: Can iterate on Phase 2 independently
- Con: Extra intermediate format

**Questions:**
- Should extraction be part of build, or a separate tool?
- Do we version the extracted raw JSON?
- How do we handle PDF updates/errata?

**Decision needed:** Extraction architecture + failure handling

---

## Testing Strategy

**Progressive Approach:**

### Phase 1 - Single Monster Prototype
1. Extract "Adult Black Dragon" from PDF
2. Compare to fixture JSON
3. Iterate on extraction logic
4. Document challenges encountered

### Phase 2 - Small Set (6 monsters)
1. Extract all fixture monsters
2. Run through current pipeline
3. Compare output to golden tests
4. Measure accuracy/completeness

### Phase 3 - Full Extraction
1. Extract all monsters from PDF
2. Validate against 14MB raw JSON (if structure matches)
3. Run full test suite
4. Measure performance (time, memory)

---

## Technical Constraints

**Must maintain:**
- Deterministic output (same PDF → same JSON, every time)
- Schema compliance (`monster.schema.json`)
- Pipeline compatibility (output must work with current parse/postprocess)
- No timestamps in output files

**Performance targets:**
- Build time: < 30 seconds for full extraction
- Memory: < 500MB peak
- CPU: Single-threaded acceptable

---

## Open Questions for Team Discussion

1. **Detection:** Header-based or pattern-based monster boundaries?
2. **Extraction:** Block, line, or hybrid text extraction?
3. **Parsing:** Regex, state machine, or hybrid approach?
4. **Quality:** What's acceptable error rate? How to handle failures?
5. **Architecture:** Integrated build step or separate extraction tool?
6. **Validation:** How to use 14MB raw JSON for validation?
7. **Iteration:** Extract raw first, or parse immediately?
8. **Edge cases:** How to handle lair actions, regional effects, variants?

---

## Next Steps

1. **Team decision session** - Discuss above questions, pick approaches
2. **Prototype extraction** - Implement single-monster extraction
3. **Validate approach** - Test against fixtures
4. **Scale to full** - Extract all monsters
5. **Document patterns** - Record what worked/didn't work

---

## Resources

- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [SRD 5.1 Monster Section](https://dnd.wizards.com/resources/systems-reference-document)
- Current pipeline: `src/srd_builder/build.py`
- Test fixtures: `tests/fixtures/srd_5_1/raw/monsters.json`
