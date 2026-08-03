# Module Content Comparison

**Status:** Discovery artifact. This document compares representative publications,
defines consumer-oriented retrieval requirements, and sketches candidate output
shapes. It is not a frozen schema or implementation plan.

**Related:** [Module Content Discovery](module_content_discovery.md)

## Purpose

Turn the broad module-content research into a narrow, testable design target without
allowing Blackmoor's current story packs, a single source publication, or one ruleset
to define the result.

The comparison uses three anchor families:

1. a compact, portable location-based adventure published in multiple rulesets;
2. a 5e / 5th Edition anthology with a separate player-map publication; and
3. a BRP-family investigation distributed with GM maps, player handouts, plain-text
   handouts, and NPC portraits.

No source text or compiled module output belongs in this repository. Examples below
are synthetic and illustrate structure only.

## Corpus correction: product folders are not ruleset evidence

The file named `Grimmsgate.pdf` inside the “5th Edition Beast of a Bundle” directory
is a Swords & Wizardry edition. Its rules text and creature records use that
ruleset's vocabulary. The actual 5e publication is `Grimmsgate (5e) 2020.pdf` in the
Lost Lands 5th Edition bundle.

This is more useful than a single fixture would have been. Two editions of the same
adventure allow the discovery work to compare stable module content with different
mechanical projections. It also establishes a source-probing requirement:

> Directory names, filenames, and storefront bundle labels are hints. Ruleset
> identity must be established from publication evidence and confirmed during
> review.

## Comparison matrix

| Concern | Portable location adventure | 5e anthology plus maps | BRP investigation bundle |
|---|---|---|---|
| Publication unit | One adventure | One book containing twelve independent adventures | One main case file plus four companion publications |
| Play unit | Village, surrounding wilderness, and dungeon | Each one-shot is independently usable | One case with several investigative paths and conclusions |
| Primary structure | Physical containment and keyed locations | Publication hierarchy, then separate adventure units | Situations, evidence, choices, and procedural transitions |
| Secondary structure | Hooks, rumors, wandering encounters, and persistent village relationships | Setting-neutral guidance versus named-setting guidance | Location graph, NPC relationships, handout dependencies, and chase/combat branches |
| Entry | Several optional hooks or unstructured treasure-seeking | A short premise and immediate situation per one-shot | Assigned case, background checks, and an initial witness/location |
| Progression | Player-directed exploration | Usually compact situation-to-resolution flow | Explicit but non-linear progression diagram with repeated convergence |
| Locations | Village buildings, wilderness points, and dungeon rooms | Varies by one-shot; may be a vehicle, site, route, structure, or region | Real-world and fantastic locations with maps and evidence-bearing subareas |
| Read-aloud | Visually distinguished from GM explanation | Descriptive blocks mixed with concise setup and mechanics | Descriptive prose, dialogue prompts, procedures, and GM advice have distinct roles |
| People and creatures | Many common rules references plus named NPCs and module-specific monsters | Encounter-specific actors and creatures, often compactly presented | Dramatis personae, full cast records, witnesses, contacts, spirits, and adversaries |
| Tables | Rumors, wandering encounters, and treasure | Smaller and less consistent; varies by one-shot | Checks, outcomes, chase procedures, and reference material rather than dominant random tables |
| Rules references | Existing rules entities plus an appendix of module-supplied monsters | Existing 5e concepts plus publication-specific creatures, items, or hazards | BRP/Rivers skills, rolls, Luck, magic, opposed actions, chases, and additional rules |
| Setting portability | Explicitly designed to be renamed and placed into another campaign | Separate “use in your campaign” and named-setting guidance | Strong setting identity, institutions, procedures, and real geography |
| Open space | Hooks are optional; village decline and future use invite GM development | Adaptation guidance identifies required features and replaceable assumptions | Loose ends and optional approaches leave campaign consequences open |
| Assets | Embedded maps and illustration | Separate player-map publication associated by adventure | GM/player map variants, handouts, diagrams, portraits, and plain-text alternatives |
| Audience | Mostly GM, with read-aloud blocks for players | Main book for GM; map pack for players | Explicit GM-only, player-facing, and reusable/plain-text variants |
| Extraction advantage | Strong bookmarks in the actual 5e edition and consistent keyed identifiers | Strong top-level bookmarks for adventure boundaries | Strong bookmarks and author-supplied progression diagrams |
| Extraction challenge | Distinguishing shared adventure truth from edition-specific mechanics | Detecting independent submodules and matching each to a map | Reconstructing clue dependencies and matching numbered handouts across files |
| Runtime pressure | Fast “run this room/location” context | Mount whole publication but load one adventure independently | Retrieve bounded evidence, NPC, location, and next-step context without flattening the investigation |

