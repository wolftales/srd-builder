# Extraction Quality Comparison

This document compares the extraction approaches and results across different implementations.

## Methodology Comparison

### TabylTop (Community Tool)
- **Source:** PDF text extraction
- **Method:** Scraping with custom parsing
- **Output:** Pre-parsed JSON with field values
- **Coverage:** 319 entries (includes NPCs, appendices, conditions, chapter headers)
- **Metadata:** Minimal (page numbers only)
- **Limitations:**
  - Early normalization loses context
  - No font/layout information
  - Flattened structure
  - Mixed monster and non-monster content

### Previous MVP Implementation
- **Source:** TabylTop's JSON output (secondary source)
- **Method:** Normalize pre-parsed data
- **Output:** Schema-compliant monsters.json
- **Coverage:** 201 monsters normalized
- **Metadata:** Standard schema fields
- **Achievement:**
  - Established stable JSON schema
  - Validated output structure
  - Proved normalization pipeline

### SRD-Builder v0.3.0 (Current)
- **Source:** Direct PDF extraction (primary source)
- **Method:** Font-aware text block extraction with layout analysis
- **Output:** Rich metadata + schema-compliant final output
- **Coverage:** 296 monsters from Monster Manual section (pages 261-394)
- **Metadata:**
  - Font information (name, size, color, flags)
  - Layout data (column, bounding box, positioning)
  - Page numbers per monster
  - Verbatim text blocks with formatting preserved
  - Multiple blocks per monster (not flattened)
- **Achievement:**
  - ✅ First-class PDF extraction (no TabylTop dependency)
  - ✅ +95 monsters vs previous implementation (+47% coverage)
  - ✅ Rich metadata enables smarter parsing decisions
  - ✅ Deterministic extraction with PDF hash tracking
  - ✅ Zero extraction warnings across all monsters
  - ✅ Validated against 8 known monster categories

## Quality Metrics

### Data Richness

| Feature | TabylTop | Previous MVP | SRD-Builder v0.3.0 |
|---------|----------|--------------|-------------------|
| Font metadata | ❌ | ❌ | ✅ NEW |
| Layout info | ❌ | ❌ | ✅ NEW |
| Page numbers | ✅ | ✅ | ✅ |
| Verbatim text | Partial | ❌ | ✅ Better |
| Block structure | ❌ Flattened | ❌ | ✅ NEW |
| PDF source | ✅ Primary | ❌ Secondary | ✅ Primary |

### Coverage

| Metric | TabylTop | Previous MVP | SRD-Builder v0.3.0 |
|--------|----------|--------------|-------------------|
| Total entries | 319* | 201 | 296 |
| Actual monsters | ~296** | 201 | 296 |
| Duplicates | Unknown | 0 | 0 |
| Non-monsters | ~23* | 0 | 0 |

\* TabylTop's 319 includes NPCs (page 60), appendix titles, conditions, and chapter headers
\*\* Estimated actual monster count after filtering non-monsters

### Validation

| Check | TabylTop | Previous MVP | SRD-Builder v0.3.0 |
|-------|----------|--------------|-------------------|
| Category completeness | ❓ | ✅ | ✅ Automated |
| Uniqueness verification | ❓ | ✅ | ✅ Automated |
| Count validation | ❓ | ✅ | ✅ Automated |
| Extraction warnings | ❓ | N/A | ✅ 0 warnings |

## Schema Evolution

The JSON schema established during previous development has proven robust:

**Schema Fields (Required):**
- `id`, `name`, `simple_name`
- `armor_class`, `hit_points`, `ability_scores`, `actions`

**Schema Fields (Optional):**
- `challenge_rating`, `page`, `saving_throws`, `senses`, `skills`, `speed`, `xp_value`

**Key Design Decision:**
- Rich extraction metadata (fonts, layout, blocks) stays in intermediate `monsters_raw.json`
- Final output (`monsters.json`) remains schema-compliant
- Parser uses rich metadata for better decisions, but output structure stays stable

**Future Considerations:**
- Enhanced parsing may reveal opportunities for schema extensions
- Current schema uses `additionalProperties: true` allowing non-breaking additions
- Any breaking changes would require major version bump

## Pipeline Architecture

### Previous Flow (TabylTop → MVP)
```
TabylTop PDF extraction
    ↓
TabylTop JSON (pre-parsed fields)
    ↓
Load + normalize
    ↓
monsters.json (201 monsters)
```

### Current Flow (SRD-Builder v0.3.0)
```
SRD PDF (primary source)
    ↓
extract_monsters.py (font-aware extraction)
    ↓
monsters_raw.json (296 monsters, rich metadata)
    ↓
parse_monsters.py (block parsing) ← IN PROGRESS
    ↓
postprocess.py (normalization)
    ↓
monsters.json (schema-compliant output)
```

## Achievements

### v0.3.0 Milestones ✅

1. **Direct PDF Extraction**
   - Eliminated TabylTop dependency
   - First-class source document processing
   - Deterministic extraction with hash tracking

2. **Enhanced Data Quality**
   - Font and layout metadata for context-aware parsing
   - Preserved text formatting (tabs, whitespace)
   - Block structure maintained (not flattened)

3. **Improved Coverage**
   - 296 monsters (vs 201 previously, +47%)
   - Focused on actual Monster Manual content (pages 261-394)
   - Excludes non-monster entries (NPCs, appendices, conditions)

4. **Validation Framework**
   - Automated category completeness checks
   - Count validation with expected ranges
   - Uniqueness verification
   - Zero extraction warnings

5. **Build Integration**
   - Extraction runs automatically during build
   - Backward compatible with legacy formats
   - Comprehensive metadata tracking

## Next Steps

### Parser Enhancement (In Progress)
- Update `parse_monsters.py` to read blocks array
- Leverage font/layout metadata for smarter field detection
- Maintain schema compliance while improving accuracy

### Testing
- Extraction tests with fixtures
- Cross-page monster validation
- Column detection verification

### Future Enhancements
- Dynamic page range detection
- Additional entity types (equipment, spells, etc.)
- Schema extensions based on improved parsing capabilities

---

*This comparison demonstrates the progression from secondary-source processing to primary-source extraction with enhanced metadata, positioning SRD-Builder as a comprehensive PDF-to-JSON pipeline for the D&D 5e SRD.*
