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

## Repository boundary

The committed fixture is synthetic but structurally equivalent to the selected
source slice. Source-specific analysis remains in the paper prototype under
`docs/planning/local/`, which is gitignored because it quotes publication
content.
Actual imported publication records should be generated only into a private,
ignored build location; public test fixtures should remain synthetic or otherwise
independently authored.

## Next design choices

The next schema pass should resolve only the decisions now supported by evidence:

1. make anonymous actor-group identity explicit;
2. define a small structured predicate shape and its evaluation owner;
3. split the monolithic package schema into maintainable contracts;
4. settle cross-bundle rules-reference syntax; and
5. define the dependency-edge annotations used by scene-context assembly.

Importer implementation should still wait until the revised schemas and the same
five retrieval tests agree.
