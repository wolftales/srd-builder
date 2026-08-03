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

*Done. See "Groups became records, and the last exemption went away" below.*

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

*Done. See "The split, and what it proved" below.*

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

### Stance was two different questions wearing one name

Three vocabularies had drifted apart: `placement` used
`source_baseline`/`source_conditional`/`reviewer_proposed`, `adaptationPoint`
and `relationship` used `source_explicit`/`source_inferred`/`reviewer_proposed`,
and the discovery document proposed a fourth set.

They could not be reconciled by choosing one list, because they were not all
answering the same question. Two axes had been conflated:

- **warrant** — did the source state this, did the importer work it out, or did
  a reviewer add it; and
- **modality** — is this baseline or conditional, open or bound.

`placement` proved it. Its `stance` offered `source_baseline` versus
`source_conditional` while its `presence` field already offered
`usual`/`initial`/`conditional`. The same distinction was stored twice, and only
one of the two fields was named for what it actually carried.

`stance` now means warrant and nothing else. Modality stays on the field that
names it: `presence` for placements, `state` for adaptation points. One
`contentStance` definition is referenced everywhere, and a test rejects any
definition that declares a stance-like vocabulary of its own.

The vocabulary stays at three values. A fourth distinction between "reconstructed
from source evidence" and "suggested by the compiler" is a confidence judgement,
and D5 already assigns confidence to the review companion — which carries a
`confidence` field today. Runtime warrant stays coarse; the sidecar owns nuance.

`intentionally_open` was also rejected as a stance value. It is not warrant: it
is what an `adaptation_point` is, and its `state` field already says so.

### Warrant is required, on every normalized entity

Eleven definitions carried no stance at all. All of them do now, and it is
required rather than optional, because at unbounded module count an optional
provenance field is an absent one — there is no review capacity to fill it in
later. An importer must make a claim about every record it emits.

### A generated summary was load-bearing on a location

Extending stance surfaced a modelling error. Blocks of type `summary` are
importer-generated abstracts, not the publication's own prose, so they are
`source_inferred` — but they sat inside `location.content_refs` alongside real
source blocks. Stripping inferred records therefore broke a location.

The scene-context schema had already made the right distinction:
`site_context.summary_ref` is its own field, separate from content refs. The
package schema had not. Locations now carry an optional `summary_ref`, so
dropping a generated abstract removes an optional reference instead of editing
the list of the source's own prose.

One consequence is worth stating plainly: the assembled scene context depends on
a generated summary, so a consumer that refuses inferred content gets no site
summary. That is a property of the generated view, not of the package, and the
package remains fully runnable without it.

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

### The split, and what it proved

The 1,588-line schema is now seven files averaging about 220 lines:

| File | Holds |
| --- | --- |
| `common` | identifiers, source pointers, warrant, names |
| `content` | publication spine and normalized content entities |
| `situations` | situations, active features, triggers, effects |
| `relationships` | typed relationships and their graph views |
| `assets` | visual assets and map regions |
| `rules` | selected-lens references, supplements, procedures |
| `module-package` | the envelope and package metadata |

Two boundaries were added to the sketch above. `rules` earned its own file
because D1 puts mechanics behind the selected ruleset lens, and making that a
file boundary means adding a second ruleset touches one file. `relationships`
earned one because it is the only collection that spans every view by design, and
the package envelope depends on its vocabulary; content should not own the graph.

The layering came out flat and is now asserted: `common` is a leaf, every domain
file depends on `common` alone, and only the envelope composes them. No domain
file reaches another. That flatness is the property worth protecting — it is what
keeps the lens boundary real.

The split was also a test of the derive-from-schema approach adopted earlier.
Twenty-one existing checks were rewritten across seven files by changing exactly
one assertion: the one pinning a literal JSON pointer,
`{"$ref": "#/$defs/contentStance"}`, which the split turned into a file-qualified
pointer. Everything else kept working because it matched on definition names
rather than locations. Definition names must therefore stay globally unique
across the files, which is now asserted rather than assumed.

The lesson generalizes: assertions about *where* something is declared break
under repackaging; assertions about *what* is declared survive it.

### Groups became records, and the last exemption went away

