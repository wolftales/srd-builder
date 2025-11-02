# Data Dictionary

This document maps SRD 5.1 source terminology and formats to our normalized schema field names, explaining how we transform raw data into structured JSON.

**Version:** Schema v1.3.0
**Updated:** 2025-11-01

---

## Purpose

The SRD uses natural language, tables, and gaming terminology. Our schemas normalize this into consistent, machine-readable structures. This dictionary explains:

1. **SRD terminology → Our field names** (e.g., "Versatile (1d8)" → `versatile_damage`)
2. **Data transformations** (e.g., "11 + Dex modifier" → `{base: 11, dex_bonus: true}`)
3. **Field meanings and derivations** (computed vs. extracted fields)
4. **Cross-dataset patterns** (shared conventions like `simple_name`, namespaced `id`)

---

## Universal Fields (All Datasets)

These fields appear consistently across all entity types (monsters, equipment, spells, etc.):

### `id`
- **Type:** `string`
- **Pattern:** `<entity_type>:<normalized_name>`
- **Examples:** `monster:adult_red_dragon`, `item:longsword`, `spell:fireball`
- **SRD Source:** Derived from entity name
- **Transformation:** Lowercase, replace spaces/punctuation with underscores, namespace with entity type
- **Purpose:** Stable, globally unique identifier for cross-referencing

### `name`
- **Type:** `string`
- **SRD Source:** Direct from SRD (e.g., "Adult Red Dragon", "Longsword", "Fireball")
- **Transformation:** Minimal - preserve original capitalization and spacing
- **Purpose:** Display name for UI presentation

### `simple_name`
- **Type:** `string`
- **Pattern:** `[a-z0-9_]+` (lowercase alphanumeric + underscores)
- **Examples:** `adult_red_dragon`, `longsword`, `fireball`
- **SRD Source:** Derived from `name`
- **Transformation:** Same as `id` but without namespace prefix
- **Purpose:** Human-readable identifier for indexing, search, and sorting

### `page`
- **Type:** `integer`
- **SRD Source:** PDF page number where entity appears
- **Purpose:** Citation and reference back to source material

### `src`
- **Type:** `string`
- **Examples:** `"SRD 5.1"`, `"SRD_CC_v5.1"`
- **SRD Source:** Document metadata
- **Purpose:** Track which source document provided the data

### `summary`
- **Type:** `string` (optional)
- **SRD Source:** First significant sentence or trait description
- **Examples:**
  - Monster: `"If the dragon fails a saving throw, it can choose to succeed instead."` (from Legendary Resistance trait)
  - Equipment: Brief item description (future)
- **Purpose:** One-sentence preview for tooltips, search results, or quick reference

---

## Monsters Dataset

### Core Identity

#### `size`
- **Type:** `string`
- **SRD Values:** `"Tiny"`, `"Small"`, `"Medium"`, `"Large"`, `"Huge"`, `"Gargantuan"`
- **SRD Source:** Monster stat block header (e.g., "_Huge dragon, chaotic evil_")
- **Transformation:** Extract first word from type line

#### `type`
- **Type:** `string`
- **SRD Values:** `"dragon"`, `"humanoid"`, `"undead"`, `"aberration"`, `"beast"`, etc.
- **SRD Source:** Monster stat block header (e.g., "_Huge **dragon**, chaotic evil_")
- **Transformation:** Extract creature type from type line

#### `alignment`
- **Type:** `string`
- **SRD Values:** `"chaotic evil"`, `"lawful good"`, `"neutral"`, `"unaligned"`, etc.
- **SRD Source:** Monster stat block header (e.g., "_Huge dragon, **chaotic evil**_")
- **Transformation:** Extract alignment from type line

### Defenses

#### `armor_class`
- **Type:** `integer | string | object`
- **SRD Format:**
  - `"19 (natural armor)"` → `{value: 19, source: "natural armor"}`
  - `"15"` → `15`
  - Complex cases → `string` (fallback)
