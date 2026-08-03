"""Executable checks for the candidate module-content package design.

These tests intentionally exercise planning fixtures rather than production bundle
output. They should remain generic: no helper branches on source keys, room names,
or package-specific IDs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "docs" / "planning" / "module_content_prototype"
SCHEMAS = PROTOTYPE / "schemas"
FIXTURES = PROTOTYPE / "fixtures"
PACKAGE_PATH = FIXTURES / "prototype_module_slice.json"
SCENE_CONTEXT_PATH = FIXTURES / "v2_scene_context.json"
REVIEW_COMPANION_PATH = FIXTURES / "review_companion.json"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(name: str) -> Draft202012Validator:
    schema = _load(SCHEMAS / name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _records(package: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for collection in (
        "publication",
        "blocks",
        "locations",
        "actors",
        "placements",
        "objects",
        "tables",
        "active_features",
        "situations",
        "relationships",
        "adaptation_points",
        "assets",
    ):
        records.extend(package[collection])
    records.extend(package["rules"]["references"])
    records.extend(package["rules"]["supplements"])
    records.extend(package["rules"]["procedures"])
    return records


def _index(package: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {record["id"]: record for record in _records(package)}


def _declared_ids(package: dict[str, Any]) -> set[str]:
    declared = set(_index(package))
    declared.add(package["meta"]["package_id"])
    for situation in package["situations"]:
        for participant in situation["participants"]:
            group_ref = participant.get("group_ref")
            if group_ref:
                declared.add(group_ref)
    return declared


def _internal_refs(package: dict[str, Any]) -> set[str]:
    refs: set[str] = set()

    for node in package["publication"]:
        refs.update(node["children"])
        if node.get("parent_ref"):
            refs.add(node["parent_ref"])

    for location in package["locations"]:
        for field in (
            "content_refs",
            "asset_refs",
            "feature_refs",
            "object_refs",
            "situation_refs",
        ):
            refs.update(location.get(field, []))
        if location.get("parent_ref"):
            refs.add(location["parent_ref"])

    for actor in package["actors"]:
        refs.add(actor["mechanics"]["ref"])

    for placement in package["placements"]:
        refs.update((placement["actor_ref"], placement["location_ref"]))

    for obj in package["objects"]:
        refs.add(obj["location_ref"])
        for field in ("content_refs", "feature_refs", "mechanic_refs"):
            refs.update(obj.get(field, []))
        refs.update(item["rules_ref"] for item in obj.get("contents", []) if item.get("rules_ref"))

    for table in package["tables"]:
        refs.update(outcome["result_ref"] for outcome in table["outcomes"])

    for feature in package["active_features"]:
        refs.update(feature["scope"])
        for field in ("content_refs", "mechanic_refs"):
            refs.update(feature.get(field, []))
        if feature.get("attached_object_ref"):
            refs.add(feature["attached_object_ref"])
        for effect in feature["effects"]:
            refs.add(effect["target_ref"])
            if effect.get("mechanic_ref"):
                refs.add(effect["mechanic_ref"])

    for situation in package["situations"]:
        for field in ("location_ref", "trigger_ref"):
            if situation.get(field):
                refs.add(situation[field])
        refs.update(situation["content_refs"])
        for participant in situation["participants"]:
            refs.update(
                participant[field]
                for field in ("actor_ref", "rules_ref", "group_ref")
                if participant.get(field)
            )
        for response in situation["on_events"]:
            for field in ("if_ref", "mechanic_ref"):
                if response.get(field):
                    refs.add(response[field])
            for effect in response["effects"]:
                refs.add(effect["target_ref"])
                if effect.get("mechanic_ref"):
                    refs.add(effect["mechanic_ref"])

    for relationship in package["relationships"]:
        refs.update((relationship["from_ref"], relationship["to_ref"]))
        refs.update(relationship.get("mechanic_refs", []))

    for point in package["adaptation_points"]:
        refs.update(point["targets"])

    for asset in package["assets"]:
        refs.update(region["location_ref"] for region in asset["regions"])

    return refs


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

    missing = _internal_refs(package) - _declared_ids(package)
    assert missing == set()


def test_scene_context_and_review_refs_resolve() -> None:
    package = _load(PACKAGE_PATH)
    context = _load(SCENE_CONTEXT_PATH)
    companion = _load(REVIEW_COMPANION_PATH)
    declared = _declared_ids(package)

    refs = {
        context["package_ref"],
        context["location"]["ref"],
        *context["location"]["content_refs"],
        context["site_context"]["ref"],
        context["site_context"]["summary_ref"],
        *context["effective_active_features"],
        *context["present_actors"],
        *context["active_situations"],
        *context["immediately_triggerable"],
        *context["objects"],
        *context["dependency_closure"]["locations_summary"],
        *context["dependency_closure"]["actor_groups"],
        *context["dependency_closure"]["rules"],
        *context["dependency_closure"]["tables"],
        *context["dependency_closure"]["mechanics"],
        *(exit_["to"] for exit_ in context["exits"]),
        *(asset["ref"] for asset in context["assets"]),
        *(item["runtime_ref"] for item in companion["items"]),
    }
    assert refs - declared == set()

    regions_by_asset = {
        asset["id"]: {region["id"] for region in asset["regions"]} for asset in package["assets"]
    }
    for selected in context["assets"]:
        assert selected["region_id"] in regions_by_asset[selected["ref"]]


def test_fixture_serialization_is_canonical_and_repeatable() -> None:
    for path in (PACKAGE_PATH, SCENE_CONTEXT_PATH, REVIEW_COMPANION_PATH):
        document = _load(path)
        rendered = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        rebuilt = json.dumps(
            json.loads(rendered), ensure_ascii=False, separators=(",", ":"), sort_keys=True
        )
        assert rebuilt == rendered


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
    assert rules_targets == {"monster:veteran", "monster:commoner"}


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