## Findings

### 1. Publication, package, module, and play unit are different

The terms cannot safely be synonyms:

- A **publication** is a source artifact such as a PDF or EPUB.
- A **source bundle** is the set of publications and assets sold or distributed
  together.
- A **content package** is one compiled, mountable output with stable identity and
  version.
- An **adventure unit** is independently selectable play content inside a package.
- A **content entity** is an addressable person, place, clue, encounter, table,
  asset, or other record.

One source publication may contain many adventure units. One adventure may span
several source publications. A compiled package should preserve both facts.

### 2. Publication blocks and normalized entities are both required

Normalization cannot be all-or-nothing. The producer needs:

- ordered content blocks that preserve headings, prose roles, tables, images, and
  adjacency; and
- normalized entities and relationships that support efficient application queries.

When an importer confidently identifies a location, clue, or actor, it creates an
entity linked to its supporting blocks. When classification is uncertain, the blocks
remain usable and reviewable without inventing a domain record.

### 3. The neutral layer is not mechanics-free

The canonical dataset should preserve mechanical intent without pretending all
rulesets express it identically. Examples include:

- a challenge or hazard occurs here;
- this actor is the occupant or opposition;
- a check can reveal information;
- an event happens at a time interval;
- treasure or another reward is present; and
- a branch depends on an outcome or resource.

The ruleset projection supplies the executable expression: skill name, difficulty,
statblock, timing unit, roll method, damage, condition, or other native mechanic.

### 4. Module-supplied rules entities are not SRD entities

The 5e edition of the portable adventure refers to both existing SRD creatures and
eight appendix statblocks for creatures or named adversaries not found in that SRD.
Those records should exercise the same monster schema and runtime adapter without
being added silently to the core SRD dataset.

Three reference classes are needed:

| Class | Ownership | Example role |
|---|---|---|
| Core rules reference | Installed ruleset package | A standard creature, spell, skill, condition, or item |
| Module supplement | Module content package | A new monster, named adversary, item, hazard, or procedure supplied by the adventure |
| Module override or variant | Module content package | A deliberate local alteration of an otherwise known rule entity |

Module supplements should be namespaced to the package and use the same data shapes
where possible. Promoting a supplement into a reusable bestiary or other shared
library is a separate editorial action.

### 5. Ruleset conversion and content extraction must remain separable

The two editions of the portable adventure share much of their world and adventure
content but differ in statblocks, checks, time expressions, terminology, and some
treasure or balance details.

This suggests three outputs from comparison-capable import work:

1. a shared or rules-neutral module representation;
2. a source-edition rules projection; and
3. an optional comparison report identifying content and mechanical differences.

The first implementation does not need automatic edition conversion. It does need
an architecture that does not bake source-edition mechanics into every location or
prose block.

### 6. Setting portability is structured information

Genericity should not be inferred merely from missing setting fields. The source may
explicitly communicate what can change, what the adventure requires, and what named
setting details are optional.

A useful adaptation view may distinguish:

- required campaign features;
- replaceable names or setting bindings;
- optional hooks;
- named-setting placement guidance;
- follow-on opportunities; and
- facts that must remain true for the adventure to function.

This is a better home for material previously conflated with `author_tbd`. It is
intentional adaptation space, not unfinished authorship.

### 7. Several graph views must coexist

No single edge type can represent all three samples:

- **publication edges:** contains, follows, appears-in;
- **world edges:** inside, connected-to, route-to, near;
- **information edges:** clue-supports-revelation, known-by, found-at;
- **procedural edges:** on-success, on-failure, next, optional-next;
- **reference edges:** depicts, uses-rule, has-handout, features-actor; and
- **adaptation edges:** alternative-to, replaces, requires-feature.

