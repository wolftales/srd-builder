# Entity Identity Across Sources

**Status:** Proposal. Not implemented. Records a defect found by building the
module importer, and what to do about it.

**Related:** [Module Import Status](module_import_status.md) ·
[Comparison](module_content_comparison.md)

## How this surfaced

The module importer had to *construct* a reference to an SRD creature. It could
not. Given the name "Veteran" there is no rule that yields `npc:veteran` rather
than `monster:veteran` or `creature:veteran`, so the importer reads the built
bundle and looks the id up.

Producing content is a much better test of an identity scheme than consuming it.
The SRD pipeline never had to ask which namespace a name belonged to, so the
defect stayed invisible for the bundle's whole life.

## The defect

An id like `npc:veteran` is asked to answer three questions at once:

1. **Which mounted content set?** Not answered at all.
2. **What kind of thing is it?** Answered, but conflated with:
3. **Where was it printed?** `monster:` / `npc:` / `creature:` are the SRD's
   three document sections, not three kinds of entity.

Point 3 is the root. The prefix is a table of contents wearing a type system's
clothes.

### It is a habit, not an incident

An audit of all 1,693 bundle records found the same pattern three times:

| Pattern | Records | What is encoded |
| --- | --- | --- |
| `monster:` / `npc:` / `creature:` | 317 | which chapter it was printed in |
| `item:` / `magic_item:` | 499 | whether it is magical - a property, not a kind |
| `feature:barbarian:rage`, `rule:<section>/<subsection>` | 412 | owner and document hierarchy, in parseable form |

Genuinely structural, and not to be touched: `spell`, `condition`, `skill`,
`lineage`, `class`, `table`, `ability`, `poison`, `damage`, `disease`,
`weapon_property`.

### The test

> Would this record's id have to change if an editor reclassified it, without
> changing what it is?

If yes, that information is a **field**, not a type.

- A veteran moving from the NPC appendix into the monsters chapter renames it.
- An item reprinted as mundane, or a mundane item made magical, renames it.
- A feature shared with a second class renames it.
- A reorganized rules section renames it - and this already happened. The
  migration notes record rules ids changing shape when document structure moved.

## Why it gets worse with many sources

- **Same concept, different prefix.** This SRD files a veteran under `npc:`.
  Another publisher files theirs under `monster:`. Nothing can match them without
  per-publisher special cases.
- **Collision.** Two modules supplying `monster:goblin_shaman`, or SRD 5.1 and
  5.2 mounted together, both offering `monster:goblin`.
- **Churn propagates.** Every reclassification inside any source dangles every
  consumer reference to it.

The importer already produces a latent instance: a supplement's envelope id is
package-qualified (`module_rules:grimmsgate_5e:monster/...`) while its payload id
is bare (`monster:...`). A consumer indexing by payload id - the natural thing,
since that is what SRD records look like - silently overwrites one with the
other.

## Proposal

Two layers. The first is non-breaking and needed regardless; the second is a
breaking change to the SRD bundle worth taking.

### Layer 1: references carry their source, and local ids are opaque

A reference is three parts, not one string:

```
{ source: "srd_5_1", entity_type: "creature", local_id: "npc:veteran" }
```

- **source** - which mounted set. Solves collision and multi-version mounting.
- **entity_type** - ours, closed, small. What consumers switch on.
- **local_id** - opaque. Never parsed for meaning.

Making local ids opaque is the important half. It means another publisher's
taxonomy costs nothing: you never have to interpret `npc:` versus `monster:`
again, because you stop reading the prefix at all.

**Rule to enforce: never parse an id for meaning.** If code splits on `:` to
decide behaviour, that information should have been a field. That is exactly what
the importer was forced to do.

### Layer 2: normalize the bundle's own ids

Layer 1 makes the mess survivable. It does not make it good, and preserving a
known-defective scheme only because it exists is not a reason.

```
monster: / npc: / creature:   ->  creature:  + category: monster | npc | beast
item: / magic_item:           ->  item:      + magic: true | false
feature:barbarian:rage        ->  feature:barbarian_rage  + class_ref: class:barbarian
rule:<section>/<subsection>   ->  rule:<stable_slug>      + section: <field>
```

Ids become `<entity_type>:<opaque_slug>`, where entity_type is a small closed set
of structural kinds and the slug may contain underscores for uniqueness but is
never parsed. Compound slugs stay - `feature:barbarian_rage` - because two
classes can both have "Extra Attack". The change is that it becomes opaque rather
than structured, so nothing is tempted to split it.

## What the breaking change buys

Not tidiness. Five concrete things:

1. **Ids survive editorial reclassification.** The documented rules-id churn
   would not have happened. This is the main prize: ids stop being a function of
   document layout.
2. **One index per kind.** A consumer wanting every creature stops needing to
   know it must union three prefixes. The importer's own
   `CREATURE_NAMESPACES = ("monster", "npc", "creature")` constant deletes, and
   creature resolution becomes `(source, "creature", name)` with no lookup.
3. **Cross-source queries work without taxonomy knowledge.** Any publisher's
   creature is `creature:`.
4. **Consumers stop parsing ids.** The `feature:class:name` shape actively
   invites splitting on `:`; removing the structure removes the temptation.
5. **Categories become queryable.** `category` and `magic` as fields support
   filters that today require prefix-matching, and support records that are
   legitimately both.

## Migration

The strongest argument for doing this now is not the defect - it is that **a
breaking change is already coming.** Layer 1 changes how module packages
reference the bundle. Doing Layer 2 separately makes consumers migrate twice.

- Ship an alias map in the bundle: `old_id -> new_id`, so consumers migrate
  incrementally rather than atomically.
- Precedent exists: monster records already carry `aliases`, and the repo has
  done a documented id migration before.
- One MAJOR bump covering both layers. Update `docs/COMPATIBILITY.md` to say ids
  are opaque outside their source, which is the durable version of this rule.

## Recommended order

1. Qualify module supplement payload ids - smallest, fixes a live latent
   collision, no consumer impact.
2. Make `rulesReference` structured `{source, entity_type, local_id}`. Retires
   the open cross-bundle reference question properly instead of by convention.
3. Write the "never parse an id" rule into the architecture docs.
4. Bundle normalization plus alias map, as one MAJOR release, coordinated with
   the Blackmoor integration.

Steps 1-3 are producer-side and pre-1.0. Step 4 is the one that needs a consumer
conversation.
