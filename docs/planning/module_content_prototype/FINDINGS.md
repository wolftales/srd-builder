# Prototype Findings

Status: results of the first executable schema experiment

## Outcome

The candidate package, scene context, review companion, and two package-local
monster supplements validate successfully. Generic lookup helpers answer all five
target scenarios without branching on publication keys, room names, or package
identity:

1. assemble the inn's baseline content, actors, object, and rules references;
2. enter the alarm room before an encounter exists;
3. trigger the alarm and discover its cross-room consequences;
4. include or suppress reinforcements from current group state; and
5. resolve a module-owned monster through the package appendix.

The full existing SRD-builder test suite also passes with the prototype present.

## What held up

### The hybrid package is queryable

The publication spine and typed collections coexist without duplicating the same
record. Ordered reading uses publication nodes; runtime lookup uses typed IDs and
relationships.

### A scene context works as a generated view

The alarm room context contains the current location, site summary, effective
features, immediately triggerable situation, exits, asset region, and a bounded
dependency closure. Nothing prevents a later targeted lookup.

### Site-scoped active features compose correctly

A generic ancestor walk activates both the room-local alarm and the site-wide
wandering check. No scene- or room-specific rule is needed.

### Rules references and supplements can share one resolution path

Core records resolve through reference entries. Module-owned records resolve
through a small ownership envelope whose `data` value validates against the
existing selected-ruleset monster schema. Locations and situations do not care
which resolution mode supplied the result.

### Consumer state remains separate

Baseline placements and situation recipes are package content. The reinforcement
query uses supplied current group state; it does not rewrite the package or infer
campaign history.

## Revisions exposed by execution

### Anonymous actor groups need an explicit contract

The fixture currently introduces `group:*` identity through situation participant
recipes. That is sufficient for the experiment, but implicit declaration is too
subtle for a production contract. Schema drafting should choose one explicit
model:

- a first-class actor-group collection;
- an encounter or situation participant-template collection; or
- a declared group identity nested within its owning situation with a defined
  address syntax.

The group must be stable enough for consumer state to say that its occupants moved,
fled, or were defeated without requiring named NPC records for interchangeable
creatures.

### Executable conditions cannot remain prose strings

The first fixture draft expressed reinforcement eligibility as a sentence. The
working schema now separates `if_ref` from `if_state`, allowing generic evaluation.
Human-readable preconditions can remain useful guidance, but any condition that
controls an executable effect needs structured operands and a declared evaluation
owner.

### A prefetched random table needs its outcome dependencies

Including the wandering table alone does not make the scene context self-contained.
The context must include or resolve every rules record that an immediate table roll
can select. The prototype verifies this closure explicitly.

### Active features need capabilities, not one exclusive subtype

The alarm is simultaneously an alarm and a hazard; the wandering process is both a
schedule and an encounter check. The experimental `kinds` list works, although a
production schema may replace it with capability-specific fragments if those kinds
need distinct required fields.

### The selected lens includes procedures as well as statblocks

The 5e fixture needs ability checks, skill and tool references, DCs, chance rolls,
and durations measured in rounds. A ruleset lens limited to creature parsing would
not be enough for module content.

### The monolithic schema should be split before production

One schema with local definitions made the experiment easy to run and review as a
single contract. It is already too large to maintain comfortably. A production
draft should separate shared identifiers/source pointers, content entities,
situations and active features, assets, and the package envelope while retaining
cross-schema validation tests.

## Revisions from the second pass

### Relationship views are normative; relationship types are vocabulary

The first draft used a flat closed enum of five relationship types. The fixture
used three of them. `located_at` duplicated the `placements` collection and
`supports` had no entities to connect — both were written by listing plausible
edges rather than by asking what the slice needed. Meanwhile `signal_reaches`,
the one edge the slice actually forced into existence, belonged to no obvious
category.

The comparison document's finding 7 already required this: a relationship needs a
type *and* a graph/view classification, so physical travel is never mistaken for
narrative progression. The schema now separates the two:

- `view` is closed, required, and normative. Consumers switch on it.
- `type` is an extensible vocabulary scoped within a view, and every type used
  must be declared in `meta.relationship_vocabulary`.