Consumers may use a unified relationship collection, but every relationship needs a
type and graph/view classification so that physical travel is never mistaken for
narrative progression.

### 8. Asset identity includes role and audience

Matching an extracted image by filename is insufficient. An asset record needs to
answer:

- what it depicts or supports;
- whether it is a map, diagram, handout, portrait, illustration, or decoration;
- whether it is intended for GM, player, or shared use;
- whether it is a variant of another asset;
- which entities and content blocks refer to it;
- whether it is a whole publication page, embedded image, or crop; and
- whether map coordinates or regions link back to locations.

Plain-text handouts are semantic alternatives to designed player handouts, not
merely duplicate files. They may be better sources for extraction while the designed
version remains the player-facing asset.

## Retrieval scenarios and acceptance criteria

The canonical dataset is successful only if a consumer can ask useful questions
without knowing the source document layout.

### R1. Run the current location

**Request:** Given a location ID and audience, return the bounded context required to
present and adjudicate that location.

**Expected context:**

- simple and proper names with reveal constraints;
- player-facing description or read-aloud blocks;
- GM-only facts and secrets;
- occupants and possible arrivals;
- features, hazards, treasure, and relevant checks;
- connected locations and unresolved exits;
- local random tables or procedures;
- referenced rules entities; and
- associated map and handout assets.

**Acceptance:** A consumer does not need the whole publication or a hand-authored
scene conversion to run one keyed location.

### R2. Understand an actor

**Request:** Given an actor ID, return identity, role, agenda, knowledge, appearances,
relationships, rules projection, and audience-safe presentation.

**Acceptance:** The result distinguishes the persistent actor from each placement or
appearance and does not leak GM-only identity or knowledge into player context.

### R3. Trace information toward a conclusion

**Request:** Given a clue, revelation, or investigation state, return what supports
it, where that information can be found, who knows it, and alternative paths.

**Acceptance:** Missing one clue does not erase other authored paths, and physical
location links are not substituted for information dependencies.

### R4. Determine what can happen next

**Request:** Given current location, known facts, completed events, and active
conditions, return authored possibilities and clearly unresolved transitions.

**Acceptance:** The response distinguishes physical travel, procedural branches,
suggested GM options, and terminal outcomes. It does not invent a single mandatory
plot order from publication order.

### R5. Select safe and useful assets

**Request:** Given context and audience, return relevant assets and variants.

**Acceptance:** GM maps are not returned to players; player maps and handouts are
available independently; portraits resolve to actors; map anchors resolve to
locations; and a semantic/plain-text alternative can be selected when appropriate.

### R6. Resolve mechanics

**Request:** Given a content entity and installed ruleset, resolve core references,
module supplements, and local variants into executable mechanics.

**Acceptance:** Core and module-owned entities share a consumer interface while
retaining ownership and namespace. Unresolved mechanics remain explicit rather than
being discarded or fabricated.

### R7. Adapt the adventure to a campaign

**Request:** Return the adventure's required setting features, optional hooks,
replaceable bindings, named-setting guidance, and intentionally open follow-ons.

**Acceptance:** The consumer can adapt portable content without treating optional
setting material as canon or intentional openness as missing data.

### R8. Retrieve wider context without flooding runtime

**Request:** Given an entity or current play unit, return a bounded wider-context
summary: enclosing adventure, important relationships, downstream consequences, and
high-priority unresolved threads.

**Acceptance:** vd20 can understand the bigger picture without injecting every
content block and statblock into each turn.

## Candidate output shapes

These examples are structural probes. Names and content are synthetic.

### Candidate A: typed collections

```json
{
  "package_id": "package:sample_adventure",
  "ruleset": "dnd_5_1",
  "publications": ["publication:main_book", "publication:player_maps"],
  "adventures": ["adventure:sample_adventure"],
  "collections": {
    "blocks": "content/blocks.jsonl",
    "locations": "entities/locations.jsonl",
    "actors": "entities/actors.jsonl",
    "encounters": "entities/encounters.jsonl",
    "tables": "entities/tables.jsonl",
    "rules_supplements": "rules/supplements.jsonl",
    "assets": "assets/manifest.jsonl",
    "relationships": "indexes/relationships.jsonl"
  }
}
```

