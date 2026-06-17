# Data Dictionary

This document maps SRD 5.1 source terminology and formats to our normalized schema field names, explaining how we transform raw data into structured JSON.

**Version:** Schema v1.3.0
**Updated:** 2025-11-09

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
- **Examples:** `monster:adult_red_dragon`, `creature:awakened_shrub`, `npc:acolyte`, `item:longsword`, `spell:fireball`
- **SRD Source:** Derived from entity name and page location
- **Transformation:** Lowercase, replace spaces/punctuation with underscores, namespace with entity type (monster: for pages 261-365, creature: for pages 366-394 Appendix MM-A, npc: for pages 395-403 Appendix MM-B)
- **Purpose:** Stable, globally unique identifier for cross-referencing with semantic separation by creature category

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
- `monster:` - Main bestiary creatures (SRD pages 261-365)
- `creature:` - Miscellaneous creatures from Appendix MM-A (SRD pages 366-394)
- `npc:` - Nonplayer characters from Appendix MM-B (SRD pages 395-403)
- `item:` - All equipment (weapons, armor, gear, mounts, trade goods)
- `spell:` - All spells
- `class:` - All character classes
- `lineage:` - All ancestries/races
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

## Rules Dataset (v0.17.0)

Game rules and mechanics extracted from SRD core chapters (abilities, combat, spellcasting, adventuring).

### Core Identity

#### `id`
- **Type:** `string`
- **Pattern:** `rule:<normalized_name>`
- **Examples:** `rule:ability_checks`, `rule:attack_rolls`, `rule:concentration`, `rule:bonus_actions`
- **SRD Source:** Derived from rule name and hierarchical position
- **Purpose:** Stable identifier for cross-referencing mechanics

#### `name`
- **Type:** `string`
- **Examples:** `"Ability Checks"`, `"Attack Rolls"`, `"Concentration"`, `"Bonus Actions"`
- **SRD Source:** Section/subsection headers from SRD chapters
- **Transformation:** Preserves original capitalization
- **Purpose:** Display name for UI, search, and navigation

#### `simple_name`
- **Type:** `string`
- **Pattern:** `[a-z0-9_]+`
- **Examples:** `ability_checks`, `attack_rolls`, `concentration`, `bonus_actions`
- **SRD Source:** Derived from `name`
- **Transformation:** Lowercase, spaces to underscores
- **Purpose:** Normalized search key

#### `category`
- **Type:** `string` (required)
- **Examples:** `"Using Ability Scores"`, `"Spellcasting"`, `"Combat"`
- **SRD Source:** Top-level chapter/section headers
- **Purpose:** High-level grouping of related rules
- **Coverage:** 7 categories from 76 pages:
  - Using Ability Scores (abilities, checks, scores)
  - Combat (actions, attacks, damage, movement)
  - Spellcasting (casting, components, concentration)
  - Movement (speed, terrain, climbing, jumping)
  - Environment (vision, light, falling, suffocating)
  - Resting (short rest, long rest)
  - Time (initiative, turns, rounds)

#### `subcategory`
- **Type:** `string` (optional)
- **Examples:** `"Ability Checks"`, `"Actions in Combat"`, `"Movement and Position"`, `"Casting a Spell"`
- **SRD Source:** Section headers within chapters
- **Purpose:** Fine-grained categorization within category
- **Note:** Most rules have both category and subcategory; some top-level rules may omit subcategory

### Hierarchical Structure

#### `parent_id`
- **Type:** `string` (optional)
- **Pattern:** `rule:<normalized_name>`
- **Examples:** `rule:ability_checks`, `rule:making_an_attack`
- **SRD Source:** Derived from outline structure
- **Purpose:** Links child rules to parent (rarely used - prefer subcategory)
- **Note:** Minimally used in current implementation (flat hierarchy with subcategories is preferred)

### Content

#### `text`
- **Type:** `array` of `string` (required)
- **SRD Source:** Rule description paragraphs from SRD body text
- **Transformation:**
  - Split into paragraphs (array items)
  - Remove PDF artifacts (\r, \n, control characters)
  - Preserve original SRD wording
- **Examples:**
  ```json
  "text": [
    "An ability check tests a character's or monster's innate talent and training in an effort to overcome a challenge.",
    "The DM calls for an ability check when a character or monster attempts an action (other than an attack) that has a chance of failure."
  ]
  ```
- **Purpose:** Human-readable rule text for display and search

