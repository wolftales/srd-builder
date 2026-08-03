# Module Content Discovery Notes

**Status:** Working hypotheses for research. This is not a schema, RFC, or
implementation plan. Findings from Blackmoor, real module documents, SRD-Builder,
and external content systems are expected to revise or replace these ideas.

**Related:** [Module Content Comparison](module_content_comparison.md)

## Purpose

Explore whether SRD-Builder's document and prose extraction capabilities can grow
into a module-content producer that emits a useful, reasonably standardized content
dataset. Blackmoor and the future vd20 engine are important consumers, but their
current bespoke story packs must not define the universal source model.

The desired result should preserve enough of an adventure's bigger picture for an
application to navigate, retrieve, reason over, and adapt the material efficiently.
It need not reproduce the source document with archival rigor.

## Working principles

1. **Blackmoor is evidence, not specification.** Reuse its proven concepts and
   consumption needs without assuming its current scene-oriented format is the
   correct general module format.
2. **Discovery precedes schema freeze.** Draft models are probes. They must remain
   easy to discard when real module structures or established systems suggest a
   better approach.
3. **Module conversion has more latitude than SRD production.** Multiple extraction
   methods, inference, restructuring, summarization, and human review are acceptable
   when they improve playability and coherence.
4. **Accuracy and fidelity are distinct.** The dataset should clearly distinguish
   source-established content from optional expansion space or compiler suggestions,
   but it does not require exhaustive field-level provenance.
5. **Source model and consumer model may differ.** A reusable module dataset may be
   compiled or projected into a Blackmoor/vd20 runtime pack rather than sharing one
   universal shape.
6. **Large-context retrieval is a first-class use case.** The dataset should let an
   application understand both the current local situation and the wider adventure
   context without repeatedly reparsing the full document.
7. **Maps and images are content.** The design must investigate extraction,
   identification, association, cropping, metadata, and delivery—not treat visual
   material as a later attachment.
8. **Ownership remains open.** The implementation might remain in SRD-Builder, move
   into a reusable library, or eventually live partly inside vd20. Boundaries should
   preserve those options.

## Useful concepts already demonstrated by Blackmoor

- Story flow and physical-location topology are different graphs.
- Persistent people, places, factions, and setting truths should not be owned by one
  scene or story merely because they appear there.
- Lore identity and mechanical statblocks have different responsibilities.
- Authored/source content is immutable during play; campaign/session overlays own
  change.
- Exact references and role/tag-based loose stitching are both useful.
- Objectives should be optional and advisory rather than presumed to exist in every
  module section.
- A destination can be resolved, explicitly terminal, or honestly unresolved.
- Source truth, player knowledge, and unresolved creative space are distinct.
- Ruleset identity and mechanics must cross an explicit adapter boundary.

## Terminology hypothesis: intentionally open content

Blackmoor's current `author_tbd` name is too implementation-oriented and can imply
unfinished work. Some entries are intentionally left open so a campaign, GM, player,
or adaptation can supply an answer.

Candidate concepts to test:

- `open_threads`
- `open_questions`
- `customization_points`
- `adaptation_space`
- `unfixed_details`
- `campaign_prompts`

These may not be synonyms. Research should determine whether the model needs separate
categories, for example:

- an intentionally unresolved truth;
- a suggested expansion opportunity;
- a campaign customization slot;
- a compiler inference needing review; and
- a source ambiguity that should remain ambiguous.

## Candidate pipeline—not a committed architecture

```text
source document
  -> document structure
  -> module content dataset
  -> consumer-specific projection or pack
  -> immutable loaded content
  -> mutable campaign/session state
```

Possible responsibilities to investigate:

- document blocks, hierarchy, tables, and visual assets;
- keyed areas, physical links, and map associations;
- people, creatures, factions, encounters, treasure, and rules references;
- read-aloud text, GM information, secrets, rumors, and player handouts;
- adventure-level arcs, chapters, situations, hooks, and possible transitions;
- retrieval summaries and indexes at several scopes;
- ruleset-specific recognition and adaptation;
- compiler suggestions and deliberately open customization space; and
- projection into Blackmoor/vd20 content and session initialization.

## Questions for discovery

### Blackmoor and vd20

- What content does session bootstrap require, and what is needed only on demand?
- Which content is copied into session state versus referenced from an immutable
  library?