Strengths:

- straightforward validation and lazy loading;
- natural fit for typed vd20 queries;
- clear ownership of module rules supplements; and
- easy generation of indexes.

Risks:

- uncommon content may be forced into the wrong collection;
- relationships can become scattered across records; and
- incomplete semantic extraction may appear more confident than it is.

### Candidate B: publication spine with graph annotations

```json
{
  "publication_id": "publication:main_book",
  "spine": ["block:introduction", "block:village", "block:wilderness"],
  "annotations": [
    {
      "id": "annotation:location_gatehouse",
      "kind": "entity",
      "entity_type": "location",
      "targets": ["block:gatehouse_heading", "block:gatehouse_description"]
    },
    {
      "id": "annotation:route_gatehouse_inn",
      "kind": "relationship",
      "relationship_type": "connected_to",
      "from": "location:gatehouse",
      "to": "location:inn"
    }
  ]
}
```

Strengths:

- excellent source review and graceful partial extraction;
- all semantic claims remain attached to recoverable context; and
- supports several overlapping graph views.

Risks:

- runtime queries require more indexing;
- domain validation is less obvious; and
- consumers may accidentally depend on source-document structure.

### Candidate C: hybrid package

The current preference combines the previous shapes:

1. package manifest and publication records;
2. ordered, semantically typed blocks;
3. normalized typed entities linked to blocks;
4. one typed relationship collection;
5. module-owned rules supplements beside core rules references;
6. asset manifest with audience and variant relationships;
7. generated query indexes; and
8. optional build/review sidecar excluded from the runtime package.

Illustrative location entity:

```json
{
  "id": "location:village_gatehouse",
  "type": "location",
  "names": {
    "simple": "Ruined Gatehouse",
    "proper": "The Old North Gate"
  },
  "content_blocks": [
    "block:gatehouse_read_aloud",
    "block:gatehouse_gm_detail"
  ],
  "relationships": [
    "relationship:gatehouse_contains_guard",
    "relationship:gatehouse_connects_village"
  ],
  "mechanics": [
    {
      "role": "occupant",
      "ref": "rules:dnd_5_1:monster/veteran"
    }
  ],
  "assets": ["asset:village_map#region-gatehouse"],
  "stance": "source_explicit"
}
```

Illustrative module supplement reference:

```json
{
  "id": "module_rules:sample_adventure:monster/ash_crawler",
  "type": "monster",
  "ruleset": "dnd_5_1",
  "ownership": "module_supplement",
  "data_ref": "rules/supplements.jsonl#ash_crawler"
}
```

Illustrative adaptation record:

```json
{
  "id": "adaptation:sample_adventure",
  "setting_binding": "portable",
  "required_features": [
    "small_declining_settlement",
    "nearby_wilderness",
    "accessible_ruined_site"
  ],
  "hooks": ["hook:commission", "hook:local_property", "hook:open_exploration"],
  "replaceable_bindings": ["settlement_name", "regional_authority"],
  "open_questions": ["open_question:settlement_future"]
}
```

## Implications for Blackmoor and vd20

Blackmoor's existing loader assembles one fixed scene context containing description,
objectives, outcomes, rewards, choices, exits, activities, and initial actors. It
loads from a repository-relative story directory and assumes one authored scene per
bound location.

The comparison indicates several capabilities the future content-library boundary
must add:

- configurable mounted package roots;
- lookup by stable typed ID rather than story/module/scene file position;
- bounded context assembly driven by query and audience;
- more than one authored context or situation per physical location;
- persistent actors separated from placements;
- information and procedural graph traversal;
- core and module-owned rules resolution;
- asset selection and map-region lookup; and
- context summaries at location, adventure, and package scopes.

This does not require replacing Blackmoor's scene state. The scene remains useful as
mutable runtime focus. The content library should become the source from which scene
context is assembled.

## Initial vertical-slice target

The first slice should use the actual 5e edition of the portable location adventure
and prove only the following:

