# Equipment Schema: Recommended Compromise (v1.1.0)

## Philosophy

**Balance two needs:**
1. **Consumer clarity** - Schema reflects what's actually in the data NOW
2. **Builder flexibility** - Include optional fields for planned features (magic items)

**Solution:** Three field tiers with clear documentation

---

## Recommended Schema

```json
{
  "$id": "https://srd-builder.local/schemas/equipment.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SRD 5.1 Equipment (v1.1.0)",
  "description": "Equipment items from SRD 5.1. Includes base equipment (extracted) and optional magic item fields (future).",
  "type": "object",
  "required": ["id", "name", "category", "source", "page"],
  "additionalProperties": false,

  "properties": {

    // ============================================================
    // TIER 1: Core Fields (ALWAYS PRESENT)
    // ============================================================

    "id": {
      "type": "string",
      "pattern": "^item:",
      "description": "Unique identifier using item: namespace"
    },

    "name": {
      "type": "string",
      "description": "Display name (e.g., 'Longsword')"
    },

    "simple_name": {
      "type": "string",
      "description": "Lowercase, hyphenated (e.g., 'longsword')"
    },

    "category": {
      "type": "string",
      "enum": ["armor", "weapon", "gear", "mount", "trade_good"],
      "description": "Item category as extracted from SRD tables"
    },

    "source": {
      "type": "string",
      "description": "Source document (e.g., 'SRD 5.1')"
    },

    "page": {
      "type": "integer",
      "description": "Page number in source PDF"
    },

    // ============================================================
    // TIER 2: Category-Specific Fields (PRESENT WHEN RELEVANT)
    // These are extracted NOW for base equipment
    // ============================================================

    "sub_category": {
      "type": ["string", "null"],
      "description": "Armor: light/medium/heavy. Weapon: simple/martial (future). Gear: varies.",
      "examples": ["light", "medium", "heavy", "adventuring gear"]
    },

    "cost": {
      "type": "object",
      "required": ["amount", "currency"],
      "properties": {
        "amount": { "type": "number" },
        "currency": {
          "type": "string",
          "enum": ["cp", "sp", "ep", "gp", "pp"]
        }
      },
      "description": "Base cost in D&D currency"
    },

    "weight_lb": {
      "type": ["number", "null"],
      "description": "Parsed weight in pounds (enables calculations)"
    },

    "weight_raw": {
      "type": ["string", "null"],
      "description": "Original weight text from PDF (e.g., '10 lb.', '1/4 lb.', '—')"
    },

    // ARMOR-SPECIFIC

    "armor_class": {
      "type": "object",
      "required": ["base"],
      "properties": {
        "base": {
          "type": "integer",
          "description": "Base AC value"
        },
        "dex_bonus": {
          "type": "boolean",
          "description": "Whether Dex modifier applies"
        },
        "max_bonus": {
          "type": ["integer", "null"],
          "description": "Max Dex bonus (e.g., 2 for medium armor)"
        }
      },
      "description": "Armor Class calculation (armor only)"
    },

    "strength_req": {
      "type": ["integer", "null"],
      "description": "Minimum Strength requirement (heavy armor)"
    },

    "stealth_disadvantage": {
      "type": ["boolean", "null"],
      "description": "Whether armor imposes stealth disadvantage"
    },

    // WEAPON-SPECIFIC

    "weapon_type": {
      "type": ["string", "null"],
      "enum": ["melee", "ranged", null],
      "description": "Attack type (weapons only)"
    },

    "damage": {
      "type": ["object", "null"],
      "required": ["dice", "type"],
      "properties": {
        "dice": {
          "type": "string",
          "pattern": "^[0-9]+d[0-9]+$",
          "description": "Damage dice (e.g., '1d8')"
        },
        "type": {
          "type": "string",
          "description": "Damage type (e.g., 'slashing', 'piercing')"
        }
      },
      "description": "Base damage (weapons only)"
    },

    "versatile_damage": {
      "type": ["object", "null"],
      "properties": {
        "dice": {
          "type": "string",
          "pattern": "^[0-9]+d[0-9]+$",
          "description": "Damage when wielded two-handed"
        }
      },
      "description": "Versatile damage (some weapons). Type defaults to base damage type."
    },

    "properties": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Weapon/armor properties (e.g., 'finesse', 'heavy', 'versatile (1d10)')"
    },

    // GEAR-SPECIFIC

    "quantity": {
      "type": ["integer", "null"],
      "description": "Default quantity (e.g., arrows come in 20)"
    },

    // ============================================================
    // TIER 3: Future Fields (OPTIONAL - for magic items)
    // Clearly marked as not yet extracted from base equipment
    // ============================================================

    "variant_of": {
      "type": ["string", "null"],
      "description": "FUTURE: Reference to base item (magic items: 'item:longsword')"
    },

    "is_magic": {
      "type": "boolean",
      "default": false,
      "description": "FUTURE: Whether item is magical (false for all base equipment)"
    },

    "rarity": {
      "type": ["string", "null"],
      "enum": ["common", "uncommon", "rare", "very rare", "legendary", "artifact", null],
      "description": "FUTURE: Magic item rarity (null for base equipment)"
    },

    "requires_attunement": {
      "type": ["boolean", "null"],
      "description": "FUTURE: Whether magic item requires attunement"
    },

    "modifiers": {
      "type": "array",
      "items": { "type": "string" },
      "description": "FUTURE: Magic item modifiers (e.g., '+1 to attack and damage')"
    },

    // ============================================================
    // TIER 4: Extraction Metadata (INTERNAL)
    // For debugging and tracking extraction process
    // ============================================================

    "section": {
      "type": ["string", "null"],
      "description": "INTERNAL: PDF section header where item was found"
    },

    "table_header": {
      "type": ["array", "null"],
      "items": { "type": "string" },
      "description": "INTERNAL: Column headers from source table"
    },

    "row_index": {
      "type": ["integer", "null"],
      "description": "INTERNAL: Row position in source table"
    },

    "_meta": {
      "type": "object",
      "description": "INTERNAL: Builder metadata (extraction timestamps, notes, issues)"
    }
  }
}
```

