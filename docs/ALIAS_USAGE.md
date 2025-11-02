# Alias Usage Guide

This document demonstrates how to use the comprehensive alias system in the SRD dataset.

## Overview

The alias system works at three levels:

1. **Index-level (terminology)**: Category mappings like "races" → "lineages"
2. **Entity-level**: Search terms for compound items like "tankard" → "flask_or_tankard"
3. **Indexer-level**: Automatic lookup expansion in `by_name` indexes

## Index-level Aliases (Terminology)

Located at the top level of `index.json`:

```json
{
  "aliases": {
    "races": "lineages",
    "race": "lineage"
  },
  "lineages": {
    "by_name": { ... },
    "by_size": { ... }
  }
}
```

### Consumer Usage Pattern

```javascript
// Load index
const index = require('./index.json');

// Helper function to resolve terminology aliases
function getEntityIndex(type) {
  // Check if type is an alias
  const canonical = index.aliases[type] || type;
  return index[canonical];
}

// Usage examples
const lineages = getEntityIndex("races");     // → index.lineages
const lineages2 = getEntityIndex("race");     // → index.lineages
const lineages3 = getEntityIndex("lineages"); // → index.lineages (no alias needed)

// Access data
console.log(lineages.by_name["dwarf"]);       // → "lineage:dwarf"
```

## Entity-level Aliases

Entities can have an optional `aliases` array for alternative search terms:

```json
{
  "id": "item:flask_or_tankard",
  "simple_name": "flask_or_tankard",
  "name": "Flask or tankard",
  "aliases": ["flask", "tankard"]
}
```

### Indexer Expansion

The indexer automatically expands `by_name` lookups to include all aliases:

```json
{
  "equipment": {
    "by_name": {
      "flask or tankard": "item:flask_or_tankard",
      "flask": "item:flask_or_tankard",    // From aliases
      "tankard": "item:flask_or_tankard"   // From aliases
    }
  }
}
```

### Consumer Usage

```javascript
// Direct lookup works with any alias
const flaskId = index.equipment.by_name["flask"];     // → "item:flask_or_tankard"
const tankardId = index.equipment.by_name["tankard"]; // → "item:flask_or_tankard"
const fullId = index.equipment.by_name["flask or tankard"]; // → "item:flask_or_tankard"

// All return the same ID - consumer can then fetch entity data
```

## Complete Example

```javascript
const fs = require('fs');

// Load dataset files
const index = JSON.parse(fs.readFileSync('./index.json', 'utf8'));
const equipment = JSON.parse(fs.readFileSync('./equipment.json', 'utf8'));

// Helper to resolve terminology aliases
function getEntityIndex(type) {
  return index[index.aliases[type] || type];
}

// Helper to get entity by name (handles aliases automatically)
function findEntity(category, searchName) {
  const categoryIndex = getEntityIndex(category);
  const entityId = categoryIndex.by_name[searchName.toLowerCase()];

  if (!entityId) return null;

  // Find entity in appropriate data file
  const entities = JSON.parse(fs.readFileSync(`./${category}.json`, 'utf8'));
  return entities.items.find(e => e.id === entityId);
}

// Search using old terminology
const dwarf = findEntity("races", "dwarf");
console.log(dwarf.name); // → "Dwarf"

// Search using new terminology
const elf = findEntity("lineages", "elf");
console.log(elf.name); // → "Elf"

// Search using entity alias
const flask = findEntity("equipment", "tankard");
console.log(flask.name); // → "Flask or tankard"
```

## Schema Definition

All entity schemas include an optional `aliases` field:

```json
{
  "properties": {
    "simple_name": {
      "type": "string",
      "pattern": "^[a-z0-9_]+$"
    },
    "aliases": {
      "type": "array",
      "items": {"type": "string"},
      "uniqueItems": true,
      "description": "Alternative names or search terms"
    }
  }
}
```

## Current Implementation Status

### ✅ Completed
- Index-level terminology aliases (`races` → `lineages`, `race` → `lineage`)
- Entity-level schema support (all schemas have optional `aliases` field)
- Automatic indexer expansion (`by_name` includes entity aliases)
- Documentation in `meta.json` for reference

### ⏳ Pending
- Entity-level data population (e.g., `flask_or_tankard` with `aliases: ["flask", "tankard"]`)
- Additional compound equipment items (`jug_or_pitcher`, etc.)

## Best Practices

1. **Always use lowercase** for lookups in `by_name` indexes
2. **Check aliases first** when resolving category names
3. **Entity aliases are optional** - only use for compound items or historical terms
4. **Avoid alias conflicts** - each alias should point to exactly one entity
5. **Document aliases** - make it clear why an alias exists

## FAQ

### Why are aliases in both index.json and meta.json?

- `index.json`: **Functional** - used for actual lookups and searches
- `meta.json`: **Documentation** - describes the dataset's terminology choices

### Can aliases be bidirectional?

No. Aliases map old → new or alternative → canonical. The system is designed for one-way resolution.

### What happens with alias conflicts?

The indexer tracks conflicts and skips duplicate entries. Check `index.conflicts` for any collisions.

### Do I need to add aliases to every entity?

No. Only add aliases when:
- Entity has compound names ("flask or tankard")
- Historical terminology needs mapping
- Common search terms differ from official name