- Which current story-pack concepts generalize, and which exist only because the two
  authored stories were built around scenes and objectives?
- What enhancements would let Blackmoor consume external content libraries or
  compiled packs efficiently?
- Does the engine need a content query/retrieval interface rather than direct file
  knowledge?

### SRD-Builder

- Which extraction stages are genuinely reusable for arbitrary prose documents?
- Is its current raw/intermediate representation rich enough for hierarchy, spatial
  layout, tables, and images?
- Which modules are SRD-specific and which could become a document-processing core?
- Can output builders be plugged in without turning SRD-Builder into an application
  runtime dependency?

### Real modules

- What recurring document structures appear across dungeon, investigation, sandbox,
  city, campaign, and rules-light adventures?
- How are keyed areas, chapters, encounters, random tables, secrets, handouts, and
  appendices represented?
- How much structure is communicated visually rather than through headings?
- What information is useful globally, locally, and only during a specific encounter?

### Maps and images

- Can an image be identified as a map, illustration, handout, diagram, token, or
  decorative element?
- How are map labels and keyed locations linked to text sections?
- Should extracted assets remain whole, be cropped, or support both?
- What stable references and dimensions are required by consumers?
- Which image understanding belongs at import time versus runtime?

### External models

- How do established VTTs package adventures, scenes, journals, actors, items,
  compendia, maps, and cross-document references?
- Which systems separate source/reference content from instantiated world state?
- What indexing and linking approaches scale without forcing every consumer to load
  the complete adventure?
- Is there a credible interchange standard to adopt, or only useful patterns to
  borrow?

## Research outputs

The discovery pass should produce:

1. A comparison of Blackmoor's current model with representative real modules and
   established digital-content systems.
2. A recurring-content taxonomy with counterexamples and genre-specific variations.
3. Two or more candidate dataset/pack architectures rather than one premature answer.
4. A content-library hypothesis explaining immutable sources, retrieval, consumer
   projections, and live campaign state.
5. Recommendations for Blackmoor/vd20 capabilities that should change independently
   of the module producer.
6. A small vertical-slice proposal only after the preceding findings are reviewed.

## Discovery pass: evidence collected

### Blackmoor session state

Blackmoor's session state is already close to the right runtime boundary. It is a
composition root for the active scene, actors, time, ruleset/configuration, party,
encounter, lore, and story progress. It also carries references such as `module_id`
and `location_ref`. This argues against copying the entire adventure into session
state.

The cleaner direction is:

- an immutable, queryable content library owns published module content;
- session/campaign state owns live selections, progress, discoveries, changes, and
  overlays; and
- stable content IDs connect the two.

The current implementation still exposes repository-specific assumptions and
bespoke story shapes. Those are consumer constraints to remove or isolate, not
features to copy into the producer's canonical dataset.

### SRD-Builder extraction capability

SRD-Builder has useful low-level machinery for spans, fonts, bounding boxes,
columns, heading inference, tables, paragraph assembly, probing, and deterministic
post-processing. Those are a credible starting point for a reusable publication
processing core.

Its current high-level prose path is not a general module extractor. It relies on
known headers, fixed page ranges, SRD-specific fonts, and source-tuned thresholds.
The reusable opportunity is therefore below the current `ProseExtractor`: retain
the document/layout primitives and add source profiles and semantic compilation
above them.

### Representative local modules

The local corpus demonstrates several materially different structures:

- A classic adventure combines background, adventure phases, keyed locations,
  boxed text, random encounters, stat lines, cross-references, and appendices.
- A modern one-shot combines a concise premise, an immediately playable situation,
  statblocks, and explicit alternatives for fitting the adventure into a campaign.
- A megadungeon emphasizes terse numbered keys, factions, rumors, area-level random
  tables, and dense cross-map references across hundreds of locations.
- A solo adventure is fundamentally a directed conditional graph: checks, resource
  changes, outcomes, and links to numbered entries.
- At least one professionally produced module is an image-only PDF. A usable import
  path must support OCR and vision-based classification rather than assuming a text
  layer.
- Some products separate adventure text, maps, player maps, handouts, tokens, and
  VTT assets into multiple files. The import unit is therefore often a bundle, not a
  document.

