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

### Not every prefix is equally wrong

Two classes of problem, and only one of them breaks anything:

| Class | Examples | Effect |
| --- | --- | --- |
| **One kind split across prefixes** | monster/npc/creature, item/magic_item | **Breaks queries.** A kind cannot be enumerated without knowing every prefix it hides under. |
| **One prefix at debatable granularity** | table, poison, disease | Enumeration still works; the type is merely coarser or finer than ideal. |

The sharper test is therefore: **does one kind live under more than one prefix?**
That is the query-breaking case and the only one this proposal changes.

Genuinely structural, with their own distinct fields, and not to be touched:
`spell` (level, school, casting, components), `condition`, `skill`, `ability`,
`damage`, `weapon_property`, `class`, `lineage`.

### Two layers, two identity rules

`table:` and `rule:` looked like the same defect. They are not. They belong to a
different layer, and that layer has a different - legitimate - identity rule.

| Layer | Examples | Identity rule |
| --- | --- | --- |
| **Entity** | creature, spell, item, class, lineage | Must survive reclassification. Never encodes document location. |
| **Publication artifact** | tables, rules passages, content blocks | Position *is* the identity. Document location is correct here. |

This is the same split the module-content work already makes between content
blocks and normalized entities, and which the comparison document lists as
finding 2: both are required, and neither substitutes for the other. Tables were
built deliberately as a collection for consumers who want to reach any table
readily - that is supporting material, in the sense that an appendix reference or
a figure is supporting material. `rule:<section>/<subsection>` is a passage, and a
passage is identified by where it sits, exactly as the importer identifies one
with `pub:the_village/map_key`.

So neither needs restructuring. The only change worth making is cosmetic: make
the slug **opaque** rather than parseable, so nothing is tempted to split on `/`
to recover the section. `table:` already carries `section` as a field, which is
the pattern.

The lesson generalizes: before calling an id defective, establish which layer the
record belongs to. Document position in an entity id is a defect; document
position in a publication-artifact id is the point.

### Genuine granularity questions, deferred

- `poison:` carries `cost`, which is an item property. A poison and a healing
  potion are the same kind of thing - a consumable with an effect - differing on
  an axis that is beneficial-versus-harmful. That is a field, like
  magical-versus-mundane. Folding both into `item:` would make "every consumable"
  a single query.
- `disease:` looks mergeable into `condition:` and probably **is not**. In 5e a
  *condition* is a term of art: a closed list with defined mechanical behaviour. A
  disease is not a member of that list; it is an affliction that may impose
  conditions. They are siblings, not subtype and supertype, and merging them would
  flatten a real rules distinction to satisfy tidiness. Recorded so the split is
  not "fixed" later by someone reading only the first half of this document.

Neither breaks a query today. Folding debatable churn into a change with a crisp
justification weakens the case for both.

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

## The wider blindspot: single-source assumptions

The id scheme is one instance of a larger gap. A producer with one source and one
consumer never has to answer *does this compose with something else?* Identity,
collision and uniqueness are not wrong in that world - they are simply never
exercised. Approaching the same data as a producer of a SECOND source is what
made the question visible.

This is not a one-off. The same class of defect has already been hit once inside
a single bundle: `index.json`'s `by_name` was first-write-wins, and 85 feature
names and 17 rule names collided. `by_name_all` was added to expose every
matching id. That was an assumption of uniqueness that held until it did not,
found late, and fixed at the symptom.

Worth auditing deliberately rather than waiting to be surprised again:

| Assumption | Status |
| --- | --- |
| An id identifies one thing | **Broken.** This proposal. |
| A display name identifies one thing | **Broken once already**, patched with `by_name_all`. Cross-source it is worse. |
| One ruleset bundle is mounted | Untested. `rulesets/` already holds `srd_5_1` and `srd_5_2_1`; nothing says whether they can coexist. |
| Indexes describe everything | Per-bundle by construction. A merged index is undefined. |
| Provenance is implicit | `_meta.pdf_sha256` per dataset answers "from which build", not "which source asserted this" once several are mounted. |

The general shape: anywhere the producer says "the", ask whether it survives
"several".

## Where the habit may have come from

Untested, but worth recording because it shapes where else to look: the producer
may have inherited its id shape from its first consumer. Ids that describe *where
something was printed* are the view of someone reading the document, not someone
modelling the domain - which is what you get when a data model is derived from a
reader rather than from the entities themselves.

If that is what happened, the same instinct will show up wherever else the
producer took its shape from a consumer's convenience rather than from the source
material.

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

**Decision: documentation, not compatibility machinery.** No alias map, no
redirect table, no dual-emit period. The project is small enough that the cost of
carrying a compatibility layer forever exceeds the cost of a documented rename
handled once. Building migration machinery would also mean keeping the defective
scheme alive inside the producer, which is the thing this change exists to stop.

What ships instead:

- One MAJOR bump covering both layers, with a migration note listing every
  changed id and the field that replaced the dropped prefix.
- `docs/COMPATIBILITY.md` gains the durable form of the rule: ids are opaque
  outside their source, and no consumer should parse one for meaning.
- Consumers migrate on their own schedule by pinning the previous release. The
  bundle is versioned and tagged; nothing forces an upgrade.

## Recommended order

1. Qualify module supplement payload ids - smallest, fixes a live latent
   collision, no consumer impact.
2. Make `rulesReference` structured `{source, entity_type, local_id}`. Retires
   the open cross-bundle reference question properly instead of by convention.
3. Write the "never parse an id" rule into the architecture docs.
4. Bundle normalization as one MAJOR release, with a migration note rather than
   an alias map. Scope it to the query-breaking cases only:
   `monster:`/`npc:`/`creature:` -> `creature:` + `category`, and
   `item:`/`magic_item:` -> `item:` + `magic`.

Steps 1-3 are producer-side and pre-1.0. Step 4 is the one that needs a consumer
conversation.