- **SRD Source:** "**Armor Class**" line in stat block
- **Transformation:** Parse number and optional parenthetical source
- **Note:** v1.1.0 handles both simple integers and structured objects

#### `hit_points`
- **Type:** `integer | string | object`
- **SRD Format:**
  - `"256 (19d12+133)"` → `{average: 256, formula: "19d12+133"}`
  - Simple number → `integer`
- **SRD Source:** "**Hit Points**" line in stat block
- **Transformation:** Parse average value and dice formula
- **Related:** `hit_dice` stores the full formula string separately

#### `hit_dice`
- **Type:** `string`
- **SRD Format:** `"19d12 + 133"`
- **SRD Source:** Extracted from Hit Points parenthetical
- **Transformation:** Parse dice notation from `hit_points` field
- **Purpose:** Separate field for easier dice rolling calculations

### Abilities

#### `ability_scores`
- **Type:** `object`
- **SRD Source:** Six ability scores table in stat block
- **SRD Format:**
  ```
  STR     DEX     CON     INT     WIS     CHA
  27(+8)  10(+0)  25(+7)  16(+3)  13(+1)  21(+5)
  ```
- **Transformation:** Parse into object with full ability names:
  ```json
  {
    "strength": 27,
    "dexterity": 10,
    "constitution": 25,
    "intelligence": 16,
    "wisdom": 13,
    "charisma": 21
  }
  ```
- **Note:** Modifiers (e.g., +8) are in SRD but not stored - easily calculated as `(score - 10) / 2`

#### `saving_throws`
- **Type:** `object` (optional)
- **SRD Source:** "**Saving Throws**" line listing proficient saves
- **SRD Format:** `"Dex +6, Con +13, Wis +7, Cha +11"`
- **Transformation:** Parse into object with full ability names as keys:
  ```json
  {
    "dexterity": 6,
    "constitution": 13,
    "wisdom": 7,
    "charisma": 11
  }
  ```
- **Note:** Only includes proficient saves (omitted abilities use base modifier)

#### `skills`
- **Type:** `object` (optional)
- **SRD Source:** "**Skills**" line listing proficient skills
- **SRD Format:** `"Perception +13, Stealth +6"`
- **Transformation:** Parse into object with lowercase skill names:
  ```json
  {
    "perception": 13,
    "stealth": 6
  }
  ```

### Movement

#### `speed`
- **Type:** `integer | string | object`
- **SRD Format:**
  - `"30 ft."` → `30` (single value)
  - `"40 ft., climb 40 ft., fly 80 ft."` → `{walk: 40, climb: 40, fly: 80}`
- **SRD Source:** "**Speed**" line in stat block
- **Transformation:** Parse movement types and convert to feet (strip "ft.")
- **Common keys:** `walk`, `fly`, `swim`, `climb`, `burrow`, `hover`

### Senses

#### `senses`
- **Type:** `object` (optional)
- **SRD Format:** `"blindsight 60 ft., darkvision 120 ft., passive Perception 23"`
- **Transformation:**
  ```json
  {
    "blindsight": 60,
    "darkvision": 120
  }
  ```
- **Note:** `passive Perception` is omitted (derivable from Perception skill: 10 + modifier)

### Resistances and Immunities

#### `damage_immunities`
- **Type:** `array[object]` (optional)
- **SRD Format:** `"fire"`, `"bludgeoning, piercing, and slashing from nonmagical attacks"`
- **Transformation:** Parse into array of damage type objects:
  ```json
  [
    {"type": "fire"}
  ]
  ```
- **Note:** Complex conditions (e.g., "from nonmagical attacks") currently stored as text - future enhancement

#### `damage_resistances`
- **Type:** `array[object]` (optional)
- **Format:** Same as `damage_immunities`

#### `damage_vulnerabilities`
- **Type:** `array[object]` (optional)
- **Format:** Same as `damage_immunities`