1. probe and confirm publication identity and ruleset;
2. recover the publication hierarchy and keyed location boundaries;
3. classify read-aloud, GM detail, table, map, and statblock blocks;
4. create location, actor, table, asset, and rules-reference entities;
5. separate core SRD monster references from module-supplied monster records;
6. preserve hooks, rumors, and explicit adaptation space;
7. build physical containment and connection relationships;
8. answer R1, R5, R6, R7, and R8 for one village location and one dungeon room; and
9. compile a consumer-neutral package plus a temporary Blackmoor projection.

It should not initially:

- convert between the Swords & Wizardry and 5e editions;
- model every optional narrative relationship;
- generate walls, lighting, or encounter automation;
- promote module monsters into the core SRD dataset;
- force every source block into a normalized entity; or
- replace Blackmoor's runtime scene/session models.

## Decisions reached

### D1. One selected ruleset lens per import

Module imports are compiled through one explicitly selected ruleset lens. Each
runtime package targets exactly one ruleset and schema version.

The shared foundation is intentionally limited to publication and general content
structures such as hierarchy, blocks, tables, assets, places, actors, relationships,
hooks, secrets, read-aloud material, and adaptation guidance. Mechanical recognition,
validation, references, and module supplements belong to the selected lens.

The initial implementation will not create multi-ruleset runtime packages, a
universal mechanics ontology, automatic edition conversion, or unimplemented
ruleset projections. It will define only a narrow lens interface so another ruleset
can be added later without replacing the publication pipeline.

Unrecognized mechanics must remain available as content or compiler-review items;
the selected lens must not silently discard them.

### D2. Module rules records are linked, resolved appendix entries

Locations, encounters, and actor placements refer to rules records by stable typed
ID. They do not embed or duplicate monster, NPC, item, hazard, or other rules data.
Module-owned records live once in a typed rules appendix within the package and use
the selected lens's native executable schema, carried inside a small package
ownership and version envelope.

The initial package model distinguishes three results:

1. a **reference** uses an installed ruleset record unchanged;
2. a **reskin** gives module-specific identity or presentation to unchanged rules;
   and
3. a **supplement** provides a complete module-owned rules record in the package
   appendix.

An importer or authoring tool may express a variant as a base rules reference plus
explicit changes. During compilation, however, that overlay is materialized as a
complete supplement record. The package may retain `derived_from` and change
metadata for explanation and future editing, but the initial runtime contract does
not require Blackmoor or vd20 to execute inheritance or patch semantics.

This directly covers the patterns already explored in Blackmoor: the Goblin Boss as
a reskin/reference, the Mole-Person as a complete supplement, and the Goblin Shaman
as a proposed derived variant that must compile into its own complete appendix
record.

Completeness is a package-build concern. If the selected lens cannot produce a
valid executable record, the source material remains available as content and a
review item rather than being mislabeled as a runnable supplement. Whether a
consumer can tolerate incomplete ad hoc records is outside this package contract.

### D3. The scene is a runtime composition, not a fixed publication record

A scene is the bounded context a consumer runs and mutates. It is assembled from a
location baseline, current campaign and site state, present actors, active
situations, active features, objects, and assets. The package supplies the
addressable ingredients and suggested compositions; Blackmoor or another consumer
owns the live scene and its consequences.

An encounter is therefore not a competing container beside the scene. It is a
situation definition that can introduce participants, triggers, behavior, stakes,
rewards, and consequences into the current scene. A keyed location may provide an
expected initial scene recipe, but that recipe is not a permanent snapshot: actors
may move, alarms may already be raised, random encounters may arrive, and prior
events may have changed the environment.

Locations, sites, and lairs may also contribute active behavior independently of
actors or encounters. These **active features** use a more specific kind such as
`hazard`, `weather`, `lair_effect`, `machinery`, `alarm`, `spreading_effect`, or
`schedule`. An active feature can record:

- its location, region, site, or lair scope;
- source-defined cadence and trigger procedure;
- random selection or escalation steps;
- effects and rules references;
- visible or discoverable presentation; and
- mutable state and possible interventions.

For example, a cave's steam vents remain active scene contributors whether the
party is exploring, fighting a wandering monster, or returning after the lair has
changed. Site-wide processes can apply across several child locations, while a
specific location can add, configure, activate, or suppress local behavior.

