"""Executable checks for the candidate module-content package design.

These tests intentionally exercise planning fixtures rather than production bundle
output. They should remain generic: no helper branches on source keys, room names,
or package-specific IDs.

Reference integrity is DERIVED FROM THE SCHEMA, not hand-listed. Any property
referencing the `id` or `idList` definition is treated as an in-package reference
and must resolve; any property referencing `externalRef` resolves against the
installed selected-ruleset bundle instead. Adding a reference-bearing field to the
schema therefore extends the integrity check automatically.

The package schema is split across several files. Definitions are matched by NAME
rather than by JSON pointer, so moving one between files changes nothing here;
definition names are asserted globally unique to keep that safe.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "docs" / "planning" / "module_content_prototype"
SCHEMAS = PROTOTYPE / "schemas"
FIXTURES = PROTOTYPE / "fixtures"
PACKAGE_PATH = FIXTURES / "prototype_module_slice.json"
SCENE_CONTEXT_PATH = FIXTURES / "v2_scene_context.json"
REVIEW_COMPANION_PATH = FIXTURES / "review_companion.json"
BUNDLE_DIR = ROOT / "dist" / "srd_5_1"

ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*:[a-z0-9_:/.-]+$")

# Properties that DECLARE an identity rather than reference one.
DECLARATION_FIELDS = frozenset({"id", "package_id", "context_id"})

# Matched by definition NAME, not by pointer, so a definition moving between
# schema files does not change what the integrity checks cover.
_INTERNAL_ID_DEFS = frozenset({"id", "idList"})
_EXTERNAL_ID_DEFS = frozenset({"externalRef", "externalRefList"})

PACKAGE_SCHEMA = "module-package.schema.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema(name: str) -> dict[str, Any]:
    return _load(SCHEMAS / name)


def _schema_documents() -> dict[str, dict[str, Any]]:
    return {path.name: _load(path) for path in sorted(SCHEMAS.glob("*.json"))}


def _registry() -> Registry:
    """Every schema file, keyed by $id, so cross-file $refs resolve."""
    return Registry().with_resources(
        (document["$id"], Resource.from_contents(document, default_specification=DRAFT202012))
        for document in _schema_documents().values()
        if "$id" in document
    )


def _validator(name: str) -> Draft202012Validator:
    schema = _schema(name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=_registry())


def _ref_targets(node: Any) -> set[tuple[str, str]]:
    """Every ($ref target file, definition name) in a document. '' means same file."""
    found: set[tuple[str, str]] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            ref = value.get("$ref")
            if isinstance(ref, str) and "#/$defs/" in ref:
                file, _, pointer = ref.partition("#/$defs/")
                found.add((file, pointer))
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(node)
    return found


def _package_schema_files() -> list[str]:
    """Schema files reachable from the package envelope, envelope first."""
    documents = _schema_documents()
    reached = [PACKAGE_SCHEMA]
    queue = [PACKAGE_SCHEMA]
    while queue:
        for file, _ in sorted(_ref_targets(documents[queue.pop()])):
            if file and file not in reached:
                reached.append(file)
                queue.append(file)
    return reached


def _package_defs() -> dict[str, dict[str, Any]]:
    """All definitions across the split package schemas, by name.

    Definition names must stay globally unique: the integrity checks match on
    name so that moving a definition between files changes nothing.
    """
    documents = _schema_documents()
    merged: dict[str, dict[str, Any]] = {}
    for file in _package_schema_files():
        for name, definition in documents[file].get("$defs", {}).items():
            assert name not in merged, f"definition {name!r} declared in two schema files"
            merged[name] = definition
    return merged


def _ref_fields(*schemas: dict[str, Any]) -> tuple[frozenset[str], frozenset[str]]:
    """Return (in-package reference fields, cross-bundle reference fields).

    Matches on the referenced definition NAME, so this is unaffected by which
    schema file a definition lives in.
    """
    internal: set[str] = set()
    external: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                for name, subschema in properties.items():
                    ref = subschema.get("$ref") if isinstance(subschema, dict) else None
                    target = ref.rsplit("/", 1)[-1] if isinstance(ref, str) else None
                    if target in _INTERNAL_ID_DEFS and name not in DECLARATION_FIELDS:
                        internal.add(name)
                    elif target in _EXTERNAL_ID_DEFS:
                        external.add(name)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    for schema in schemas:
        visit(schema)
    return frozenset(internal), frozenset(external)


def _package_ref_fields() -> tuple[frozenset[str], frozenset[str]]:
    documents = _schema_documents()
    return _ref_fields(*(documents[file] for file in _package_schema_files()))


def _visit_records(node: Any, on_record: Callable[[dict[str, Any]], None]) -> None:
    """Walk any package-shaped document, yielding every record with a typed ID.

    A module supplement's `data` payload is governed by the selected ruleset lens
    (schemas/monster.schema.json), not by the package schema, so the walk reports
    the ownership envelope but does not descend into the payload.
    """
    if isinstance(node, dict):
        record_id = node.get("id")
        if isinstance(record_id, str) and ID_PATTERN.match(record_id):
            on_record(node)
        skip = {"data"} if node.get("ownership") == "module_supplement" else frozenset()
        for key, value in node.items():
            if key not in skip:
                _visit_records(value, on_record)
    elif isinstance(node, list):
        for item in node:
            _visit_records(item, on_record)


def _records(package: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    _visit_records(package, records.append)
    return records


def _index(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {record["id"]: record for record in _records(package)}


def _declared_ids(package: dict[str, Any]) -> set[str]:
    declared = {record["id"] for record in _records(package)}
    declared.add(package["meta"]["package_id"])
    return declared


def _values_at(document: Any, fields: Iterable[str]) -> set[str]:
    """Collect every string value stored under any of `fields`."""
    wanted = frozenset(fields)
    found: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            skip = {"data"} if node.get("ownership") == "module_supplement" else frozenset()
            for key, value in node.items():
                if key in skip:
                    continue
                if key in wanted:
                    if isinstance(value, str):
                        found.add(value)
                    elif isinstance(value, list):
                        found.update(item for item in value if isinstance(item, str))
                visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(document)
    return found


def _internal_refs(package: dict[str, Any]) -> set[str]:
    internal, _ = _package_ref_fields()
    return _values_at(package, internal)


def _external_refs(package: dict[str, Any]) -> set[str]:
    _, external = _package_ref_fields()
    return _values_at(package, external)


def _placement_for(package: dict[str, Any], occupant_ref: str) -> dict[str, Any] | None:
    """The baseline placement of a named actor or an actor group."""
    for placement in package["placements"]:
        if occupant_ref in (placement.get("actor_ref"), placement.get("group_ref")):
            return placement
    return None


def _ancestor_ids(package: dict[str, Any], location_id: str) -> list[str]:
    index = _index(package)
    ancestors = [location_id]
    current = index[location_id]
    while current.get("parent_ref"):
        parent_id = current["parent_ref"]
        ancestors.append(parent_id)
        current = index[parent_id]
    return ancestors


def _effective_feature_ids(package: dict[str, Any], location_id: str) -> set[str]:
    scope = set(_ancestor_ids(package, location_id))
    return {
        feature["id"]
        for feature in package["active_features"]
        if scope.intersection(feature["scope"])
    }


def _baseline_actor_ids(package: dict[str, Any], location_id: str) -> set[str]:
    return {
        placement["actor_ref"]
        for placement in package["placements"]
        if placement["location_ref"] == location_id
        and placement["presence"] in {"usual", "initial"}
    }


def _resolve_rules(package: dict[str, Any], ref: str) -> dict[str, Any]:
    references = {item["id"]: item for item in package["rules"]["references"]}
    supplements = {item["id"]: item for item in package["rules"]["supplements"]}
    if ref in references:
        return {"mode": "reference", "target": references[ref]["target"]}
    if ref in supplements:
        return {"mode": "supplement", "data": supplements[ref]["data"]}
    raise KeyError(ref)


def _event_effects(
    situation: dict[str, Any], event: str, state: dict[str, str]
) -> list[dict[str, Any]]:
    effects: list[dict[str, Any]] = []
    for response in situation["on_events"]:
        if response["event"] != event:
            continue
        if_ref = response.get("if_ref")
        if if_ref and state.get(if_ref) != response.get("if_state"):
            continue
        effects.extend(response["effects"])
    return effects


def _is_trusted(record: dict[str, Any], field: str) -> bool:
    """A field is trusted only if the source established both record and field."""
    if record.get("stance") != "source_explicit":
        return False
    return field not in record.get("inferred_fields", [])


def _player_safe_content(package: dict[str, Any], refs: Iterable[str]) -> list[str]:
    """Generic audience filter over content blocks — no per-block special cases.

    Fails closed: a block whose `audience` the importer inferred is withheld from
    players regardless of the inferred value. Guessing "player_safe" wrong is how
    GM text reaches the table.
    """
    index = _index(package)
    return [
        ref
        for ref in refs
        if index[ref].get("audience") == "player_safe" and _is_trusted(index[ref], "audience")
    ]


def _assets_for_audience(assets: Iterable[dict[str, Any]], audience: str) -> list[dict[str, Any]]:
    return [asset for asset in assets if asset["audience"] in {audience, "shared"}]


@pytest.fixture(scope="module")
def bundle_ids() -> set[str]:
    """Every entity ID in the built SRD bundle; skips when dist/srd_5_1/ is absent."""
    if not BUNDLE_DIR.exists():
        pytest.skip(f"SRD bundle not built at {BUNDLE_DIR}")
    ids: set[str] = set()
    for path in sorted(BUNDLE_DIR.glob("*.json")):
        document = _load(path)
        for item in document.get("items", []):
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                ids.add(item["id"])
    return ids


def test_candidate_schemas_and_fixtures_validate() -> None:
    package = _load(PACKAGE_PATH)
    context = _load(SCENE_CONTEXT_PATH)
    companion = _load(REVIEW_COMPANION_PATH)

    _validator("module-package.schema.json").validate(package)
    _validator("scene-context.schema.json").validate(context)
    _validator("review-companion.schema.json").validate(companion)

    monster_validator = Draft202012Validator(_load(ROOT / "schemas" / "monster.schema.json"))
    for supplement in package["rules"]["supplements"]:
        if supplement["entity_type"] == "monster":
            monster_validator.validate(supplement["data"])


def test_split_schemas_resolve_and_keep_a_flat_layering() -> None:
    """Every cross-file reference resolves, and no domain file leans on another.

    `common` is a leaf, each domain file depends on `common` alone, and only the
    envelope composes them. That flatness is what makes the lens boundary real:
    adding a second ruleset touches rules.schema.json and nothing beside it.
    """
    documents = _schema_documents()
    files = _package_schema_files()
    assert set(files) == {
        PACKAGE_SCHEMA,
        "common.schema.json",
        "content.schema.json",
        "situations.schema.json",
        "relationships.schema.json",
        "assets.schema.json",
        "rules.schema.json",
    }

    for file in files:
        for target_file, definition in _ref_targets(documents[file]):
            owner = documents[target_file] if target_file else documents[file]
            assert definition in owner.get("$defs", {}), f"{file} -> {target_file}#{definition}"

    def outgoing(file: str) -> set[str]:
        return {target for target, _ in _ref_targets(documents[file]) if target and target != file}

    assert outgoing("common.schema.json") == set(), "common must stay a leaf"
    for file in files:
        if file in {PACKAGE_SCHEMA, "common.schema.json"}:
            continue
        assert outgoing(file) == {"common.schema.json"}, f"{file} reaches past common"
    assert outgoing(PACKAGE_SCHEMA) == set(files) - {PACKAGE_SCHEMA}

    # Definition names stay globally unique, so name-based matching is safe.
    assert len(_package_defs()) == sum(len(documents[f].get("$defs", {})) for f in files)

    # No schema file is orphaned: it is either part of the package or a root.
    assert set(documents) == set(files) | {
        "scene-context.schema.json",
        "review-companion.schema.json",
    }


def test_package_ids_are_unique_and_internal_references_resolve() -> None:
    package = _load(PACKAGE_PATH)
    records = _records(package)
    ids = [record["id"] for record in records]
    assert len(ids) == len(set(ids))

    unresolved = _internal_refs(package) - _declared_ids(package)
    assert unresolved == set(), f"undeclared references: {sorted(unresolved)}"


def test_schema_declares_reference_fields_the_integrity_check_can_find() -> None:
    """Guards the derivation itself: a schema that declared no refs would pass vacuously."""
    internal, external = _package_ref_fields()

    assert {"parent_ref", "actor_ref", "location_ref", "target_ref", "children"} <= internal
    assert {"ability_id", "skill_id", "tool_id", "target"} <= external
    assert not internal & external
    assert not internal & DECLARATION_FIELDS

    package = _load(PACKAGE_PATH)
    assert len(_internal_refs(package)) > 40


def test_actor_groups_are_declared_records_that_own_their_composition() -> None:
    """A group is addressable content, not a shape implied by a participant recipe.

    Groups exist so interchangeable creatures can be tracked without a named actor
    per creature, and so consumer state can say a group moved, fled, or was
    defeated. That needs a declared record, resolvable mechanics, and a baseline
    location to move away from.
    """
    package = _load(PACKAGE_PATH)
    index = _index(package)
    groups = package["actor_groups"]
    assert groups

    for group in groups:
        assert group["id"].startswith("group:")
        assert _resolve_rules(package, group["rules_ref"])["mode"] in {"reference", "supplement"}
        quantity = group["quantity"]
        assert isinstance(quantity, str) or quantity >= 1

        placement = _placement_for(package, group["id"])
        assert placement is not None, f"{group['id']} has no baseline placement"
        assert placement["location_ref"] in index

    # Composition lives in one place: participants reference, they do not declare.
    for situation in package["situations"]:
        for participant in situation["participants"]:
            assert not {"quantity", "rules_ref"} & set(participant)
            occupant = participant.get("group_ref") or participant["actor_ref"]
            assert occupant in index


def test_actor_groups_are_referenced_across_situation_boundaries() -> None:
    """The evidence that ruled out nesting groups inside their owning situation.

    A group declared for one location is targeted by situations at other
    locations - that is the whole reinforcement mechanic. No single situation owns
    it, so it cannot be addressed as a child of one.
    """
    package = _load(PACKAGE_PATH)
    declaring = {
        participant["group_ref"]: situation["id"]
        for situation in package["situations"]
        for participant in situation["participants"]
        if participant.get("group_ref")
    }

    external_uses: dict[str, set[str]] = {}
    for situation in package["situations"]:
        for response in situation["on_events"]:
            referenced = {response.get("if_ref")} | {e["target_ref"] for e in response["effects"]}
            for ref in referenced:
                if isinstance(ref, str) and ref in declaring and declaring[ref] != situation["id"]:
                    external_uses.setdefault(ref, set()).add(situation["id"])

    assert external_uses, "fixture no longer exercises cross-situation group references"
    assert any(len(users) > 1 for users in external_uses.values())


def test_external_refs_resolve_against_the_built_srd_bundle(bundle_ids: set[str]) -> None:
    """Cross-bundle references really do name records in the installed ruleset."""
    package = _load(PACKAGE_PATH)
    external = _external_refs(package)
    assert external

    missing = external - bundle_ids
    assert missing == set(), f"external refs not present in the SRD bundle: {sorted(missing)}"


def test_relationship_views_are_declared_and_vocabulary_is_closed_per_package() -> None:
    """Views are normative; types are vocabulary the package must declare itself.

    An open type vocabulary is what lets a later investigation slice add
    information edges without a schema version bump. Requiring each type to be
    declared in meta.relationship_vocabulary keeps it checkable anyway.
    """
    package = _load(PACKAGE_PATH)
    vocabulary = package["meta"]["relationship_vocabulary"]
    declared_pairs = {(view, type_) for view, types in vocabulary.items() for type_ in types}

    used_pairs = {(rel["view"], rel["type"]) for rel in package["relationships"]}
    assert used_pairs <= declared_pairs, f"undeclared: {sorted(used_pairs - declared_pairs)}"
    assert declared_pairs == used_pairs, "vocabulary declares types the package never uses"

    # A type name must mean one thing: the same type may not span two views.
    views_by_type: dict[str, set[str]] = {}
    for view, type_ in declared_pairs:
        views_by_type.setdefault(type_, set()).add(view)
    assert all(len(views) == 1 for views in views_by_type.values())


def test_stance_vocabulary_is_unified_and_required() -> None:
    """Exactly one stance vocabulary, applied by reference, required everywhere.

    Three divergent vocabularies had drifted into the schema. This guards the
    unification: a new definition cannot quietly introduce a fourth.
    """
    schema = _schema(PACKAGE_SCHEMA)
    defs = _package_defs()

    # No definition may declare its own stance-like enum.
    offenders: list[str] = []

    def visit(node: Any, path: str) -> None:
        if isinstance(node, dict):
            enum = node.get("enum")
            if isinstance(enum, list) and any(
                isinstance(v, str) and v.startswith(("source_", "reviewer_", "compiler_"))
                for v in enum
            ):
                if path != "contentStance":
                    offenders.append(path)
            for key, value in node.items():
                visit(value, key if path == "" else path)
        elif isinstance(node, list):
            for item in node:
                visit(item, path)

    for name, definition in defs.items():
        visit(definition, name)
    assert offenders == [], f"definitions declaring their own stance vocabulary: {offenders}"

    # Every definition that carries stance uses the shared vocabulary and requires it.
    carriers = [name for name, d in defs.items() if "stance" in d.get("properties", {})]
    assert len(carriers) >= 13
    for name in carriers:
        # Asserted by target name, not by pointer: which file owns contentStance
        # is a packaging decision, that every carrier shares it is the contract.
        stance_ref = defs[name]["properties"]["stance"].get("$ref", "")
        assert stance_ref.rsplit("/", 1)[-1] == "contentStance", name
        assert "stance" in defs[name]["required"], f"{name} does not require stance"

    # Every top-level collection holds records that carry warrant.
    for prop, subschema in schema["properties"].items():
        item_ref = subschema.get("items", {}).get("$ref") if "items" in subschema else None
        if item_ref:
            assert item_ref.rsplit("/", 1)[-1] in carriers, f"{prop} records carry no stance"


def _strip_inferred(package: dict[str, Any]) -> dict[str, Any]:
    """Drop every record the source did not establish, plus optional refs to them.

    Optional references to a dropped record are legitimately droppable. A REQUIRED
    reference to one is precisely the failure this is built to surface.
    """
    stripped = json.loads(json.dumps(package))
    removed = {
        record["id"]
        for record in _records(package)
        if record.get("stance") not in (None, "source_explicit")
    }

    internal, _ = _package_ref_fields()
    optional_refs = {
        name
        for definition in _package_defs().values()
        for name in definition.get("properties", {})
        if name in internal and name not in definition.get("required", [])
    }

    def prune(node: Any) -> Any:
        if isinstance(node, dict):
            out = {}
            for key, value in node.items():
                kept = value
                if key in optional_refs:
                    if isinstance(value, str) and value in removed:
                        continue
                    if isinstance(value, list):
                        kept = [item for item in value if item not in removed]
                out[key] = prune(kept)
            return out
        if isinstance(node, list):
            return [prune(item) for item in node if not _is_removed(item, removed)]
        return node

    return prune(stripped)


def _is_removed(item: Any, removed: set[str]) -> bool:
    return isinstance(item, dict) and item.get("id") in removed


def test_inferred_records_are_not_load_bearing() -> None:
    """Strip everything the importer inferred; the package must still validate and run.

    This is the machine substitute for hand review. Module imports are unbounded,
    so nothing merely inferred can be required to run the content — otherwise
    unreviewed inference silently becomes canon.
    """
    package = _load(PACKAGE_PATH)
    stripped = _strip_inferred(package)
    assert len(_records(stripped)) < len(_records(package)), "nothing inferred to strip"

    _validator("module-package.schema.json").validate(stripped)
    assert _internal_refs(stripped) - _declared_ids(stripped) == set()

    # No source prose was lost: only generated material and derived edges go.
    prose_before = {location["id"]: location["content_refs"] for location in package["locations"]}
    prose_after = {location["id"]: location["content_refs"] for location in stripped["locations"]}
    assert prose_before == prose_after

    # R1 still answers, and site-scoped feature composition still resolves —
    # containment survives on location.parent_ref, not on the inferred edges.
    assert _baseline_actor_ids(stripped, "location:wayfarers_rest") == {
        "actor:mara_voss",
        "actor:oren_voss",
        "actor:tess_voss",
    }
    context = _load(SCENE_CONTEXT_PATH)
    assert set(context["effective_active_features"]) == _effective_feature_ids(
        stripped, context["location"]["ref"]
    )


def test_inferred_fields_name_real_present_attributes() -> None:
    """`inferred_fields` must name actual properties of its own record.

    Validated against the schema rather than a hand-list, so it cannot rot: a
    renamed property turns any stale entry into a failure.
    """
    schema = _schema(PACKAGE_SCHEMA)
    defs = _package_defs()
    package = _load(PACKAGE_PATH)

    # Map each top-level collection to the definition governing its records.
    def_for_collection = {
        prop: sub["items"]["$ref"].rsplit("/", 1)[-1]
        for prop, sub in schema["properties"].items()
        if "items" in sub
    }

    seen = 0
    for collection, def_name in def_for_collection.items():
        allowed = set(defs[def_name]["properties"]) - {"id", "type", "stance", "inferred_fields"}
        for record in package[collection]:
            fields = record.get("inferred_fields")
            if fields is None:
                continue
            seen += 1
            assert fields, f"{record['id']}: empty inferred_fields should be omitted"
            unknown = set(fields) - allowed
            assert unknown == set(), f"{record['id']} names non-properties: {sorted(unknown)}"
            absent = [name for name in fields if name not in record]
            assert absent == [], f"{record['id']} marks absent fields: {absent}"
            # Only a source_explicit record has a mix worth describing; if the
            # record itself was inferred, every attribute already is.
            assert record["stance"] == "source_explicit", record["id"]

    assert seen >= 2, "fixture no longer exercises attribute-level warrant"


def test_player_projection_fails_closed_on_inferred_audience() -> None:
    """The payoff: a guessed `audience` is never trusted toward players.

    Record-level warrant cannot express this. The inn read-aloud is source_explicit
    prose whose player-safety was read off typography, so it is withheld, while a
    block whose audience the source did state is served normally.
    """
    package = _load(PACKAGE_PATH)
    index = _index(package)

    inn_refs = index["location:wayfarers_rest"]["content_refs"]
    read_aloud = index["block:inn_read_aloud"]
    assert read_aloud["audience"] == "player_safe"
    assert read_aloud["stance"] == "source_explicit"
    assert "audience" in read_aloud["inferred_fields"]

    # Marked player_safe, but withheld because that value was inferred.
    assert "block:inn_read_aloud" in inn_refs
    assert _player_safe_content(package, inn_refs) == []

    # A block whose audience the source established is unaffected.
    context = _load(SCENE_CONTEXT_PATH)
    assert _player_safe_content(package, context["location"]["content_refs"]) == [
        "block:v2_read_aloud"
    ]


def test_inferred_attributes_survive_the_strip_but_stay_untrusted() -> None:
    """Attribute-level warrant is orthogonal to record-level warrant.

    A record with an inferred attribute is still source-established, so stripping
    inferred RECORDS must keep it — the prose is real. Only the attribute is soft.
    """
    package = _load(PACKAGE_PATH)
    stripped = _strip_inferred(package)
    index = _index(stripped)

    assert "block:inn_read_aloud" in index, "source prose was stripped for a soft attribute"
    assert index["block:inn_read_aloud"]["inferred_fields"] == ["audience"]
    assert not _is_trusted(index["block:inn_read_aloud"], "audience")
    assert _is_trusted(index["block:v2_read_aloud"], "audience")

    # Map regions cannot be recovered from page extraction alone (17.6), so the
    # region-to-location bindings the scene context selects are not trusted.
    asset = index["asset:steamvault_map"]
    assert not _is_trusted(asset, "regions")
    context = _load(SCENE_CONTEXT_PATH)
    assert context["assets"][0]["ref"] == asset["id"]


def test_generated_summaries_are_inferred_and_never_mixed_into_source_prose() -> None:
    """A generated abstract is not one of the publication's own blocks.

    Recorded consequence: the assembled scene context DOES depend on a generated
    site summary, so a consumer refusing inferred content gets no site summary.
    That is a property of the generated view, not of the package.
    """
    package = _load(PACKAGE_PATH)
    index = _index(package)
    summaries = {block["id"] for block in package["blocks"] if block["type"] == "summary"}
    assert summaries

    assert all(index[summary]["stance"] == "source_inferred" for summary in summaries)
    for location in package["locations"]:
        assert not summaries & set(location["content_refs"]), location["id"]
        if "summary_ref" in location:
            assert location["summary_ref"] in summaries

    context = _load(SCENE_CONTEXT_PATH)
    assert context["site_context"]["summary_ref"] in summaries


def test_scene_context_and_review_refs_resolve() -> None:
    package = _load(PACKAGE_PATH)
    context = _load(SCENE_CONTEXT_PATH)
    companion = _load(REVIEW_COMPANION_PATH)
    declared = _declared_ids(package)

    refs = _values_at(context, _ref_fields(_schema("scene-context.schema.json"))[0])
    refs.update(item["runtime_ref"] for item in companion["items"])
    assert refs - declared == set()

    regions_by_asset = {
        asset["id"]: {region["id"] for region in asset["regions"]} for asset in package["assets"]
    }
    for selected in context["assets"]:
        assert selected["region_id"] in regions_by_asset[selected["ref"]]


def test_fixture_files_are_stored_canonically() -> None:
    """The files on disk are byte-identical to a canonical re-render.

    This reads the stored bytes deliberately: an in-memory round-trip would hold
    for any parseable JSON and would prove nothing about the fixture.

    These files are kept ASCII-only on purpose. Two canonical forms exist in this
    repo: the bundle uses ensure_ascii=False (see
    tests/test_bundle_json_format_stability.py) and never meets pre-commit because
    dist/ is gitignored, while pre-commit's pretty-format-json hook escapes
    non-ASCII in every file it does see - including these. While the content stays
    ASCII the two forms are identical bytes and cannot disagree; a single smart
    quote or em dash would put the hook and this test in a rewrite loop.
    """
    for path in sorted(FIXTURES.glob("*.json")) + sorted(SCHEMAS.glob("*.json")):
        stored = path.read_text(encoding="utf-8")
        assert stored.isascii(), f"{path.name} contains non-ASCII; see this test's docstring"
        canonical = json.dumps(json.loads(stored), indent=2, ensure_ascii=False) + "\n"
        assert stored == canonical, f"{path.name} is not canonically serialized"


def test_scenario_run_the_inn() -> None:
    package = _load(PACKAGE_PATH)
    index = _index(package)
    location_id = "location:wayfarers_rest"
    location = index[location_id]

    assert location["names"] == {"simple": "inn", "proper": "Wayfarer's Rest"}
    assert _baseline_actor_ids(package, location_id) == {
        "actor:mara_voss",
        "actor:oren_voss",
        "actor:tess_voss",
    }
    assert {index[ref]["audience"] for ref in location["content_refs"]} == {
        "player_safe",
        "gm_only",
    }
    assert location["object_refs"] == ["object:inn_lockbox"]
    assert location["situation_refs"] == ["situation:inn_service"]

    rules_targets = {
        _resolve_rules(package, index[actor_id]["mechanics"]["ref"])["target"]
        for actor_id in _baseline_actor_ids(package, location_id)
    }
    assert rules_targets == {"npc:veteran", "npc:commoner"}


def test_scenario_audience_filter_withholds_gm_content(bundle_ids: set[str]) -> None:
    """R2/R5: a player-facing projection leaks neither GM prose nor GM maps."""
    package = _load(PACKAGE_PATH)
    context = _load(SCENE_CONTEXT_PATH)
    index = _index(package)

    refs = context["location"]["content_refs"]
    assert {index[ref]["audience"] for ref in refs} == {"player_safe", "gm_only"}
    assert _player_safe_content(package, refs) == ["block:v2_read_aloud"]

    # Every map in this fixture is GM-owned and one carries secrets, so a player
    # audience must come back empty rather than be handed a redacted GM map.
    assert _assets_for_audience(context["assets"], "player") == []
    assert _assets_for_audience(context["assets"], "gm") == context["assets"]
    assert any(index[asset["ref"]]["contains_secrets"] for asset in context["assets"])


def test_scenario_adaptation_point_stays_open_without_breaking_content() -> None:
    """R7: intentional openness is addressable, unbound, and not a missing value."""
    package = _load(PACKAGE_PATH)
    index = _index(package)
    declared = _declared_ids(package)

    points = package["adaptation_points"]
    assert points

    for point in points:
        assert point["state"] == "open"
        assert point["binding"] is None
        assert point["stance"] == "source_explicit"
        assert point["constraints"] and point["suggestions"]
        assert set(point["targets"]) <= declared
        # The target is fully runnable while the adaptation point remains open.
        for target in point["targets"]:
            assert index[target]["names"]["proper"]


def test_scenario_enter_alarm_room_before_alarm() -> None:
    package = _load(PACKAGE_PATH)
    context = _load(SCENE_CONTEXT_PATH)

    assert context["location"]["ref"] == "location:steamvault_v2"
    assert context["present_actors"] == []
    assert set(context["effective_active_features"]) == _effective_feature_ids(
        package, context["location"]["ref"]
    )
    assert context["immediately_triggerable"] == ["situation:v2_alarm_response"]
    assert context["state_inputs"]["active_feature:v2_alarm_coffer"] == "armed"


def test_scenario_trigger_alarm_and_find_immediate_consequences() -> None:
    package = _load(PACKAGE_PATH)
    index = _index(package)
    feature = index["active_feature:v2_alarm_coffer"]

    activated = {
        effect["target_ref"]
        for effect in feature["effects"]
        if effect["operation"] == "activate_situation"
    }
    assert activated == {"situation:v2_alarm_response"}

    response = index[activated.pop()]
    consequences = _event_effects(response, "situation_activated", {})
    assert {(effect["operation"], effect["target_ref"]) for effect in consequences} == {
        ("set_flag", "situation:v3_burrower_nest"),
        ("set_intent", "group:v4_occupants"),
    }

    reached = {
        relationship["to_ref"]
        for relationship in package["relationships"]
        if relationship["type"] == "signal_reaches" and relationship["from_ref"] == feature["id"]
    }
    assert reached == {"location:steamvault_v3", "location:steamvault_v4"}


def test_scenario_lair_reinforcements_respect_current_state() -> None:
    package = _load(PACKAGE_PATH)
    situation = _index(package)["situation:v3_burrower_nest"]

    present = _event_effects(
        situation,
        "combat_begins",
        {"group:v4_occupants": "alive_and_present"},
    )
    absent = _event_effects(
        situation,
        "combat_begins",
        {"group:v4_occupants": "defeated"},
    )

    assert [(effect["operation"], effect["target_ref"]) for effect in present] == [
        ("set_intent", "group:v4_occupants")
    ]
    assert present[0]["mechanic_ref"] == "mechanic:reinforcement_delay"
    assert absent == []


def test_scenario_resolve_package_local_monster_appendix() -> None:
    package = _load(PACKAGE_PATH)
    index = _index(package)
    situation = index["situation:v3_burrower_nest"]

    # Situation -> group -> rules appendix. The participant names an occupant;
    # the group owns what that occupant mechanically is.
    group = index[situation["participants"][0]["group_ref"]]
    assert group["quantity"] == 3
    resolved = _resolve_rules(package, group["rules_ref"])

    assert resolved["mode"] == "supplement"
    assert resolved["data"]["id"] == "monster:ash_burrower"
    assert resolved["data"]["aliases"] == ["cinder mole"]
    assert resolved["data"]["actions"]

    context = _load(SCENE_CONTEXT_PATH)
    table = _index(package)[context["dependency_closure"]["tables"][0]]
    possible_rules = {outcome["result_ref"] for outcome in table["outcomes"]}
    assert possible_rules <= set(context["dependency_closure"]["rules"])
    for ref in possible_rules:
        assert _resolve_rules(package, ref)["mode"] in {"reference", "supplement"}