---

## Key Compromises

### 1. Weight: Both Formats
**Copilot wanted:** String only (matches current data)
**I wanted:** Number only (enables calculations)
**Compromise:** `weight_lb` (number) + `weight_raw` (string)

**Rationale:**
- Consumers who want calculations use `weight_lb`
- Consumers who want exact source text use `weight_raw`
- Parser can emit both without complexity
- Future magic items can add weight modifiers to `weight_lb`

### 2. Category Enum: Current Reality
**Copilot wanted:** Only extracted values
**I wanted:** All possible categories
**Compromise:** Use actual extracted values, document others in description

**Current enum:**
```json
["armor", "weapon", "gear", "mount", "trade_good"]
```

**Future expansion:** Add to enum when extracted (e.g., "tools", "services", "packs")

### 3. Future Fields: Included but Marked
**Copilot wanted:** Don't include until extracted
**I wanted:** Include all fields magic items will need
**Compromise:** Include with "FUTURE:" prefix in description

**Benefit:**
- Magic items can use same schema without version bump
- Clear documentation prevents confusion
- Validation still works (all optional)

### 4. Versatile Damage Type: Omitted
**Copilot observation:** Data doesn't include damage type, defaults to base damage
**Compromise:** Schema matches reality - only `dice` field

**Example:**
```json
{
  "damage": {"dice": "1d8", "type": "slashing"},
  "versatile_damage": {"dice": "1d10"}  // Type is implicitly "slashing"
}
```

---

## What This Means for Implementation

### Phase 1: Equipment Parser Updates