#### `summary`
- **Type:** `string` (optional)
- **SRD Source:** Extracted from first sentence or manually curated
- **Examples:** `"When you make an attack, your attack roll determines whether the attack hits or misses."`
- **Purpose:** One-sentence preview for tooltips, search results, quick reference

### Search and Classification

#### `aliases`
- **Type:** `array` of `string` (optional)
- **Examples:** `["critical hit", "nat 20"]` for `rule:critical_hits`
- **SRD Source:** Alternative terminology, common player phrases
- **Purpose:** Improve search discoverability with alternative terms

#### `tags`
- **Type:** `array` of `enum` (optional)
- **Allowed Values:** `action`, `bonus_action`, `reaction`, `movement`, `saving_throw`, `ability_check`, `attack`, `advantage`, `disadvantage`, `concentration`, `proficiency`, `rest`, `damage`, `healing`, `vision`, `cover`, `condition`
- **Examples:** `["attack", "ability_check"]` for `rule:attack_rolls`
- **SRD Source:** Derived from rule content and mechanical patterns
- **Purpose:** Lightweight mechanical tagging for filtering and search
- **Note:** Tags are intentionally minimal - not every rule needs tags

### Cross-References

#### `related_conditions`
- **Type:** `array` of `string` (optional)
- **Pattern:** `condition:<normalized_name>`
- **Examples:** `["condition:blinded", "condition:invisible"]` for rules about vision
- **Purpose:** Link rules to game conditions they reference

#### `related_spells`
- **Type:** `array` of `string` (optional)
- **Pattern:** `spell:<normalized_name>`
- **Examples:** `["spell:shield", "spell:mage_armor"]` for AC-related rules
- **Purpose:** Link rules to spells that exemplify or interact with them

#### `related_features`
- **Type:** `array` of `string` (optional)
- **Pattern:** `feature:<normalized_name>`
- **Examples:** `["feature:action_surge", "feature:cunning_action"]` for action economy rules
- **Purpose:** Link rules to class features that modify them

#### `related_tables`
- **Type:** `array` of `string` (optional)
- **Pattern:** `table:<normalized_name>`
- **Examples:** `["table:ability_scores_and_modifiers"]` for ability score rules
- **Purpose:** Link rules to relevant reference tables

### Source Tracking

#### `page`
- **Type:** `integer` (required)
- **SRD Source:** PDF page number where rule text begins
- **Examples:** `76`, `94`, `101`
- **Purpose:** Citation and reference back to source PDF

#### `source`
- **Type:** `string` (required)
- **Examples:** `"SRD 5.1"`
- **Purpose:** Document provenance

### Design Notes

**Prose-First Philosophy:**
- Rules are primarily human-readable text, not structured data
- Unlike monsters/spells which have stat blocks, rules preserve SRD narrative
- Tags and cross-references are lightweight aids, not comprehensive categorization

**Minimal Hierarchy:**
- Most rules are flat with category/subcategory for organization
- `parent_id` is rarely used (prefer subcategory for grouping)
- Avoids deep nesting that complicates navigation

**No Formula Extraction:**
- Rules don't extract mechanical formulas (e.g., damage dice, modifiers)
- Preserves SRD wording for legal compliance and clarity
- Consumers parse formulas from `text` arrays if needed

---

## Tables Dataset

Reference tables extracted from SRD including class progression tables.

### Core Identity

#### `id`
- **Type:** `string`
- **Pattern:** `table:<normalized_name>`
- **Examples:** `table:proficiency_bonus`, `table:barbarian_progression`, `table:spell_slots_full_caster`
- **SRD Source:** Derived from table title/context
- **Purpose:** Stable identifier for cross-referencing

#### `name`
- **Type:** `string`
- **Examples:** `"Proficiency Bonus by Level"`, `"The Barbarian"`, `"Experience Points by Challenge Rating"`
- **SRD Source:** Table caption or heading from SRD
- **Purpose:** Display name for UI presentation

### Table Structure

#### `columns`
- **Type:** `array` of `object`
- **SRD Format:** Table headers → `{name: "Level", type: "integer"}`
- **Properties:**
  - `name` (string): Column header from SRD
  - `type` (string): `"integer"`, `"string"`, `"mixed"` (auto-detected from data)
- **Purpose:** Describe table structure for rendering and validation

#### `rows`
- **Type:** `array` of `array`
- **SRD Format:** Table rows, preserves cell order matching columns
- **Examples:**
  - `[1, "+2", "Rage, Unarmored Defense", 2, "+2"]` (Barbarian level 1)
  - `[5, 1800]` (CR 5 = 1800 XP)