This invalidates a single scene/objective hierarchy as the general source model.

### EPUB as a source format

A local module supplied in both PDF and EPUB revealed that EPUB already exposes a
publication manifest, ordered spine, table of contents, XHTML structure, embedded
assets, stable anchors, and hyperlinks between solo entries. When equivalent source
formats are available, extraction should prefer the richest structure rather than
defaulting to PDF.

The producer should be thought of as a **publication importer** with several source
front ends:

- EPUB/HTML: preserve explicit hierarchy, anchors, links, and asset relationships;
- tagged or text PDF: reconstruct structure from layout and document metadata;
- image-only PDF: OCR plus visual/layout interpretation;
- asset bundle: inventory and associate maps, handouts, tokens, and variants; and
- optional structured/VTT sources: map their existing entities and references.

### External content-system patterns

The strongest recurring ideas from established systems are:

- Foundry bundles heterogeneous documents into an Adventure while preserving IDs
  and links. Its Compendia are typed, indexed collections that are loaded on demand.
- Foundry Scenes model maps as coordinate spaces with several optional runtime
  layers. Notes connect coordinates to journal content; walls, lights, regions,
  sounds, and tokens remain distinct layers.
- Fantasy Grounds distinguishes read-only reference/module content from editable
  campaign data. Its modules contain multiple typed collections, while the campaign
  owns live tools and state.
- Roll20 modules instantiate a prepared game populated with pages, journals,
  handouts, and characters. This is useful as a deployment target, but it conflates
  source content and one live world more than the desired canonical model should.
- EPUB provides a strong packaging precedent: manifest, metadata, reading order,
  navigation, and bundled resources without claiming semantic understanding of the
  adventure.
- IIIF provides a useful visual-content precedent: a canvas has dimensions, content
  and derived material can be layered as annotations, and a rectangular region can
  be addressed independently of the whole image.
- Node-based scenario design distinguishes authored plot order from a network of
  situations and information paths. Redundant clue paths also imply that clues and
  revelations deserve explicit relationships in investigative material.
- RPG-Schema is worth watching as a vocabulary source, especially for portable game
  entities, but its universal-ontology ambition is larger and less mature than this
  project's immediate module-content need. It should inform vocabulary comparison,
  not become a dependency or force JSON-LD into the runtime.

## Revised working model

### A module has several simultaneous structures

The evidence supports preserving at least four views rather than forcing one tree:

1. **Publication structure** — source order, chapters, sections, blocks, appendices,
   and asset placement.
2. **World structure** — locations, containment, routes, map anchors, factions, and
   persistent entities.
3. **Narrative/information structure** — situations, hooks, clues, revelations,
   secrets, rumors, dependencies, and possible transitions.
4. **Procedural structure** — numbered entries, checks, outcomes, resource changes,
   triggers, and conditional branches.

These may share entities and typed edges, but they must remain independently
queryable. A dungeon may be dominated by world structure; an investigation by
information structure; a solo module by procedural structure; and a conventional
book still needs publication structure for faithful retrieval and review.

### Content blocks and domain entities are complementary

A robust intermediate dataset likely needs both:

- semantically typed content blocks such as prose, read-aloud, instruction, table,
  statblock, callout, list, image, and caption; and
- normalized domain entities such as location, actor, faction, item, encounter,
  clue, revelation, event, table, objective, and asset.

Blocks preserve what the importer found and provide useful context even when
semantic normalization is incomplete. Entities and relationships make the material
efficient for an engine to query. This dual representation avoids an all-or-nothing
semantic extraction requirement.

### Fidelity without archival provenance

`author_tbd` currently conflates several different situations. A smaller and more
useful vocabulary would separate:

- `open_questions`: facts the module intentionally does not settle;
- `adaptation_hooks`: explicit or compiler-suggested ways to fit or extend content;
- `customization_points`: values a campaign is expected to choose;
- `source_ambiguities`: incompatible or genuinely unclear source statements; and
- `compiler_review`: low-confidence extraction or interpretation that should not be
  presented as authored content.

Runtime-facing content only needs a light **content stance**, for example:

- `source_explicit`
- `source_reconstructed`
- `compiler_suggested`
- `intentionally_open`

