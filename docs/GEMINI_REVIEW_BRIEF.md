# Gemini Review Brief: v0.3.0 PDF Extraction Plan

> **Date:** October 29, 2025
> **Phase:** Pre-Implementation Review (Phase 1.5)
> **Your Role:** Senior Architect + Auditor
> **Goal:** Validate readiness for Phase 2 implementation

---

## 📋 Executive Summary

**Status:** Phase 1 Research complete. Need senior review before Phase 2 implementation.

**What we've done:**
1. ✅ GPT created initial solution plan
2. ✅ Claude added 53 critical questions and decision points
3. ✅ Codex provided technical implementation guidance
4. ✅ Phase 1 research scripts executed against real PDF

**What we need from you:**
- Validate technical decisions against actual data
- Identify contradictions between AI collaborators
- Assess Phase 2 readiness (green/yellow/red light)
- Risk evaluation and gap analysis

---

## 🎯 Your Mission

### 1. **Technical Validation**

**Given these Phase 1 findings:**
```json
{
  "monster_headers": "GillSans-SemiBold @ 18.0pt and 13.92pt",
  "body_text": "Calibri @ 9.84pt",
  "section_headers": "Calibri-Bold @ 12.0pt",
  "column_midpoint": "306.0 pt",
  "left_column_avg": "~90 pt",
  "right_column_avg": "~370 pt",
  "monster_count": "319 unique monsters",
  "page_range": "300+"
}
```

**Questions:**
- Is the header detection strategy (font size spike + type-line pattern) sound?
- Is 306pt column split correct given measured coordinates?
- Are the font thresholds reliable or do we need fallbacks?
- What edge cases might these measurements miss?

### 2. **Contradiction Detection**

**Review these three perspectives for conflicts:**

**GPT's Recommendations:**
- Two-phase approach: raw extraction → parsing
- Bridge pattern for backward compatibility
- PyMuPDF with `get_text("dict")`

**Claude's Concerns:**
- 53 open questions (see Appendix of Extraction_Solution_Plan.md)
- Emphasis on evidence-based decisions before coding
- Warning about premature optimization

**Codex's Technical Choices:**
- Span-level granularity with bbox storage
- Hardcode extraction params in v0.3.0, config later
- Best-effort with warnings (no fail-fast)

**Your task:** Do these recommendations align? Any buried contradictions?

### 3. **Risk Assessment**

**Codex identified 6 risks:**

| Risk | Impact | Mitigation | Your Assessment? |
|------|--------|-----------|------------------|
| Reading order drift when PyMuPDF changes | Medium | Pin version, round coordinates | ? |
| Headers without bold fonts | Medium | Combine heuristics + keywords | ? |
| Multi-column wrap mid-stat-block | High | Duplicate spans, merge by y-order | ? |
| PDF errata releases | Medium | Re-run scripts on SHA change | ? |
| Reference JSON mismatches | Low | Advisory only | ? |
| Memory spikes | Low | Stream JSON writes | ? |

**Questions:**
- Are these the RIGHT risks?
- Any missing risks?
- Are mitigations sufficient or hand-wavy?
- Priority ordering correct?

### 4. **Phase 2 Readiness**

**Review the 53-question appendix status tracker.**

**For each category, assess:**
- A. Extraction Scope (3 questions) - Ready?
- B. Boundary Detection (5 questions) - Ready?
- C. Two-Column Layout (6 questions) - Ready?
- D. Raw JSON Schema (5 questions) - Ready?
- E. Reference JSON Usage (4 questions) - Ready?
- F. Bridge Strategy (4 questions) - Ready?

**Give us:**
- 🟢 **Green:** Ready to implement (no blockers)
- 🟡 **Yellow:** Proceed with caution (minor gaps)
- 🔴 **Red:** Stop, more research needed (critical gaps)

### 5. **Schema Validation**

**Review:** `schemas/raw_monster.schema.json`

**Questions:**
- Does it capture everything needed from PDF?
- Should we add fields? (e.g., `extraction_confidence`, `needs_manual_review`)
- Should we remove fields? (e.g., is `color` array necessary?)
- Is `additionalProperties: true` appropriate or too loose?

---

## 📚 Key Documents to Review

### Primary Documents:
1. **`docs/Extraction_Solution_Plan.md`** (main plan, ~400 lines)
   - Section 2: Technical approach with Codex's updates
   - Section 7: Phase 1-3 action plan with priorities
   - Appendix: 53-question status tracker

2. **`schemas/raw_monster.schema.json`** (extraction output format)

3. **`docs/reference/reference_summary.json`** (319 monsters identified)

### Supporting Evidence:
4. **`scripts/explore_pdf.py`** (font analysis tool)
5. **`scripts/analyze_reference.py`** (reference JSON inspector)