#### `condition_immunities`
- **Type:** `array[string]` (optional)
- **SRD Format:** `"charmed, frightened, paralyzed"`
- **Transformation:** Parse into array: `["charmed", "frightened", "paralyzed"]`

### Languages

#### `languages`
- **Type:** `string`
- **SRD Format:** `"Common, Draconic"`, `"—"` (for none)
- **Transformation:** Direct from SRD text
- **Note:** Future enhancement: parse into array or structured format

### Actions and Features

#### `traits`
- **Type:** `array[object]` (optional)
- **SRD Source:** Traits section (between stats and Actions)
- **Format:** Array of named text blocks with `simple_name`:
  ```json
  [
    {
      "name": "Legendary Resistance (3/Day)",
      "simple_name": "legendary_resistance_3day",
      "text": "If the dragon fails a saving throw, it can choose to succeed instead."
    }
  ]
  ```
- **Transformation:** Parse each trait heading and body; derive `simple_name`

#### `actions`
- **Type:** `array[object]` (required)
- **SRD Source:** "Actions" section in stat block
- **Format:** Same structure as `traits`
- **Examples:** Multiattack, Bite, Claw, Breath Weapon, Spellcasting
- **Note:** Attack statistics (to-hit, damage dice) currently in `text` - future enhancement for structured parsing

#### `legendary_actions`
- **Type:** `array[object]` (optional)
- **SRD Source:** "Legendary Actions" section (if present)
- **Format:** Same structure as `traits` and `actions`
- **Note:** Cost variants (e.g., "Costs 2 Actions") currently in name - future enhancement for structured cost field

#### `reactions`
- **Type:** `array[object]` (optional)
- **SRD Source:** "Reactions" section (if present)
- **Format:** Same structure as `traits`

### Challenge

#### `challenge_rating`
- **Type:** `number`
- **SRD Source:** "**Challenge**" line at end of stat block
- **SRD Format:** `"17 (18,000 XP)"`
- **Transformation:** Extract numeric CR (handles fractions: 0.125, 0.25, 0.5)
- **Related:** `xp_value` stores XP separately

#### `xp_value`
- **Type:** `integer`
- **SRD Source:** XP in parentheses after Challenge Rating
- **SRD Format:** `"17 (18,000 XP)"` → `18000`
- **Transformation:** Parse and strip commas

---

## Equipment Dataset

### Core Identity

#### `category`
- **Type:** `string`
- **Enum:** `"weapon"`, `"armor"`, `"gear"`, `"mount"`, `"trade_good"`
- **SRD Source:** Table section headers and context
- **Examples:**
  - "Weapons" section → `"weapon"`
  - "Armor" section → `"armor"`
  - "Adventuring Gear" section → `"gear"`
  - "Mounts and Vehicles" section → `"mount"`
  - "Trade Goods" section → `"trade_good"`

### Weapons

#### `weapon_type`
- **Type:** `string`
- **Enum:** `"melee"`, `"ranged"`
- **SRD Source:** Weapon table subsections ("Melee Weapons", "Ranged Weapons")
- **Transformation:** Derived from table section

#### `damage`
- **Type:** `object`
- **SRD Format:** `"1d8 slashing"`
- **Transformation:**
  ```json
  {
    "dice": "1d8",
    "type": "slashing"
  }
  ```
- **Properties:**
  - `dice` (string): Dice notation (e.g., `"1d8"`, `"2d6"`, `"1d6+1"`)
  - `type` (enum): `"bludgeoning"`, `"piercing"`, `"slashing"`
- **Purpose:** Base damage for one-handed use or default grip

#### `versatile_damage`
- **Type:** `object` (optional)
- **SRD Format:** Property text `"Versatile (1d10)"`
- **Transformation:**
  ```json
  {
    "dice": "1d10"
  }
  ```
- **Properties:**
  - `dice` (string, required): Two-handed damage dice
  - `type` (string, optional): Damage type (defaults to same as `damage.type`)