That answers the comparison document's open question 5. Views are normative;
types are vocabulary. A later investigation slice can add information edges
without a schema version bump, while a package stays self-checking because it
declares its own vocabulary.

Deriving the view from endpoint types was rejected. The same endpoint pair
legitimately carries different views: two locations can be connected (walkable),
lead to one another (procedural), and follow one another (publication order).
Collapsing those is the `next_scene` conflation this model exists to avoid.

### Inference must not be load-bearing

Relationships now carry a `stance`. This matters more here than anywhere else in
the package because module imports are unbounded — there will never be enough
review capacity to audit inferred structure by hand, so the boundary between what
the source stated and what the importer worked out has to be machine-maintained.

The fixture marks `contained_by` edges `source_inferred`, because they duplicate
`location.parent_ref` rather than reporting something the source said. A test
strips every non-explicit relationship and asserts the package still validates,
still answers the inn scenario, and still composes site-scoped active features.
Containment survives on `parent_ref`, so nothing that was merely inferred is
required to run the content.

This invariant is the machine substitute for review, and it should hold for every
entity type once `stance` is carried more widely — it is currently only on
placements, adaptation points, and relationships.

### Three stance vocabularies now exist

`placement` uses `source_baseline`/`source_conditional`/`reviewer_proposed`,
while `adaptationPoint` and `relationship` use
`source_explicit`/`source_inferred`/`reviewer_proposed`, and the discovery
document proposes a fourth set for runtime content stance. Unifying these is a
schema-drafting decision, not something to settle silently.

### Internal and cross-bundle references were indistinguishable

Every reference was typed `#/$defs/id`, so nothing said which ones must resolve
inside the package and which resolve against the installed ruleset. Adding
`externalRef` made the reference-integrity check derivable from the schema, and
immediately showed that four cross-bundle references named records that do not
exist: the bundle uses `npc:`, `creature:`, and `item:` where the fixture assumed
`monster:` and `tool:`. An importer cannot construct these by naming convention;
the namespace is a per-bundle lookup that the selected lens has to perform.

### The information view arrived from a dungeon, not an investigation

`signal_reaches` is classified as an information edge: an alarm changes what
actors elsewhere know and how they act. That classification is provisional and
the investigation slice should confirm it. It is worth recording because the
information graph was expected to be an investigation-only concern, and a keyed
dungeon produced one anyway.

## Deferred: the information layer and R3

There are no clue, revelation, or information-dependency entities, so R3 (trace
information toward a conclusion) is neither modeled nor tested. This is deferred
deliberately rather than overlooked.

Designing an information graph against a dungeon fixture would be guessing. The
Chaosium investigation slice is the sample that produces the evidence, and the
schema split does not depend on the answer — information entities land inside the
existing content-entity boundary and need no new one. The `information` value is
reserved in the relationship view enum so the omission stays visible.

When that layer is drafted, `stance` on information edges is not optional.
Clue-to-revelation links are the least mechanically recoverable structure in a
module: containment comes from headings and map keys, statblocks from layout, but
"this detail supports that conclusion" is usually implicit prose. That is where
importer inference will concentrate, and therefore where unmarked inference would
do the most damage.

## Repository boundary

The committed fixture is synthetic but structurally equivalent to the selected
source slice. Source-specific analysis remains in
`docs/planning/module_content_paper_prototype.local.md`, which is gitignored
because it quotes publication content.
Actual imported publication records should be generated only into a private,
ignored build location; public test fixtures should remain synthetic or otherwise
independently authored.

## Next design choices

The next schema pass should resolve only the decisions now supported by evidence:

1. make anonymous actor-group identity explicit;
2. define a small structured predicate shape and its evaluation owner;
3. split the monolithic package schema into maintainable contracts;
4. settle cross-bundle rules-reference syntax, including how the lens resolves a
   creature name to the correct bundle namespace;
5. define the dependency-edge annotations used by scene-context assembly;
6. unify the stance vocabularies and decide which entity types must carry one; and
7. decide whether `stance` is required rather than optional — at unbounded module
   count an optional provenance field is an absent one.

Importer implementation should still wait until the revised schemas and the
retrieval tests agree. The information layer and R3 are explicitly out of scope
until the investigation slice supplies evidence.