Detailed page coordinates, extraction diagnostics, confidence traces, and review
artifacts can live in an optional build sidecar. They should not burden the pack
that vd20 reads. This preserves the useful boundary—what the module establishes,
what was reconstructed, and what is optional—without reproducing the SRD pipeline's
provenance burden.

### Maps and visual assets

Visual material should be modeled first as assets, with map behavior added through
optional layers. A candidate asset record needs:

- stable ID, kind, file or URI, media type, dimensions, and description;
- audience/visibility such as GM, player, or shared;
- associations to publication blocks and domain entities;
- variants such as GM/player, labeled/unlabeled, full/cropped, or print/VTT;
- optional source region when the asset is extracted from a page; and
- derived material such as OCR text, labels, or a thumbnail.

A map-capable asset can then add a coordinate space, scale/grid metadata, and
anchors or regions linked to locations, encounters, handouts, or notes. Walls,
lighting, fog, token placement, and automation should be optional consumer/runtime
layers—not required for a valid imported map.

## Candidate pack architectures

### Candidate A: typed bundle with shared references

A manifest identifies the module and lists typed collections and assets. Collections
can be separate JSON files for locations, actors, encounters, content blocks,
tables, assets, and relationships. Stable IDs and a small cross-reference contract
connect them. Search and graph indexes can be generated alongside the authoritative
content.

Advantages: simple tooling, lazy loading, easy inspection, good fit for vd20.
Risk: too many rigid top-level types can make uncommon module structures awkward.

### Candidate B: document spine plus typed graph overlay

The primary representation is an ordered hierarchy of content blocks and assets.
Semantic entities and typed graph edges point into that spine rather than replacing
it. Consumers can use structured entities where extraction succeeded and fall back
to source-context blocks everywhere else.

Advantages: graceful partial extraction, strong reviewability, broad genre support.
Risk: the consumer query layer must reconcile the publication and semantic views.

### Current preference: a hybrid of A and B

Use a package manifest and typed collections, but retain a publication spine as one
of those collections and let entities point to blocks. Generate indexes and
consumer projections rather than making every consumer understand build-time
detail. This is a canonical internal dataset, not a promised universal interchange
standard and not Blackmoor's existing pack format.

## Content-library hypothesis

The content library is not another name for a story folder. It is the runtime-facing
service between compiled packages and the engine. Its responsibilities would be:

- mount one or more immutable packages;
- resolve stable IDs and typed references;
- retrieve an entity or a bounded context bundle;
- query by type, tag, location, participant, visibility, or relationship;
- traverse world, narrative, information, and procedural links;
- serve assets and audience-appropriate variants; and
- expose package/version identity so campaign overlays can remain stable.

Blackmoor/vd20 should talk to this interface rather than know where or how package
files are laid out. Session state stores active IDs and mutable overlays, not copies
of the whole library.

## Ownership direction

The least constraining near-term boundary is:

- **SRD-Builder owns production:** source probing, extraction, normalization,
  review, and compilation into the canonical module dataset.
- **vd20 owns consumption:** a small content-library interface, package loading,
  query behavior, visibility, and runtime overlays.
- **Blackmoor consumes a projection:** initially it may use a Blackmoor-specific
  projection or adapter while its direct content-library capabilities mature.

vd20 should not import SRD-Builder as an application dependency. If a second producer
or substantially different consumer appears, the neutral dataset models and reader
can be extracted into a small shared library then. Creating that shared project now
would freeze abstractions before the first vertical slice has tested them.

## Likely Blackmoor/vd20 enhancements

These changes appear useful independently of the final producer schema:

1. Replace repository-relative content discovery with configurable package roots or
   mounted content sources.
2. Introduce a content-library/query boundary instead of direct file knowledge.
3. Standardize typed IDs and reference resolution across content kinds.
4. Keep immutable content references separate from campaign/session overlays.
5. Allow world, narrative/information, and procedural relationships to coexist.
6. Add asset lookup, variants, coordinate anchors, and audience visibility.
7. Request bounded context bundles rather than eagerly loading a whole module into
   prompts or session state.
8. Treat ruleset mechanics as adapter output while keeping rules-neutral content
   available.
9. Preserve `source_explicit`, reconstructed, suggested, and open-content boundaries
   where they matter to GM or engine behavior.

## Remaining research before a vertical slice