- **SRD Term:** "Versatile" weapon property
- **Meaning:** Damage dealt when wielding weapon with two hands instead of one
- **Examples:**
  - Longsword: 1d8 one-handed → 1d10 two-handed
  - Quarterstaff: 1d6 one-handed → 1d8 two-handed

#### `properties`
- **Type:** `array[string]`
- **SRD Format:** Comma-separated list in table column or inline text
- **SRD Examples:**
  - `"finesse, light, thrown (range 20/60)"`
  - `"heavy, reach, two-handed"`
  - `"ammunition (range 80/320), loading, two-handed"`
- **Transformation:** Split by comma, preserve original text (including ranges)
  ```json
  [
    "finesse",
    "light",
    "thrown (range 20/60)"
  ]
  ```
- **Common Properties:**
  - `"versatile"` - can use one or two hands (see `versatile_damage`)
  - `"finesse"` - use Dex or Str for attack/damage
  - `"light"` - can dual-wield
  - `"heavy"` - Small creatures have disadvantage
  - `"reach"` - 10 ft. reach instead of 5 ft.
  - `"two-handed"` - requires two hands
  - `"thrown (range X/Y)"` - can be thrown (range in feet)
  - `"ammunition (range X/Y)"` - requires ammunition (range in feet)
  - `"loading"` - can only fire once per action
- **Note:** Range currently stored in text - future `range` object will extract this

#### `range`
- **Type:** `object` (future enhancement)
- **SRD Format:** Currently in `properties` array: `"thrown (range 20/60)"`
- **Planned Structure:**
  ```json
  {
    "normal": 20,
    "long": 60
  }
  ```
- **Status:** Not yet extracted (v1.1.0) - ranges still in `properties` text
- **Purpose:** Structured range for ranged/thrown weapons

### Armor

#### `armor_category`
- **Type:** `string`
- **Enum:** `"light"`, `"medium"`, `"heavy"`
- **SRD Source:** Armor table subsection headers
- **Examples:**
  - "Light Armor" section → `"light"`
  - "Medium Armor" section → `"medium"`
  - "Heavy Armor" section → `"heavy"`

#### `armor_class`
- **Type:** `object`
- **SRD Format:** `"11 + Dex modifier"`, `"16"`, `"13 + Dex modifier (max 2)"`
- **Transformation:**
  ```json
  {
    "base": 11,
    "dex_bonus": true
  }
  ```
- **Properties:**
  - `base` (integer, required): Base AC value
  - `dex_bonus` (boolean, optional): Whether Dex modifier can be added
  - `max_dex_bonus` (integer, optional): Maximum Dex modifier (for medium armor - future)
- **Current Status (v1.1.0):**
  - Basic structure implemented
  - `dex_bonus` field present but currently always `false` (needs fix)
  - `max_dex_bonus` not yet parsed
- **Known Issues:** See `GPT_REVIEW_equipment_status.md` for AC parsing problems

#### `stealth_disadvantage`
- **Type:** `boolean` (optional)
- **SRD Source:** "Stealth" column in armor table showing "Disadvantage"
- **SRD Format:** `"Disadvantage"` or `"—"` (absent)
- **Transformation:** `true` if "Disadvantage" present, omitted otherwise

#### `strength_requirement`
- **Type:** `integer` (optional, future)
- **SRD Source:** "Strength" column in heavy armor table
- **SRD Format:** `"Str 13"`, `"Str 15"`, or `"—"`
- **Status:** Not yet extracted (v1.1.0)

### Cost and Physical Properties

#### `cost`
- **Type:** `object`
- **SRD Format:** `"15 gp"`, `"2 sp"`, `"50 gp"`
- **Transformation:**
  ```json
  {
    "amount": 15,
    "currency": "gp"
  }
  ```
- **Properties:**
  - `amount` (number): Numeric cost
  - `currency` (enum): `"cp"`, `"sp"`, `"ep"`, `"gp"`, `"pp"`