- **Transformation:** Numeric values parsed to integers, everything else as strings
- **Purpose:** Table data ready for display or programmatic access

### Classification

#### `category`
- **Type:** `string`
- **Examples:** `"class_progression"`, `"character_creation"`, `"combat"`, `"magic"`, `"reference"`
- **SRD Source:** Derived from table context and section
- **Purpose:** Group related tables for navigation

#### `section`
- **Type:** `string`
- **Examples:** `"Chapter 3: Classes - Barbarian"`, `"Chapter 9: Combat"`, `"Chapter 1: Characters"`
- **SRD Source:** SRD chapter/section heading
- **Purpose:** Citation and context reference

---

## Lineages Dataset

Character lineages (formerly "races") with traits, abilities, and subraces.

### Core Identity

#### `id`
- **Type:** `string`
- **Pattern:** `lineage:<normalized_name>`
- **Examples:** `lineage:dwarf`, `lineage:mountain_dwarf`, `lineage:elf`
- **SRD Source:** Derived from lineage name
- **Purpose:** Stable identifier for cross-referencing

#### `is_subrace`
- **Type:** `boolean`
- **SRD Values:** `true` for Mountain Dwarf, Hill Dwarf, High Elf, Wood Elf; `false` for base lineages
- **SRD Source:** SRD structure (nested under parent lineage)
- **Transformation:** Detect from section hierarchy
- **Purpose:** Distinguish base lineages from variants

#### `parent_lineage`
- **Type:** `string` (optional)
- **Examples:** `"lineage:dwarf"` for Mountain Dwarf, `"lineage:elf"` for High Elf
- **SRD Source:** Parent lineage section
- **Purpose:** Link subrace to its base lineage

### Lineage Traits

#### `ability_score_increase`
- **Type:** `object`
- **SRD Format:** `"Your Constitution score increases by 2."` → `{Con: 2}`
- **Properties:** Ability abbreviations (Str, Dex, Con, Int, Wis, Cha) → integer bonus
- **Transformation:** Parse natural language to structured ability bonuses
- **Purpose:** Character creation stat calculations

#### `size`
- **Type:** `string`
- **SRD Values:** `"Medium"`, `"Small"`
- **SRD Source:** Size entry in lineage description
- **Purpose:** Game mechanics (space occupied, weapon size, grappling)

#### `speed`
- **Type:** `integer`
- **SRD Format:** `"Your base walking speed is 25 feet."` → `25`
- **Unit:** feet
- **SRD Source:** Speed entry in lineage description
- **Purpose:** Movement calculations in combat/exploration

#### `languages`
- **Type:** `array` of `string`
- **SRD Format:** `"You can speak, read, and write Common and Dwarvish."` → `["Common", "Dwarvish"]`
- **Transformation:** Parse language list from natural language
- **Purpose:** Communication abilities

#### `traits`
- **Type:** `array` of `object`
- **Properties:**
  - `name` (string): Trait name (e.g., "Darkvision", "Dwarven Resilience")
  - `description` (string): Full trait text from SRD
- **SRD Source:** Trait entries from lineage description
- **Purpose:** Special abilities and features

---

## Classes Dataset

Character classes with progression, features, and proficiencies.

### Core Identity

#### `id`
- **Type:** `string`
- **Pattern:** `class:<normalized_name>`
- **Examples:** `class:barbarian`, `class:wizard`, `class:fighter`
- **SRD Source:** Derived from class name
- **Purpose:** Stable identifier for cross-referencing

#### `hit_die`
- **Type:** `string`
- **SRD Values:** `"d6"`, `"d8"`, `"d10"`, `"d12"`
- **SRD Source:** "Hit Dice" or "Hit Points" section header (e.g., "Hit Dice: 1d12 per barbarian level")
- **Purpose:** HP calculation, multiclassing

#### `primary_abilities`
- **Type:** `array` of `string`
- **SRD Values:** `["Str"]` (Barbarian), `["Dex"]` (Rogue), `["Int", "Wis"]` (optional choices)
- **SRD Source:** "Quick Build" section recommendations
- **Purpose:** Character optimization guidance

### Proficiencies

#### `proficiencies`
- **Type:** `object`
- **Properties:**
  - `armor` (array): `["light", "medium", "shields"]` or `["all armor"]`
  - `weapons` (array): `["simple", "martial"]` or specific weapon names
  - `tools` (array): Tool proficiencies or `[]` if none
  - `skills` (object): `{choose: 2, from: ["Athletics", "Intimidation", ...]}`