- Compare a conventional investigation with solo branching to test clues,
  revelations, NPC agendas, timelines, and conditional flow.
- Decide whether encounters are authored content records, executable preparations,
  or both with separate definitions and instances.
- Test the hybrid dataset against three deliberately incompatible samples: a keyed
  dungeon, a one-shot/investigation, and a solo branching module.
- Define success measures for retrieval: what context vd20 needs for a current
  location, an NPC, a clue, a transition, and an adventure-wide planning request.

## Research reference set

### Local project material

- `/Users/wolftales/git/blackmoor/content/`
- `/Users/wolftales/git/blackmoor/docs/`
- `/Users/wolftales/git/blackmoor/docs/reference/session_state.schema.md`
- `/Users/wolftales/git/srd-builder/archive/docs/PROSE_EXTRACTION_FRAMEWORK.md`
- `/Users/wolftales/git/srd-builder/src/srd_builder/utils/prose.py`
- `/Users/wolftales/git/srd-builder/src/srd_builder/utils/pdf_layout.py`
- `/Users/wolftales/git/srd-builder/src/srd_builder/utils/pdf_probe.py`

### External models and documentation

- Foundry VTT: Content Packaging Guide, Adventure Documents, Compendium Packs,
  Scenes, Map Notes, Scene Regions, Canvas Layers, Walls, and Lighting.
- Fantasy Grounds: Module Data File Overview, Developer Guide—Building Modules,
  Campaign Builder, and Image Asset Pack Creation.
- Roll20: Modules and Compendium documentation.
- W3C: EPUB 3.3 and EPUB 3 Overview.
- IIIF: Presentation API 3.0.
- Chaosium: Rivers of London free resources, *The Domestic*, and the multi-file
  handouts pack description.
- The Alexandrian: Node-Based Scenario Design and the Three Clue Rule.
- RPG-Schema.org vocabulary and project overview.

## Recommended development sequence

The first implementation slice should use 5e / 5th Edition material because
SRD-Builder already understands the ruleset vocabulary. Candidate discovery must
include both labels: publishers and bundle filenames use “5e,” “5th Edition,” and
“Fifth Edition” inconsistently for the same rules family. This isolates module
structure, publication extraction, and package design before adding a new ruleset
adapter. Chaosium then becomes the deliberate generalization test rather than the
source of every unknown at once.

### First 5e / 5th Edition slice: Grimmsgate

Use the 26-page `Grimmsgate (5e) 2020.pdf` from the Lost Lands Adventure for 5th
Edition bundle. It is small but structurally complete: introduction, background,
hooks, rumor table, village, wilderness, dungeon, wandering encounters, keyed
locations, read-aloud blocks, treasure, creature statistics, maps, and conclusions.

Do not use the file named `Grimmsgate.pdf` from the “5th Edition Beast of a Bundle”
directory as the 5e fixture. Publication evidence identifies it as a Swords &
Wizardry edition. The paired editions are valuable later for isolating neutral
adventure content from ruleset projections, but bundle and filename labels are not
sufficient ruleset identification.

This is a better first compiler fixture than a large campaign because success can be
reviewed exhaustively while still testing publication blocks, locations, containment,
cross-references, random tables, encounters, assets, and ruleset references.

### Second 5e / 5th Edition slice: Prepared 2

Use `Prepared 2- A Dozen One-Shot Adventures for 5th Edition.pdf` with
`Prepared 2 Map Pack.pdf`. This tests a publication containing twelve independently
usable submodules, a separate player-map bundle, varied adventure structures, and
explicit “In Your Campaign” adaptation guidance.

The importer should be able to represent the whole publication as one package while
also making each one-shot independently addressable and loadable. This is an early
test of the distinction between publication, package, module, and adventure unit.

### Third slice: Chaosium generalization

After those two 5e / 5th Edition fixtures, use *Going Underground* to introduce
BRP/Rivers of London mechanics and a clue-driven investigation. That slice should
prove that rules-neutral module content survives a new ruleset adapter rather than
merely confirming that the importer recognizes 5e conventions.

### Later 5e / 5th Edition counterexamples

- `Mystery at Ravenrock (5e).pdf` combines investigation, optional encounters,
  keyed dungeon and castle areas, NPCs, monsters, equipment, magic items, and player
  maps in a compact 28-page package.