The importer must preserve an authored procedure even when the selected ruleset
lens cannot fully execute it. It may expose understood portions as structured data,
but it must retain the complete procedure as content or a review item rather than
forcing every active environment into one universal hazard formula.

### D4. Intentional openness is an adaptation point, not a missing value

The content model distinguishes an extraction gap, information absent from the
publication, and space intentionally left open for the GM or campaign. Intentional
creative space is represented as an **adaptation point**, not as `author_tbd`, an
error, or an incomplete entity.

An adaptation point can identify its purpose, constraints, suggestions, current
binding, and state. Its lifecycle may move from `open` to `suggested` to `bound`
without changing the underlying module content. It also records its stance:

- `source_explicit` when the publication identifies the flexibility;
- `source_inferred` when the importer can support the inference from the source; or
- `reviewer_proposed` when it is a later integration suggestion.

The importer automatically structures explicit adaptation guidance. Inferred
adaptation points are proposed for review and do not enter the runtime package as
accepted facts until approved. Extraction failures remain separate review issues;
they must not be converted into creative opportunities merely because a value is
missing.

### D5. Runtime source pointers are compact; extraction evidence is a sidecar

Runtime entities and content blocks retain stable package IDs and may carry a small,
optional source pointer containing the publication ID, section or heading, and
printed page label. This metadata helps a GM, reviewer, or developer return to the
relevant map key, table, statblock, or passage, but consumers do not require it to
run the content.

Detailed extraction evidence belongs in an optional build/review companion rather
than the runtime package. This companion may include source block IDs, document
coordinates, extraction confidence, transformations, rejected alternatives, raw or
unresolved blocks, and other information needed to review or repeat an import.

Runtime content must remain valid when the companion is absent. Conversely, the
companion uses stable runtime IDs to associate its evidence with compiled content
without making extraction machinery part of the vd20 content-library contract.

### D6. Scene context is an assembled working set with lookup escape hatches

The content library can assemble a bounded scene context containing enough material
to run the current location until the party meaningfully transitions elsewhere. It
is a generated consumer view, not a second canonical copy of the module and not a
closed runtime boundary.

The assembled context normally includes:

- the current location and relevant parent-site summary;
- player-facing and GM-facing content blocks;
- effective active features, including applicable site or lair features;
- present actors and their resolved rules records;
- active and immediately triggerable situations;
- relevant objects, clues, treasure, checks, and tables;
- current state supplied by the consumer;
- usable assets and map regions; and
- exits with conditions and short destination summaries rather than complete
  neighboring locations.

Direct dependencies needed by immediately possible outcomes can be prefetched into
the context. Optional or more distant content remains addressable by stable ID.
Blackmoor may perform targeted lookups, expand the context, or request a refreshed
assembly whenever play moves unexpectedly or state changes materially.

This design reduces routine chains of small lookups while preserving the normalized
package as the authority. A consumer that prefers direct library traversal is not
required to use the assembled view.

### D7. Builds are reproducible; campaign state belongs to the consumer

Re-importing is a producer concern. Given the same source material, selected
ruleset lens and version, import configuration, and accepted review decisions, a
build should produce semantically identical package content. Incidental build
timestamps or extraction details must not change entity identity or normalized
meaning.

Package metadata follows the established SRD-bundle pattern and separates package
identity, content version, package schema version, selected ruleset and lens
version, source fingerprint, and builder version. Content hashes can identify
changes, but stable entity IDs are based on source identity and reviewed bindings,
not mutable prose: correcting a room description does not create a new room.

The compiled module represents baseline publication content. Campaign and session
progression belongs to Blackmoor or another consumer, including defeated or moved
actors, collected treasure, triggered features, opened routes, bound adaptation
points, and other consequences. Consumer state refers to stable package entity IDs
but remains outside the package. Re-importing does not inspect, reconstruct, or
merge campaign history.

Migrating an active campaign to a changed package release is a future consumer or
content-library concern. The initial importer provides the stable identities and
version metadata needed to make that possible but does not implement a campaign
overlay compatibility or migration system.

## Open decisions for later review

No blocking decisions remain for drafting the initial Grimmsgate package slice.
Additional questions discovered by the draft should be added here rather than
silently resolved in implementation.
