"""Executable checks for the candidate module-content package design.

These tests intentionally exercise planning fixtures rather than production bundle
output. They should remain generic: no helper branches on source keys, room names,
or package-specific IDs.

Reference integrity is DERIVED FROM THE SCHEMA, not hand-listed. Any property
declared as `#/$defs/id` or `#/$defs/idList` is treated as an in-package reference
and must resolve; any property declared as `#/$defs/externalRef` resolves against
the installed selected-ruleset bundle instead. Adding a reference-bearing field to
the schema therefore extends the integrity check automatically.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

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

_INTERNAL_ID_DEFS = frozenset({"#/$defs/id", "#/$defs/idList"})
_EXTERNAL_ID_DEFS = frozenset({"#/$defs/externalRef", "#/$defs/externalRefList"})

# Anonymous actor groups have no first-class collection yet: `group:*` identity is
# declared implicitly by situation participant recipes. FINDINGS.md lists making
# this explicit as the first schema decision. Until then this is the ONE namespace
# allowed to resolve outside the declared-record set, and the allowance is asserted
# rather than assumed (see test_anonymous_actor_group_contract).
UNDECLARED_NAMESPACE = "group"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema(name: str) -> dict[str, Any]:
    return _load(SCHEMAS / name)


def _validator(name: str) -> Draft202012Validator:
    schema = _schema(name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _ref_fields(schema: dict[str, Any]) -> tuple[frozenset[str], frozenset[str]]:
    """Return (in-package reference fields, cross-bundle reference fields)."""
    internal: set[str] = set()
    external: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            properties = node.get("properties")
            if isinstance(properties, dict):
                for name, subschema in properties.items():
                    ref = subschema.get("$ref") if isinstance(subschema, dict) else None
                    if ref in _INTERNAL_ID_DEFS and name not in DECLARATION_FIELDS:
                        internal.add(name)
                    elif ref in _EXTERNAL_ID_DEFS:
                        external.add(name)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(schema)
    return frozenset(internal), frozenset(external)


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
    internal, _ = _ref_fields(_schema("module-package.schema.json"))
    return _values_at(package, internal)


def _external_refs(package: dict[str, Any]) -> set[str]:
    _, external = _ref_fields(_schema("module-package.schema.json"))
    return _values_at(package, external)


def _declared_group_ids(package: dict[str, Any]) -> set[str]:
    """Group identity as currently declared: situation participant recipes."""
    return {
        participant["group_ref"]
        for situation in package["situations"]
        for participant in situation["participants"]
        if participant.get("group_ref")
    }


def _group_consumers(package: dict[str, Any]) -> set[str]:
    """Every `group:*` reference made from somewhere other than a participant recipe."""
    consumers: set[str] = set()

    def add(value: Any) -> None:
        if isinstance(value, str) and value.startswith(f"{UNDECLARED_NAMESPACE}:"):
            consumers.add(value)

    for feature in package["active_features"]:
        for effect in feature["effects"]:
            add(effect["target_ref"])
    for situation in package["situations"]:
        for response in situation["on_events"]:
            add(response.get("if_ref"))
            for effect in response["effects"]:
                add(effect["target_ref"])
    return consumers


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


def _player_safe_content(package: dict[str, Any], refs: Iterable[str]) -> list[str]:
    """Generic audience filter over content blocks — no per-block special cases."""
    index = _index(package)
    return [ref for ref in refs if index[ref].get("audience") == "player_safe"]


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


def test_package_ids_are_unique_and_internal_references_resolve() -> None:
    package = _load(PACKAGE_PATH)
    records = _records(package)
    ids = [record["id"] for record in records]
    assert len(ids) == len(set(ids))

    unresolved = _internal_refs(package) - _declared_ids(package)
    namespaces = {ref.split(":", 1)[0] for ref in unresolved}
    assert namespaces <= {UNDECLARED_NAMESPACE}, f"undeclared references: {sorted(unresolved)}"


def test_schema_declares_reference_fields_the_integrity_check_can_find() -> None:
    """Guards the derivation itself: a schema that declared no refs would pass vacuously."""
    internal, external = _ref_fields(_schema("module-package.schema.json"))

    assert {"parent_ref", "actor_ref", "location_ref", "target_ref", "children"} <= internal
    assert {"ability_id", "skill_id", "tool_id", "target"} <= external
    assert not internal & external
    assert not internal & DECLARATION_FIELDS

    package = _load(PACKAGE_PATH)
    assert len(_internal_refs(package)) > 40


def test_anonymous_actor_group_contract() -> None:
    """`group:*` identity is implicit today; assert the implicit contract holds.

    Participant recipes are the de facto declaration site. Every group referenced
    from an effect or condition must appear in one. FINDINGS.md tracks replacing
    this with an explicit collection.
    """
    package = _load(PACKAGE_PATH)
    declared = _declared_group_ids(package)
    assert declared

    dangling = _group_consumers(package) - declared
    assert dangling == set(), f"group references with no participant recipe: {sorted(dangling)}"


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


def test_inferred_relationships_are_not_load_bearing() -> None:
    """Strip every relationship the importer inferred; the package must still run.

    This is the machine substitute for hand review. Module imports are unbounded,
    so nothing that was inferred rather than stated can be required to run the
    content — otherwise unreviewed inference silently becomes canon.
    """
    package = _load(PACKAGE_PATH)
    explicit = [rel for rel in package["relationships"] if rel["stance"] == "source_explicit"]
    assert len(explicit) < len(package["relationships"]), "fixture has no inferred edges to strip"

    stripped = {**package, "relationships": explicit}
    _validator("module-package.schema.json").validate(stripped)
    assert (
        _internal_refs(stripped) - _declared_ids(stripped) - _declared_group_ids(stripped) == set()
    )

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


def test_scene_context_and_review_refs_resolve() -> None:
    package = _load(PACKAGE_PATH)
    context = _load(SCENE_CONTEXT_PATH)
    companion = _load(REVIEW_COMPANION_PATH)
    declared = _declared_ids(package) | _declared_group_ids(package)

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
    """
    for path in sorted(FIXTURES.glob("*.json")) + sorted(SCHEMAS.glob("*.json")):
        stored = path.read_text(encoding="utf-8")
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
    situation = _index(package)["situation:v3_burrower_nest"]
    rules_ref = situation["participants"][0]["rules_ref"]
    resolved = _resolve_rules(package, rules_ref)

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
