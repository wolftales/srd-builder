# Phase 1 Research Findings - Quick Reference

> **For Gemini Review:** Hard data from actual PDF analysis

---

## 🎯 PDF Typography (from `explore_pdf.py`)

### Page 302-305 Analysis:

**Monster Name Headers:**
```
GillSans-SemiBold @ 18.0pt  (main monster names)
GillSans-SemiBold @ 13.92pt (variant/sub-monsters)
```

**Section Headers (Actions, Traits, etc):**
```
Calibri-Bold @ 12.0pt
```

**Body Text:**
```
Calibri @ 9.84pt      (vast majority - 3,784-5,006 chars/page)
Calibri-Bold @ 9.84pt (inline emphasis - 159-511 chars/page)
Calibri-Italic @ 9.84pt (inline emphasis - 127-311 chars/page)
```

**Layout:**
```
Page midpoint:    306.0 pt (exact, all pages)
Left column avg:  88.74 - 97.4 pt
Right column avg: 349.19 - 373.68 pt
```

---

## 📊 Reference Dataset (from `analyze_reference.py`)

**TabylTop Raw JSON Structure:**
```json
{
  "total_entries": 13353,     // Whole PDF
  "monster_count": 562,       // Headers found (includes "Actions" sections)
  "unique_monster_names": 319 // Actual distinct monsters
}
```

**Sample Monster Names Extracted:**
- Acolyte
- Adult Silver Dragon
- Air Elemental
- Ancient Silver Dragon
- Androsphinx
- Ape
- [... 313 more]

**Monster Section:**
- Starts: Page 300+
- Format: h1/h2/h3/h4 headings with subelements containing text
- Note: TabylTop extracted entire PDF as generic structure

---

## 🔍 Key Observations

### Font Size Thresholds:
```
18.0pt   → Definitely a monster name header
13.92pt  → Likely a variant or sub-monster
12.0pt   → Section header (Actions, Legendary Actions)
9.84pt   → Body text
```

**Detection Strategy Validation:**
- ✅ Font size spike (18pt vs 9.84pt = ~2x) is reliable
- ✅ Type-line pattern ("Large aberration, lawful evil") present
- ⚠️ Need to handle 13.92pt variants
- ⚠️ GillSans-SemiBold font name confirms header type

### Column Detection:
```
Midpoint at 306pt is mathematically sound:
- Left column centers around ~90pt
- Right column centers around ~365pt
- Page width: 612pt (US Letter)
- 612 / 2 = 306pt ✓
```

**Detection Strategy Validation:**
- ✅ Fixed midpoint works across all sampled pages
- ✅ Clear X-coordinate separation
- ⚠️ Need to handle cross-column stat blocks (rare but possible)

### Reference JSON Insights:
```
TabylTop = Whole PDF dump, no semantic parsing
Our approach = Targeted extraction + parsing

TabylTop useful for:
✅ Monster name validation (recall metric)
✅ Page range confirmation
✅ Count baseline (expect ~319 monsters)

TabylTop NOT useful for:
❌ Field structure (no parsing done)
❌ Schema validation (generic format)
❌ Quality comparison (incompatible formats)
```

---

## ⚠️ Edge Cases Identified

### From Font Analysis:
1. **Variant names:** 13.92pt headers (e.g., "Adult Silver Dragon (Variant)")
2. **Multi-font pages:** Page 305 has GillSans @ 18pt, 13.92pt, 10.8pt
3. **Section headers:** "Actions" appears as h4 in reference (could be mistaken for monster)

### From Reference JSON:
1. **Duplicate section names:** "Actions" appears 562 times (once per monster)
2. **Non-monster headers:** "Appendix MM-B: Nonplayer Characters"
3. **Whitespace in names:** Some entries have trailing spaces

### Potential Issues:
- ❓ Single-column title pages (if any)
- ❓ Monsters spanning multiple pages
- ❓ Legendary actions formatting variations
- ❓ Lair actions / Regional effects sections

---

## ✅ Validation Checklist for Gemini

**Header Detection:**
- [ ] 18pt threshold appropriate?
- [ ] How to handle 13.92pt variants?
- [ ] Fallback if font detection fails?

**Column Splitting:**
- [ ] 306pt midpoint correct?
- [ ] Handling cross-column blocks?
- [ ] Single-column page detection?

**Schema Completeness:**
- [ ] Need `font_size` field in blocks?
- [ ] Should we store `font_name`?
- [ ] Is `color` array necessary?
- [ ] Need `confidence` score?

**Reference Validation:**
- [ ] 319 monster count reasonable?
- [ ] Page 300+ range correct?
- [ ] How to filter "Actions" false positives?

---

## 📈 Next Steps After Gemini Review

**If 🟢 Green:**
→ Proceed to Phase 2: Implement `extract_monsters.py`

**If 🟡 Yellow:**
→ Address cautions, then proceed with monitoring

**If 🔴 Red:**
→ Additional research needed before implementation

---

**Data Collection Date:** October 29, 2025
**Tools Used:** `scripts/explore_pdf.py`, `scripts/analyze_reference.py`
**Sample Size:** Pages 302-305 (4 pages), Full reference JSON (13,353 entries)
