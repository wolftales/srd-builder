#!/usr/bin/env python3
"""Quality analysis report for parsed monster data.

Analyzes potential issues and edge cases in parsed monsters.
"""

import json
from pathlib import Path


def analyze_quality(parsed_path: Path, raw_path: Path) -> None:  # noqa: C901
    """Generate quality analysis report."""
    with open(parsed_path) as f:
        parsed = json.load(f)

    monsters = parsed["items"]
    total = len(monsters)

    print("=" * 80)
    print(f"Quality Analysis Report ({total} monsters)")
    print("=" * 80)
    print()

    # Coverage vs Expected
    expected_srd_count = 319  # Official D&D 5e SRD creature count
    coverage_pct = (total / expected_srd_count) * 100
    missing_count = expected_srd_count - total

    print("EXTRACTION COVERAGE")
    print("-" * 80)
    print(f"Monsters Extracted:  {total}")
    print(f"Expected from SRD:   ~{expected_srd_count} (official D&D 5e SRD count)")
    print(f"Coverage Rate:       {coverage_pct:.1f}%")
    print(f"Missing:             ~{missing_count} creatures")
    print()
    print("Likely reasons for missing monsters:")
    print("  • NPCs with different formatting (Acolyte, Guard, Noble, etc.)")
    print("  • Variant creatures in non-standard format")
    print("  • Cross-references instead of full stat blocks")
    print("  • Different font patterns (non-12pt Bold names)")
    print()
    print("See docs/COVERAGE_ANALYSIS.md for detailed investigation plan")
    print()

    # 1. Core Stats Validation
    print("1. CORE STATS VALIDATION")
    print("-" * 80)
    issues = []
    for m in monsters:
        if m.get("armor_class", 0) <= 0:
            issues.append(f"{m['name']}: AC = {m.get('armor_class')}")
        if m.get("hit_points", 0) <= 0:
            issues.append(f"{m['name']}: HP = {m.get('hit_points')}")
        if not m.get("ability_scores"):
            issues.append(f"{m['name']}: No ability scores")

    if issues:
        print(f"❌ Found {len(issues)} issues:")
        for issue in issues[:10]:
            print(f"   - {issue}")
    else:
        print(f"✅ All {total} monsters have valid AC, HP, and abilities")
    print()

    # 2. Ability Score Distribution
    print("2. ABILITY SCORE DISTRIBUTION")
    print("-" * 80)
    ability_counts: dict[int, int] = {}
    for m in monsters:
        scores = m.get("ability_scores", {})
        count = len(scores)
        ability_counts[count] = ability_counts.get(count, 0) + 1

    for count in sorted(ability_counts.keys()):
        pct = (ability_counts[count] / total) * 100
        status = "✅" if count == 6 else "⚠️"
        print(f"{status} {count} abilities: {ability_counts[count]:3d} monsters ({pct:5.1f}%)")
    print()

    # 3. Trait/Action Parsing Quality
    print("3. TRAIT/ACTION PARSING QUALITY")
    print("-" * 80)

    trait_dist: dict[int, int] = {}
    action_dist: dict[int, int] = {}
    for m in monsters:
        t_count = len(m.get("traits", []))
        a_count = len(m.get("actions", []))
        trait_dist[t_count] = trait_dist.get(t_count, 0) + 1
        action_dist[a_count] = action_dist.get(a_count, 0) + 1

    print("Trait distribution:")
    for count in sorted(trait_dist.keys())[:8]:
        print(f"  {count} traits: {trait_dist[count]:3d} monsters")

    print("\nAction distribution:")
    for count in sorted(action_dist.keys())[:8]:
        print(f"  {count} actions: {action_dist[count]:3d} monsters")

    # Check for suspiciously high counts
    high_trait = [m["name"] for m in monsters if len(m.get("traits", [])) > 5]
    high_action = [m["name"] for m in monsters if len(m.get("actions", [])) > 8]

    if high_trait:
        print(f"\n⚠️  High trait count (>5): {', '.join(high_trait)}")
    if high_action:
        print(f"\n⚠️  High action count (>8): {', '.join(high_action)}")
    print()

    # 4. Defense Fields Coverage
    print("4. DEFENSE FIELDS COVERAGE")
    print("-" * 80)
    resist_count = sum(1 for m in monsters if m.get("damage_resistances"))
    immune_count = sum(1 for m in monsters if m.get("damage_immunities"))
    vuln_count = sum(1 for m in monsters if m.get("damage_vulnerabilities"))
    cond_count = sum(1 for m in monsters if m.get("condition_immunities"))

    print(f"Damage Resistances:       {resist_count:3d} monsters ({resist_count/total*100:5.1f}%)")
    print(f"Damage Immunities:        {immune_count:3d} monsters ({immune_count/total*100:5.1f}%)")
    print(f"Damage Vulnerabilities:   {vuln_count:3d} monsters ({vuln_count/total*100:5.1f}%)")
    print(f"Condition Immunities:     {cond_count:3d} monsters ({cond_count/total*100:5.1f}%)")
    print()

    # 5. Legendary Actions
    print("5. LEGENDARY ACTIONS")
    print("-" * 80)
    legendary_count = sum(1 for m in monsters if m.get("legendary_actions"))
    legendary_monsters = [m["name"] for m in monsters if m.get("legendary_actions")][:10]
    print(
        f"✅ {legendary_count} monsters with legendary actions ({legendary_count/total*100:.1f}%)"
    )
    print(f"Examples: {', '.join(legendary_monsters)}")
    print()

    # 6. Text Content Quality
    print("6. TEXT CONTENT QUALITY")
    print("-" * 80)
    issues = []
    for m in monsters:
        # Check for empty trait/action text
        for trait in m.get("traits", []):
            if not trait.get("text", "").strip():
                issues.append(f"{m['name']}: Empty trait text for '{trait.get('name')}'")
        for action in m.get("actions", []):
            if not action.get("text", "").strip():
                issues.append(f"{m['name']}: Empty action text for '{action.get('name')}'")

        # Check for suspiciously short text
        for trait in m.get("traits", []):
            text = trait.get("text", "")
            if text and len(text) < 10:
                issues.append(f"{m['name']}: Short trait '{trait.get('name')}': {text}")

    if issues:
        print(f"⚠️  Found {len(issues)} text quality issues (showing first 10):")
        for issue in issues[:10]:
            print(f"   - {issue}")
    else:
        print("✅ All traits and actions have valid text content")
    print()

    # 7. Schema Compliance
    print("7. SCHEMA COMPLIANCE")
    print("-" * 80)
    required_fields = ["name", "size", "type", "armor_class", "hit_points", "speed"]
    compliance_issues = []

    for m in monsters:
        for field in required_fields:
            if field not in m or m[field] is None:
                compliance_issues.append(f"{m['name']}: Missing '{field}'")

    if compliance_issues:
        print(f"❌ Schema violations found ({len(compliance_issues)} issues):")
        for issue in compliance_issues[:10]:
            print(f"   - {issue}")
    else:
        print(f"✅ All {total} monsters comply with required schema fields")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_issues = len(issues) + len(compliance_issues)
    if total_issues == 0:
        print("✅ NO CRITICAL ISSUES FOUND")
        print(f"   - All {total} monsters have valid core stats")
        print("   - All text content is present and reasonable")
        print("   - Schema compliance: 100%")
    else:
        print(f"⚠️  FOUND {total_issues} POTENTIAL ISSUES")
        print("   - Review text content quality issues")
        print("   - Verify schema compliance")
    print()


if __name__ == "__main__":
    parsed_path = Path("dist/srd_5_1/data/monsters.json")
    raw_path = Path("rulesets/srd_5_1/raw/monsters_raw.json")

    if not parsed_path.exists():
        print(f"Error: {parsed_path} not found. Run build first.")
        exit(1)

    analyze_quality(parsed_path, raw_path)