#### `weight`
- **Type:** `string` (current - v1.1.0)
- **SRD Format:** `"10 lb."`, `"1½ lb."`, `"3 lb."`
- **Transformation:** Direct from SRD (no parsing yet)
- **Known Issue:** Should be `number` for calculations - see `GPT_REVIEW_equipment_status.md`
- **Future:** Parse to numeric pounds, handle fractions and Unicode characters

#### `quantity`
- **Type:** `string` (optional)
- **SRD Format:** Quantity or packaging info from table
- **Examples:**
  - `"bolts (20)"` - ammunition quantity
  - `"50 gp"` - appears on some gear items (duplicate of cost - data quality issue)
- **Context:** Appears on gear, mounts, and trade goods
- **Note:** Field meaning unclear in some cases - may need cleanup

### Future Fields (Magic Items - v2.0)

These fields are defined in the schema but not yet populated (reserved for future magic item extraction):

#### `variant_of`
- **Type:** `string` (pattern: `item:*`)
- **Purpose:** Reference to base mundane item (e.g., `"item:longsword"` for +1 Longsword)
- **Use Case:** Link magic items to their base versions

#### `is_magic`
- **Type:** `boolean`
- **Purpose:** Flag to distinguish magic from mundane items

#### `rarity`
- **Type:** `string`
- **Enum:** `"common"`, `"uncommon"`, `"rare"`, `"very rare"`, `"legendary"`, `"artifact"`
- **SRD Source:** Magic item rarity (DMG)

#### `requires_attunement`
- **Type:** `boolean`
- **Purpose:** Whether magic item requires attunement to use

#### `modifiers`
- **Type:** `array[object]`
- **Purpose:** Structured bonuses from magic items
- **Example:**
  ```json
  [
    {"type": "attack", "value": 1},
    {"type": "damage", "value": 1}
  ]
  ```

---

## Spells Dataset

Status: Schema exists (`spell.schema.json`) but dataset not yet built. Fields TBD based on SRD spell format.

---

## Transformation Patterns

### Name Normalization (`simple_name` derivation)

**Process:**
1. Take original `name` field value
2. Convert to lowercase
3. Replace spaces, hyphens, parentheses, commas with underscores
4. Remove apostrophes and other punctuation
5. Collapse consecutive underscores to single underscore
6. Trim leading/trailing underscores

**Examples:**
- `"Adult Red Dragon"` → `"adult_red_dragon"`
- `"Lantern, hooded"` → `"lantern_hooded"`
- `"Antitoxin (vial)"` → `"antitoxin_vial"`
- `"Fire Breath (Recharge 5–6)"` → `"fire_breath_recharge_56"`
- `"Wing Attack (Costs 2 Actions)"` → `"wing_attack_costs_2_actions"`

### Namespace Prefixes (`id` generation)

**Pattern:** `<entity_type>:<simple_name>`

**Entity Types:**
- `monster:` - All creatures/NPCs
- `item:` - All equipment (weapons, armor, gear, mounts, trade goods)
- `spell:` - All spells (future)
- `class:` - All character classes (future)
- `lineage:` - All ancestries/races (future)
- `condition:` - All conditions (future)

**Purpose:**
- Global uniqueness across all datasets
- Enable cross-references (e.g., spell lists referencing `spell:fireball`)
- Support mixed-entity collections and search indexes

### Nested Entries with `simple_name`

**Pattern:** Actions, traits, legendary actions, reactions - any nested named text blocks

**Structure:**
```json
{
  "name": "Original Name from SRD",
  "simple_name": "normalized_version",
  "text": "Full description text..."
}
```

**Purpose:**
- Enable referencing specific actions/traits
- Support search and filtering within entities
- Maintain consistency with top-level entity pattern

---

## Spells Dataset (v1.3.0)

### Core Identity

#### `level`
- **Type:** `integer` (0-9)
- **SRD Source:** Spell header (e.g., "3rd-level evocation", "Evocation cantrip")
- **Transformation:** Parse level number; cantrips = 0
- **Examples:** `0` (cantrip), `1` (1st-level), `3` (3rd-level), `9` (9th-level)