- **SRD Source:** "Proficiencies" section of class description
- **Transformation:** Parse armor/weapon categories vs specific items; extract skill choice structure
- **Purpose:** Character creation and equipment choices

#### `saves`
- **Type:** `array` of `string` (length: 2)
- **SRD Values:** Two abilities from `["Str", "Dex", "Con", "Int", "Wis", "Cha"]`
- **Examples:** `["Str", "Con"]` (Barbarian), `["Int", "Wis"]` (Wizard)
- **SRD Source:** "Proficiencies" section, saving throw line
- **Purpose:** Saving throw bonuses

### Class Features

#### `features`
- **Type:** `array` of `string` (feature IDs)
- **Pattern:** `feature:<normalized_name>`
- **Examples:** `["feature:rage", "feature:unarmored_defense", "feature:reckless_attack"]`
- **SRD Source:** Class feature names from progression table and descriptions
- **Purpose:** References to full feature definitions (future features dataset)

#### `progression`
- **Type:** `array` of `object` (20 levels)
- **Properties:**
  - `level` (integer): 1-20
  - `features` (array): Feature names gained at this level
  - Additional class-specific fields (computed from progression table)
- **SRD Source:** Class progression table
- **Purpose:** Level-by-level advancement details

#### `tables_referenced`
- **Type:** `array` of `string` (table IDs)
- **Examples:** `["table:proficiency_bonus", "table:barbarian_progression", "table:spell_slots_full_caster"]`
- **Purpose:** Link to detailed progression tables in tables.json

### Spellcasting (Casters Only)

#### `spellcasting`
- **Type:** `object` (optional, only present for spellcasting classes)
- **Properties:**
  - `ability` (string): `"Int"`, `"Wis"`, or `"Cha"`
  - `spell_list` (string): `"wizard"`, `"cleric"`, `"bard"`, etc.
- **SRD Source:** "Spellcasting" feature description
- **Purpose:** Spell save DC and spell attack modifier calculations

#### `subclasses`
- **Type:** `array` of `string` (subclass IDs)
- **Pattern:** `subclass:<normalized_name>`
- **Examples:** `["subclass:path_of_the_berserker"]` (Barbarian), `["subclass:college_of_lore"]` (Bard)
- **SRD Source:** Subclass sections within class description
- **Purpose:** References to subclass definitions (future subclasses dataset)

---

## Atomic Reference Datasets (v0.20.0)

These datasets provide fundamental D&D game constants as standalone, cross-referenceable JSON files. Added in v0.20.0 to enable validation of type_id cross-references.

### Damage Types Dataset (13 items)

**File:** `damage_types.json`
**Schema:** `damage_type.schema.json` v1.0.0
**Source:** SRD 5.1 page 97

The 13 canonical D&D damage types with descriptions and examples.

#### Core Fields
- `id` - Namespaced identifier (e.g., `"damage_type:fire"`)
- `simple_name` - Normalized name (e.g., `"fire"`)
- `name` - Display name (e.g., `"Fire"`)
- `description` - Array of description paragraphs
- `examples` - Array of example sources (e.g., `["red dragon breath", "fireball spell"]`)
- `page` - SRD page number (97)

#### Canonical Types
**Physical (3):** bludgeoning, piercing, slashing
**Elemental (5):** acid, cold, fire, lightning, thunder
**Exotic (5):** force, necrotic, poison, psychic, radiant

### Ability Scores Dataset (6 items)

**File:** `ability_scores.json`
**Schema:** `ability_score.schema.json` v1.0.0
**Source:** SRD 5.1 pages 76-77

The 6 core D&D ability scores with descriptions and skill associations.

#### Core Fields
- `id` - Namespaced identifier (e.g., `"ability:strength"`)
- `simple_name` - Normalized name (e.g., `"strength"`)
- `abbreviation` - Three-letter code (e.g., `"STR"`)
- `name` - Display name (e.g., `"Strength"`)
- `description` - Array of description paragraphs
- `skills` - Array of skill IDs (e.g., `["skill:athletics"]`)
- `page` - SRD page number (76-77)

#### The Six Abilities
- **STR (Strength)** → Athletics
- **DEX (Dexterity)** → Acrobatics, Sleight of Hand, Stealth
- **CON (Constitution)** → No associated skills
- **INT (Intelligence)** → Arcana, History, Investigation, Nature, Religion
- **WIS (Wisdom)** → Animal Handling, Insight, Medicine, Perception, Survival
- **CHA (Charisma)** → Deception, Intimidation, Performance, Persuasion

