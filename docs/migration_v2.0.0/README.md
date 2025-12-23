# Monster Schema v2.0.0 Migration Examples

This directory contains before/after examples showing the migration from schema v1.5.0 to v2.0.0.

## Key Changes in v2.0.0

### 1. Structured Speed Object
**Before (v1.5.0):**
```json
{"speed": {"walk": 30}}
```

**After (v2.0.0):**
```json
{
  "speed": {
    "walk": 30,
    "swim": 0,
    "fly": 0,
    "burrow": 0,
    "climb": 0,
    "hover": false
  }
}
```

### 2. Structured Senses Object
**Before (v1.5.0):**
```json
{"senses": {"darkvision": 60}}
```

**After (v2.0.0):**
```json
{
  "senses": {
    "darkvision": 60,
    "blindsight": 0,
    "tremorsense": 0,
    "truesight": 0,
    "passive_perception": 9
  }
}
```

### 3. Structured Armor Class
**Before (v1.5.0):**
```json
{"armor_class": {"value": 15, "source": "leather armor, shield"}}
```

**After (v2.0.0):**
```json
{
  "armor_class": {
    "value": 15,
    "type": "leather armor, shield",
    "type_id": "leather_armor"
  }
}
```

### 4. Structured Actions
**Before (v1.5.0):**
```json
{
  "name": "Scimitar",
  "description": ["Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) slashing damage."]
}
```

**After (v2.0.0):**
```json
{
  "name": "Scimitar",
  "description": ["Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) slashing damage."],
  "attack_bonus": 4,
  "damage": [
    {
      "damage_dice": "1d6+2",
      "damage_type": "slashing",
      "damage_type_id": "slashing"
    }
  ],
  "range": {"reach": 5}
}
```

### 5. Cross-Reference Type IDs
All damage types, armor types, and condition references now include normalized `*_id` fields for easier cross-referencing.

## Example Files

- `aboleth_v1.5.0.json` / `aboleth_v2.0.0.json` - Complex creature with multiple damage components
- `goblin_v1.5.0.json` / `goblin_v2.0.0.json` - Simple humanoid
- `adult_red_dragon_v1.5.0.json` / `adult_red_dragon_v2.0.0.json` - Dragon with multiple movement speeds and immunities

## Validation

All v2.0.0 examples validate successfully against `schemas/monster.schema.json`:

```bash
python3 -c "import json, jsonschema; schema = json.load(open('schemas/monster.schema.json')); example = json.load(open('docs/external/api/migration_examples/goblin_v2.0.0.json')); jsonschema.validate(instance=example, schema=schema)"
```