#### `school`
- **Type:** `string` (enum)
- **SRD Values:** `abjuration`, `conjuration`, `divination`, `enchantment`, `evocation`, `illusion`, `necromancy`, `transmutation`
- **SRD Source:** Spell header (e.g., "3rd-level **evocation**")
- **Transformation:** Extract school name, normalize to lowercase

### Casting Information (`casting` object)

#### `casting.time`
- **Type:** `string`
- **SRD Source:** "**Casting Time:**" line
- **Examples:** `"1 action"`, `"1 bonus action"`, `"1 minute"`, `"10 minutes"`, `"1 hour"`
- **Transformation:** Direct extraction, preserve original format

#### `casting.range`
- **Type:** `object` or `string`
- **SRD Source:** "**Range:**" line
- **Structured format (numeric):**
  ```json
  {"kind": "ranged", "value": 150, "unit": "feet"}
  ```
- **Special values (string):** `"self"`, `"touch"`, `"sight"`, `"unlimited"`
- **Transformation:** Parse numeric + unit OR recognize special keywords

#### `casting.duration`
- **Type:** `string`
- **SRD Source:** "**Duration:**" line
- **Examples:** `"instantaneous"`, `"up to 1 minute"`, `"1 hour"`, `"until dispelled"`
- **Transformation:** Extract text, remove "Concentration, " prefix (tracked separately)

#### `casting.concentration`
- **Type:** `boolean`
- **SRD Source:** "**Duration:**" line (e.g., "Concentration, up to 1 minute")
- **Transformation:** Detect "Concentration" keyword
- **Purpose:** Filter concentration spells, manage spell slot usage

#### `casting.ritual`
- **Type:** `boolean`
- **SRD Source:** Casting time line (e.g., "1 minute (ritual)")
- **Transformation:** Detect "(ritual)" marker
- **Purpose:** Identify spells castable without spell slots

### Components (`components` object)

#### `components.verbal`
- **Type:** `boolean`
- **SRD Source:** "**Components:**" line - presence of "V"
- **Transformation:** `true` if "V" appears in components list

#### `components.somatic`
- **Type:** `boolean`
- **SRD Source:** "**Components:**" line - presence of "S"
- **Transformation:** `true` if "S" appears in components list

#### `components.material`
- **Type:** `boolean`
- **SRD Source:** "**Components:**" line - presence of "M"
- **Transformation:** `true` if "M" appears in components list

#### `components.material_description`
- **Type:** `string` (optional)
- **SRD Source:** "**Components:**" line - parenthetical after "M"
- **Example:** `"M (a tiny ball of bat guano and sulfur)"`
- **Transformation:** Extract text within parentheses following "M"
- **Purpose:** Display material requirements, track consumed materials

### Effects (`effects` object, optional)

#### `effects.damage`
- **Type:** `object` (optional)
- **Fields:** `{"dice": "8d6", "type": "fire"}`
- **SRD Source:** Spell description text
- **Transformation:** Extract damage dice pattern and type from description
- **Damage Types:** acid, bludgeoning, cold, fire, force, lightning, necrotic, piercing, poison, psychic, radiant, slashing, thunder

#### `effects.healing`
- **Type:** `object` (optional)
- **Fields:** `{"dice": "2d8"}`
- **SRD Source:** Healing amount in description
- **Transformation:** Extract dice pattern for healing spells

#### `effects.save`
- **Type:** `object` (optional)
- **Fields:** `{"ability": "dexterity", "on_success": "half_damage"}`
- **SRD Source:** Saving throw mention in description
- **Abilities:** strength, dexterity, constitution, intelligence, wisdom, charisma
- **Success Outcomes:** `half_damage`, `negates`, `none`, `partial`

#### `effects.attack`
- **Type:** `object` (optional)
- **Fields:** `{"type": "ranged_spell"}` or `{"type": "melee_spell"}`
- **SRD Source:** Attack roll requirement in description
- **Purpose:** Identify spell attack roll spells (vs. saving throw spells)