### Context:
6. **`AGENTS.md`** (project guardrails and workflow)
7. **`docs/ROADMAP.md`** (v0.1-v0.5 progression)

---

## 🔍 Specific Areas Needing Your Expertise

### **Long-Context Reasoning:**
You have 2M+ token context window. Use it to:
- Cross-reference all 53 questions against actual findings
- Spot patterns humans/short-context AIs miss
- Identify subtle contradictions across 400+ lines of planning

### **Multi-Document Synthesis:**
- Do the scripts match the plan?
- Does the schema match the findings?
- Do the guardrails (AGENTS.md) align with the approach?

### **Edge Case Prediction:**
Given the actual PDF measurements, what edge cases might we hit?
- Monsters with unusual fonts?
- Single-column title pages?
- Cross-page stat blocks?
- Variant monsters with parenthetical names?

### **Architecture Validation:**
**Current decision:** Skip bridge, update `parse_monsters.py` directly

```
PDF → raw JSON → UPDATED parse_monsters.py → normalized
```

**Alternative rejected:** Bridge pattern
```
PDF → raw JSON → bridge JSON → old parser → normalized
```

**Your assessment:** Right call? What are we missing?

---

## 🎯 Decision Philosophy

**User's stated values:**
- "Select the best path forward, not just the easy path"
- "If there are problems, I want them to be my problems" (own extraction)
- "Anti-cruft" - delete unnecessary complexity
- "No bridge if it blocks progress" - pragmatic over pure

**Apply these values to your assessment.**

---

## 📊 Output Format

### **Section 1: Phase 2 Readiness Assessment**
```
Overall Status: 🟢 Green / 🟡 Yellow / 🔴 Red

Rationale: [Your analysis]

Blockers (if any):
- [ ] Critical gap #1
- [ ] Critical gap #2

Cautions (if yellow):
- ⚠️ Risk area #1
- ⚠️ Risk area #2
```

### **Section 2: Technical Validation**
```
Header Detection: ✅ Sound / ⚠️ Needs adjustment / ❌ Flawed
Column Split: ✅ Correct / ⚠️ Verify / ❌ Wrong
Schema Completeness: ✅ Complete / ⚠️ Minor gaps / ❌ Major gaps

Detailed findings:
[Your analysis with specific line references]
```

### **Section 3: Contradiction Analysis**
```
Conflicts found: [Number]

1. [Conflict description]
   - GPT says: ...
   - Claude says: ...
   - Codex says: ...
   - Resolution: ...
```

### **Section 4: Risk Re-Assessment**
```
Additional risks identified: [Number]

Priority order (revised):
1. [Highest risk with mitigation]
2. [Second highest]
...

Risks to deprioritize:
- [Risk that's overstated]
```

### **Section 5: Recommended Actions**

**Before Phase 2:**
- [ ] Action item #1 (if red/yellow)
- [ ] Action item #2

**During Phase 2:**
- [ ] Validation checkpoint #1
- [ ] Validation checkpoint #2

**Quick Wins:**
- [ ] Low-hanging fruit we can do today

---

## 🚀 Success Criteria

**You've succeeded if:**
1. ✅ We have clear go/no-go for Phase 2
2. ✅ All contradictions resolved or flagged
3. ✅ Risk assessment is reality-based (not hand-wavy)
4. ✅ Schema validated against actual PDF structure
5. ✅ Edge cases identified with concrete examples
6. ✅ We feel confident starting implementation

---

## 🤝 Collaboration Context

**AI Team Involved:**
- **GPT-4:** Initial solution architecture
- **Claude (Sonnet 4.5):** Critical question analysis, research phase
- **Codex:** Technical implementation details, Python-specific guidance
- **You (Gemini 2.0 Flash):** Senior review, long-context synthesis, validation

**Human (Wolftales):**
- Philosophy: Best path > easy path
- Role: Final decision maker, owns the problems
- Preference: Pragmatic, anti-cruft, evidence-based

**Your unique value:** Long-context reasoning, multi-document synthesis, contradiction detection, architectural validation with actual data.

---

## 📎 Attachments Referenced

All files are in the repository at: `wolftales/srd-builder`

**Must read:**
- `docs/Extraction_Solution_Plan.md`
- `schemas/raw_monster.schema.json`
- `docs/reference/reference_summary.json`

**Should read:**
- `scripts/explore_pdf.py` + `scripts/analyze_reference.py`
- `AGENTS.md` (workflow guardrails)

**Context:**
- `docs/ROADMAP.md` (where we're going)
- `schemas/monster.schema.json` (final output target)

---

**Ready when you are, Gemini. We trust your architectural judgment. 🎯**