- `The Sunken Library of Qezzit Quire.pdf` is a useful minimal nine-page fixture for
  fast tests, but it is too narrow to define the initial content model.
- `Splinters of Faith 5e.pdf`, its 97-page map book, and virtual handouts are a later
  stress test. At more than 500 pages, they should validate scale rather than shape
  early abstractions.

## Forgotten Realms Vault: a neighboring content track

The Forgotten Realms Vault bundle is primarily a fiction corpus—mostly EPUB novels,
with a few PDF editions—not a module collection. It should not be used as a 5e
adventure-import fixture merely because the setting is associated with D&D.

It may later be highly relevant to a broader lore/publication pipeline. It can test
chapter structure, characters, places, events, chronology, viewpoint, aliases,
relationships, and retrieval across a large shared setting. That is adjacent to the
module-content library, but it introduces interpretive narrative extraction and
world-model reconciliation rather than authored adventure mechanics. Keeping it as
a separate research track will help reveal which content-library primitives truly
generalize beyond modules.

## Chaosium bundle findings and candidate vertical slices

The Humble Bundle under
`/Users/wolftales/Documents/humble_bumble/HUMBLE RPG BUNDLE- FROM RIVERS TO`
`FJORDS - EXPLORE THE WORLDS OF BASIC ROLEPLAYING BY CHAOSIUM/` is a strong test
corpus. It contains core rules, short and long adventures, a solo case, maps,
player and GM variants, plain-text handouts, NPC portraits, pregenerated
characters, reference booklets, character sheets, and correction documents.

### Recommended first Chaosium slice: Going Underground

Use the 42-page `CHA3202_-_Going_Underground.pdf` together with its four companion
packs:

- `Going_Underground_-_Gamemaster_Maps_and__Diagrams.pdf`
- `Going_Underground_-_NPC_Portrait_Pack.pdf`
- `Going_Underground_-_Plain_Text_Handouts.pdf`
- `Going_Underground_-_Players_Handouts_and_Maps.pdf`

This is the best first sample because it is compact but structurally rich. The main
book contains a plot-progression diagram, branching investigation sections,
location prose beside maps, GM advice, handout references, dramatis personae, cast
records, conclusions, and loose ends. The companion files test bundle discovery,
asset roles, GM/player visibility, asset variants, and cross-document association.

The first slice should prove publication blocks, bundle manifests, entity and asset
IDs, typed links, content stance, and bounded retrieval. It should not yet attempt
automatic walls, lighting, encounter execution, or a universal rules ontology.

### Recommended contrast slice: The Cursed Farm

Use the 16-page `CHA2042_-_Age_of_Vikings_-_The_Cursed_Farm.pdf` and its separate
map pack. This is a short scenario in the same broad BRP family but a different
genre and presentation style. It combines read-aloud text, keyed places, cultural
and skill checks, creature statistics, hit locations, treasure, and a labeled GM
map. It tests whether the module dataset remains ruleset-aware without becoming
Rivers-of-London-shaped.

### Recommended procedural slice: The Domestic

Use the 34-page `The_Domestic_Rivers_of_London_RPG_Solo.pdf`. Its numbered entries,
checks, resource changes, class-dependent choices, destinations, and trace numbers
form an explicit procedural graph. This is the strongest counterexample to treating
all module structure as locations and scenes.

### Later stress sample: In Liberty's Shadow

Defer the 210-page `CHA3204_-_Rivers_of_London_-_In_Libertys_Shadow.pdf` until the
first three slices stabilize the model. It includes setting material, rules
extensions, factions, locations, two substantial investigations, optional scenes,
case seeds, spells, creatures, pregenerated investigators, and five companion
packs. Its “Story So Far” checkpoints also provide a good future test for minimum
required knowledge versus optional discoveries.

### Ruleset work should remain a neighboring track

`CHA2036_-_Basic_Roleplaying_-_Universal_Game_Engine_-_V1_05.pdf` and
`CHA3200_-_Rivers_of_London_1_4.pdf` are valuable for ruleset extraction and adapter
design, but using either as the first module-import sample would combine two large
unknowns. The module slice should reference existing or minimally hand-authored
mechanical concepts first; systematic BRP rules extraction can then test the seam
without defining the module-content model.