#### `effects.area`
- **Type:** `object` (optional)
- **Fields:** `{"shape": "sphere", "size": 20, "unit": "feet"}`
- **SRD Source:** Area description in spell text
- **Shapes:** cone, cube, cylinder, line, sphere
- **Purpose:** Visual representation, affected creature calculations

#### `effects.conditions`
- **Type:** `array` (optional)
- **Example:** `["blinded", "charmed", "frightened"]`
- **SRD Source:** Condition applications in description
- **Purpose:** Track status effects applied by spell

### Scaling (`scaling` object, optional)

#### `scaling.type`
- **Type:** `string` (enum)
- **Values:** `"slot"` or `"character_level"`
- **Purpose:** Distinguish between upcast scaling (leveled spells) and cantrip scaling

**Slot-level scaling (`"slot"`):**
- Applies when spell is cast with higher-level spell slot
- Example: Fireball at 4th level does more damage than 3rd level

**Character-level scaling (`"character_level"`):**
- Applies to cantrips based on caster's level
- Example: Fire Bolt at 5th, 11th, 17th character level

#### `scaling.base_level`
- **Type:** `integer`
- **SRD Source:** Spell level (for slot scaling) or 1 (for character scaling)
- **Purpose:** Baseline for scaling calculations

#### `scaling.formula`
- **Type:** `string`
- **SRD Source:** "At Higher Levels" section or cantrip scaling description
- **Examples:**
  - `"+1d6 per slot level above 3rd"` (slot scaling)
  - `"+1d10 at 5th, 11th, and 17th level"` (character scaling)
- **Purpose:** Human-readable scaling display, directly displayable to users
- **Design:** Preserves SRD text rather than over-structuring

### Full Description

#### `text`
- **Type:** `string`
- **SRD Source:** Complete spell description from SRD
- **Transformation:** Concatenated paragraphs, preserves original wording
- **Purpose:** Full spell details for display, search indexing

---

## Data Quality Notes

### Known Limitations (v1.3.0)

1. **Armor AC Parsing:** `armor_class.base` sometimes contains cost value instead of AC (see `GPT_REVIEW_equipment_status.md`)
2. **Armor Categories:** Some armor (e.g., Leather) misclassified as medium instead of light
3. **Weight Format:** Stored as string (`"10 lb."`) instead of number - blocks calculations
4. **Range Extraction:** Ranges embedded in `properties` text, not extracted to structured `range` object
5. **Versatile Extraction:** Not consistently parsed from properties into `versatile_damage`
6. **Dex Bonus:** `armor_class.dex_bonus` currently always `false` - needs proper light/medium armor logic

### Future Enhancements

1. **Attack Parsing:** Extract structured attack stats from action text (to-hit bonus, damage dice, damage type)
2. **Spell Slot Parsing:** Extract spellcasting details from monster spellcasting actions
3. **Language Arrays:** Parse `languages` string into structured array
4. **Condition Arrays:** Convert comma-separated strings to proper arrays
5. **Complex Resistances:** Parse conditional resistances (e.g., "from nonmagical attacks") into structured format
6. **Magic Items:** Complete extraction and variant linking (see Future Fields section)

---

## Schema Evolution

This dictionary reflects **Schema v1.1.0**. Changes to field meanings, transformations, or additions will be documented here with version annotations.

**Version History:**
- **v1.0.0** (MVP): Basic extraction with string-heavy formats
- **v1.1.0** (Current): Structured objects (AC, HP, cost), namespaced IDs, `simple_name` everywhere

See `SCHEMAS.md` for architectural evolution and versioning strategy.

---

## See Also

- **SCHEMAS.md** - Schema versioning strategy and design patterns
- **GPT_REVIEW_equipment_status.md** - Known issues and extraction challenges for equipment
- **PARKING_LOT.md** - Future enhancements and architectural decisions
- **Schema Files** - `schemas/*.schema.json` for formal JSON Schema definitions