### Skills Dataset (18 items)

**File:** `skills.json`
**Schema:** `skill.schema.json` v1.0.0
**Source:** SRD 5.1 pages 77-78

All 18 D&D skills with governing abilities and descriptions.

#### Core Fields
- `id` - Namespaced identifier (e.g., `"skill:athletics"`)
- `simple_name` - Normalized name (e.g., `"athletics"`)
- `name` - Display name (e.g., `"Athletics"`)
- `ability` - Governing ability name (e.g., `"strength"`)
- `ability_id` - Cross-reference to ability (e.g., `"ability:strength"`)
- `description` - Array of description paragraphs
- `page` - SRD page number (77-78)

#### Skill Groups
- **STR (1):** Athletics
- **DEX (3):** Acrobatics, Sleight of Hand, Stealth
- **INT (5):** Arcana, History, Investigation, Nature, Religion
- **WIS (5):** Animal Handling, Insight, Medicine, Perception, Survival
- **CHA (4):** Deception, Intimidation, Performance, Persuasion

### Weapon Properties Dataset (11 items)

**File:** `weapon_properties.json`
**Schema:** `weapon_property.schema.json` v1.0.0
**Source:** SRD 5.1 page 66

The 11 weapon properties that modify weapon behavior.

#### Core Fields
- `id` - Namespaced identifier (e.g., `"weapon_property:versatile"`)
- `simple_name` - Normalized name (e.g., `"versatile"`)
- `name` - Display name (e.g., `"Versatile"`)
- `description` - Array of description paragraphs
- `page` - SRD page number (66)

#### Properties
Ammunition, Finesse, Heavy, Light, Loading, Range, Reach, Special, Thrown, Two-Handed, Versatile

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

This dictionary reflects **Schema v1.3.0**. Changes to field meanings, transformations, or additions will be documented here with version annotations.

**Version History:**
- **v1.3.0** (2025-11-09): Extended creature extraction to pages 395-403, capturing 95 misc creatures (MM-A) and 21 NPCs (MM-B) for total of 317 creatures; implemented three-tier ID system (monster:/creature:/npc:) with separate indexing; added tables dataset (23 tables including 12 class progression), lineages dataset (13 lineages), classes dataset (12 classes), `aliases` field for all entities
- **v1.2.0** (2025-10-30): Added reference tables extraction
- **v1.1.0**: Structured objects (AC, HP, cost), namespaced IDs, `simple_name` everywhere
- **v1.0.0** (MVP): Basic extraction with string-heavy formats

See `SCHEMAS.md` for architectural evolution and versioning strategy.

---

## Datasets Summary

**v0.20.0 includes:**
- **317 Creatures** (in monsters.json, semantically separated):
  - **201 Monsters** - Main bestiary creatures (monster: prefix, pages 261-365)
  - **95 Misc Creatures** - Appendix MM-A awakened/summoned creatures (creature: prefix, pages 366-394)
  - **21 NPCs** - Appendix MM-B nonplayer characters (npc: prefix, pages 395-403)
- **111 Equipment** - Weapons, armor, adventuring gear
- **319 Spells** - Complete spell descriptions with structured effects
- **172 Rules** - Game mechanics and rules from 7 core chapters (76 pages)
- **38 Tables** - Reference tables (12 class progression + 26 general reference)
- **13 Lineages** - Character lineages (9 base + 4 subraces)
- **12 Classes** - Character classes with full progression
- **15 Conditions** - Game conditions from Appendix PH-A
- **3 Diseases** - Diseases with transmission and effects
- **246 Features** - Class features and lineage traits (154 class + 92 lineage)
- **240 Magic Items** - Magic items with rarity and attunement
- **14 Poisons** - Poisons with effects and costs

**v0.20.0 Atomic Reference Datasets:**
- **13 Damage Types** - Canonical D&D damage types with descriptions
- **6 Ability Scores** - Core abilities with skill associations
- **18 Skills** - All skills with governing abilities
- **11 Weapon Properties** - Weapon properties with behavior descriptions

**Total: 17 datasets, 1,548 items**

---

## See Also

- **SCHEMAS.md** - Schema versioning strategy and design patterns
- **ROADMAP.md** - Development roadmap and completed milestones
- **GPT_REVIEW_equipment_status.md** - Known issues and extraction challenges for equipment
- **PARKING_LOT.md** - Future enhancements and architectural decisions
- **Schema Files** - `schemas/*.schema.json` for formal JSON Schema definitions