Of the three models sketched above, the fixture chose one on evidence rather than
taste. `group:v4_occupants` is listed as a participant by the situation at its own
location, and referenced from two others: the alarm response one room away sets
its intent, and the neighbouring lair's reinforcement condition tests whether it
is still alive. No single situation owns it, so it cannot be addressed as a child
of one. Nesting was out; a first-class collection was in.

The scene context had already reached the same conclusion without saying so: it
lists groups in `dependency_closure.actor_groups` and keys `state_inputs` by group
identity. The consumer view treated groups as addressable entities while the
package still treated them as a shape implied by a recipe.

An `actor_group` record now owns its own composition — quantity and the rules
reference that says what its members are. Participants reference an occupant
instead of declaring one, so a participant is a role plus exactly one of
`actor_ref` or `group_ref`. Composition lives in one place, which is what lets
consumer state say two of five were defeated without the recipe and the state
disagreeing.

`placement` was generalized rather than duplicated. It already modelled "who is
where at baseline, with what presence modality and what warrant"; it now binds
either a named actor or a group. Groups therefore get a baseline location to be
moved away from, which is what the original requirement asked for, without a
second placement concept.

The payoff is a deletion. Reference integrity no longer carries a namespace
exemption: the check asserts that every in-package reference resolves, full stop.
A misspelled `group_ref` used to be silently legal because the namespace was
excused and participant recipes declared their own referents. It now fails.

Two follow-ons worth noting rather than acting on. `quantity` already accepts a
dice string as well as an integer, so a source that says "2d4 goblins" is
representable, but nothing yet exercises it. And a group has no display name: a
consumer refers to it by role and by the creature its `rules_ref` resolves to,
which is enough for this slice and may not be for a module with two distinct
bands of the same creature in one location.

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

1. define a small structured predicate shape and its evaluation owner;
2. settle cross-bundle rules-reference syntax, including how the lens resolves a
   creature name to the correct bundle namespace; and
3. define the dependency-edge annotations used by scene-context assembly.

Settled since the first pass: stance unification and coverage (one vocabulary,
warrant only, required on every normalized entity), attribute-level warrant
(`inferred_fields`, failing closed), relationship views and vocabulary, the schema
split, and explicit actor-group identity.

Every in-package reference now resolves with no exemptions, so reference
integrity is a closed property rather than a mostly-closed one.

### Warrant needed a second scale: the record and the attribute

Record-level warrant could not express a record whose existence is stated but
whose classification was guessed. A content block lifted verbatim from a shaded
box is `source_explicit`, yet its `audience` value — read-aloud versus GM-only —
is usually read off typography. Marking the whole block `source_inferred` was
both alarming and uninformative and would strip real prose; marking it
`source_explicit` overstated confidence in exactly the field whose failure puts
GM text in front of players.

Records now carry an optional `inferred_fields` list naming their own properties
that the source did not establish. It is meaningful only where `stance` is
`source_explicit`: if the record itself was inferred, so is everything about it.

The two scales are orthogonal, and the tests hold both:

- stripping inferred **records** keeps a block with an inferred **attribute**,
  because the prose is real; and
- the player projection withholds that block anyway, because its `audience` was
  not established.

That fail-closed rule is the point of the field. A guessed `audience` is never
trusted toward players regardless of the guessed value, since guessing
"player_safe" wrong is how GM text reaches the table.

D5's objection — that attribute detail belongs in the review companion — was
weighed and rejected for this case. The companion is optional and may be absent
at runtime, but a consumer deciding what to show a player needs this signal every
time. Confidence *scores* still belong in the companion; whether a value has any
source warrant is a runtime concern.

A bare list was chosen over a per-field warrant map. A map would also let a
reviewer mark a single corrected field, but a reviewer-corrected value is *more*
trustworthy, not less, so it does not belong in a "do not trust this" signal. If
reviewer field-level overrides ever need representing, the list becomes a map.

The fixture exercises two cases drawn from findings already recorded here: the
inn read-aloud, whose player-safety came from typography, and the site map, whose
region-to-location bindings cannot be recovered from page extraction alone
(17.6). The scene context selects a map region from that second one, so the
binding it hands a consumer is explicitly untrusted.

Importer implementation should still wait until the revised schemas and the
retrieval tests agree. The information layer and R3 are explicitly out of scope
until the investigation slice supplies evidence.