**Must implement:**
1. ✅ Parse `weight_lb` from "10 lb." → 10
2. ✅ Keep `weight_raw` as-is
3. ✅ Extract `armor_class` as object (already in progress)
4. ✅ Extract `versatile_damage` from properties
5. ✅ Set `is_magic: false` for all base equipment (explicit default)

**Can defer:**
- `variant_of` (no variants in base equipment)
- `modifiers` (magic items only)
- `requires_attunement` (magic items only)

### Phase 2: Magic Items
When extracting magic items later, they'll use same schema:
```json
{
  "id": "item:longsword-plus-1",
  "name": "Longsword +1",
  "category": "weapon",
  "variant_of": "item:longsword",  // NOW populated
  "is_magic": true,                // NOW true
  "rarity": "uncommon",            // NOW populated
  "modifiers": ["+1 to attack and damage"],
  "damage": {"dice": "1d8", "type": "slashing"},
  "weight_lb": 3,
  "cost": {"amount": 0, "currency": "gp"}  // Not for sale
}
```

---

## Validation Benefits

### Current Base Equipment
```python
# All base equipment validates cleanly
validate(equipment_json, schema)  # ✅ Passes

# Future fields are all null/false/empty
assert item['is_magic'] == False
assert item['variant_of'] is None
assert item['modifiers'] == []
```

### Future Magic Items
```python
# Magic items validate with same schema
validate(magic_item_json, schema)  # ✅ Passes

# Future fields now populated
assert item['is_magic'] == True
assert item['variant_of'] == "item:longsword"
assert len(item['modifiers']) > 0
```

---

## Documentation Strategy

### In Schema File
Use description field to mark tiers:
- Core fields: No prefix
- Category-specific: Contextual description
- Future fields: "FUTURE:" prefix
- Internal fields: "INTERNAL:" prefix

### In README or Docs
```markdown
## Equipment Schema Tiers

**Tier 1: Core** - Present for all items
**Tier 2: Category-Specific** - Present when relevant (armor/weapon/gear)
**Tier 3: Future** - Reserved for magic items (optional, clearly marked)
**Tier 4: Internal** - Extraction metadata (for debugging)

Consumers should:
- Rely on Tier 1 + Tier 2 fields
- Ignore Tier 3 fields for base equipment (always null/false)
- Ignore Tier 4 fields (internal only)
```

---

## Version Strategy

### v1.1.0 (Current)
- All base equipment fields
- Optional magic item fields marked "FUTURE"
- Schema describes current reality + planned extensions

### v1.2.0 (When Magic Items Added)
- Same schema structure
- Update descriptions: Remove "FUTURE:" prefix
- Add examples showing populated magic item fields
- No breaking changes

### v2.0.0 (If Needed)
- Breaking changes only if consumer-facing fields change
- Examples: Rename fields, change types, remove fields
- Adding optional fields = minor version (1.x)

---

## Recommendation: Accept This Hybrid

**Why this works:**

1. **Copilot's concern addressed:** Schema accurately reflects current data
2. **My concern addressed:** Magic items won't need schema v2.0
3. **Consumer clarity:** Tier documentation makes intent clear
4. **Implementation flexibility:** Parser can emit both formats (weight_lb + weight_raw)
5. **Future-proof:** One schema version for base + magic items

**Action items:**

1. ✅ Use this schema as v1.1.0
2. ✅ Update parser to emit `weight_lb` (number) and `weight_raw` (string)
3. ✅ Document tier strategy in schema description
4. ✅ Validate current equipment.json against this schema
5. ✅ Use same schema for magic items later (no v2.0 needed)

---

## Alternative: If You Want Pure "Current Reality"

If you prefer Copilot's stricter approach, you can:

**Option A: Remove future fields entirely**
- Only include what's extracted now
- Add them in v1.2.0 when magic items extracted
- Cleaner but requires schema version bump

**Option B: Separate schemas**
- `equipment.schema.json` for base items
- `magic_items.schema.json` for magic items
- More files but clearer separation

**My take:** The hybrid approach above is best balance of pragmatism and planning.
