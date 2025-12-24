"""Parse raw spell data into structured format.

Converts raw spell text from PDF extraction into structured spell objects
matching the spell schema (v1.3.0).

This is a STUB implementation - full parsing will be implemented incrementally.
"""

from __future__ import annotations

import re
from typing import Any

from ..postprocess.text import clean_text

# Parsing constants
EXPECTED_SRD_MARKER_PARTS = 2  # Expected parts after splitting on SRD marker


def _segment_paragraphs_from_blocks(description_blocks: list[dict[str, Any]]) -> list[str]:
    """Segment spell description into paragraphs using block structure.

    Uses font metadata and section markers to detect paragraph boundaries.
    Detects breaks at:
    - Section changes (e.g., main → higher_levels)
    - Bold/italic text (often indicates new paragraph/section)

    Args:
        description_blocks: List of text blocks with font metadata

    Returns:
        List of paragraph strings
    """
    if not description_blocks:
        return []

    paragraphs: list[str] = []
    current_paragraph: list[str] = []
    current_section = None

    for block in description_blocks:
        text = clean_text(block.get("text", ""))
        if not text:
            continue

        section = block.get("section")
        is_bold = block.get("is_bold", False)
        is_italic = block.get("is_italic", False)

        # Detect paragraph break conditions
        paragraph_break = False

        # 1. Section change (main → higher_levels)
        if section and section != current_section:
            paragraph_break = True
            current_section = section

        # 2. Bold/Italic headers (like "At Higher Levels." or subsection headers)
        #    But only if we already have content in current paragraph
        if current_paragraph and (is_bold and is_italic):
            paragraph_break = True

        # Start new paragraph if needed
        if paragraph_break and current_paragraph:
            paragraphs.append(" ".join(current_paragraph))
            current_paragraph = []

        current_paragraph.append(text)

    # Don't forget last paragraph
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))

    return paragraphs if paragraphs else []


def _segment_paragraphs(text: str) -> list[str]:
    """Segment spell description into paragraphs.

    Uses double-newline detection (text-based) rather than Y-position gaps
    (which are unreliable in PDFs with negative spacing values).

    Args:
        text: Full spell description text

    Returns:
        List of paragraph strings
    """
    # Split on double newlines or explicit paragraph markers
    # PDF text often has \n\n between paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # Fallback: if no double newlines found (single-paragraph spell),
    # return as single-item list
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []

    return paragraphs


def parse_spell_records(raw_spells: list[dict[str, Any]]) -> list[dict[str, Any]]:  # noqa: C901
    """Parse raw spell data into structured spell records.

    Args:
        raw_spells: List of raw spell dicts from extract_spells

    Returns:
        List of structured spell dicts matching spell.schema.json
    """
    parsed = []

    for raw_spell in raw_spells:
        name = clean_text(raw_spell.get("name", "Unknown Spell"))

        # Reconstruct text from blocks (new format) or fall back to old format
        header_blocks = raw_spell.get("header_blocks", [])
        description_blocks = raw_spell.get("description_blocks", [])

        if header_blocks or description_blocks:
            # New format: reconstruct from blocks
            header_text = " ".join(b["text"] for b in header_blocks)
            description_text = " ".join(b["text"] for b in description_blocks)
        else:
            # Old format fallback (for existing test fixtures)
            header_text = raw_spell.get("header_text", "")
            description_text = raw_spell.get("description_text", "")

        header_text = clean_text(header_text)
        description_text = clean_text(description_text)
        level_and_school = clean_text(raw_spell.get("level_and_school", ""))

        # Fix edge case: multi-page spells where description ended up in header_text
        # Pattern 1: description_text is empty, all text in header_text
        # Pattern 2: description_text only has "At Higher Levels.", main description in header_text
        if "System Reference Document" in header_text:
            # Split at the SRD marker - everything after is the description
            parts = re.split(r"System\s+Reference\s+Document\s+5\.1\s+\d+", header_text, maxsplit=1)
            if len(parts) == EXPECTED_SRD_MARKER_PARTS:
                header_text = parts[0].strip()
                extracted_desc = parts[1].strip()
                # If description_text is empty or just "At Higher Levels.", use extracted
                if not description_text or description_text == "At Higher Levels.":
                    description_text = extracted_desc
                else:
                    # Prepend extracted description to existing text
                    description_text = extracted_desc + " " + description_text

        # Parse level and school (also check for ritual marker)
        level, school = _parse_level_and_school(level_and_school)

        # Check if spell is ritual (appears in level_and_school line)
        ritual = "(ritual)" in level_and_school.lower()

        # Parse header fields (format: "Casting Time: X\nRange: Y\nComponents: Z\nDuration: W")
        casting_time = "1 action"
        range_value: dict[str, Any] = {"type": "self"}
        components_value = {"verbal": False, "somatic": False, "material": False}
        duration_value: dict[str, Any] = {
            "requires_concentration": False,
            "length": "instantaneous",
        }

        # Extract individual header fields
        # Header may be multi-line or single-line with field markers
        # Use regex to extract fields by looking for label patterns
        # Fields end at next label (word followed by colon)

        # Extract Casting Time
        if match := re.search(
            r"Casting Time:\s*(.+?)(?=\s+Range:|\s+Components:|\s+Duration:|$)", header_text
        ):
            casting_time = _parse_casting_time(match.group(1).strip())

        # Extract Range
        if match := re.search(r"Range:\s*(.+?)(?=\s+Components:|\s+Duration:|$)", header_text):
            range_value = _parse_range(match.group(1).strip())

        # Extract Components
        if match := re.search(r"Components:\s*(.+?)(?=\s+Duration:|$)", header_text):
            components_value = _parse_components(match.group(1).strip())

        # Extract Duration
        if match := re.search(r"Duration:\s*(.+?)$", header_text):
            duration_value = _parse_duration(match.group(1).strip())

        # Extract effects and scaling from description
        effects = _extract_effects(description_text)
        scaling = _extract_scaling(description_text, level)

        # Segment description into paragraphs
        # Prefer block-based segmentation if available (new format)
        if description_blocks:
            description_paragraphs = _segment_paragraphs_from_blocks(description_blocks)
        else:
            # Fallback to text-based segmentation (old format)
            description_paragraphs = _segment_paragraphs(description_text)

        # Build spell structure
        spell: dict[str, Any] = {
            "name": name,
            "level": level,
            "school": school,
            "casting": {
                "time": casting_time,
                "range": range_value,
                "ritual": ritual,
            },
            "duration": duration_value,
            "components": components_value,
            "description": description_paragraphs,
            "page": raw_spell.get("pages", [0])[0] if raw_spell.get("pages") else 0,
        }

        # Add optional fields
        if effects:
            spell["effects"] = effects
        if scaling:
            spell["scaling"] = scaling

        # Add classes field (v0.8.0) - requires simple_name to be set first
        # We'll add this after simple_name is added in postprocessing

        parsed.append(spell)

    return parsed


def _parse_level_and_school(level_school_text: str) -> tuple[int, str]:
    """Parse spell level and school from text like '3rd-level evocation'.

    Args:
        level_school_text: Text containing level and school

    Returns:
        Tuple of (level, school)
    """
    import re

    text = level_school_text.lower().strip()

    # Check for cantrip
    if "cantrip" in text:
        # Extract school name (word before "cantrip")
        school = text.split()[0] if text.split() else "evocation"
        return (0, school)

    # Parse leveled spell (e.g., "3rd-level evocation", "2nd- level evocation")
    # Handle optional space after hyphen due to PDF garbling
    match = re.match(r"(\d+)(?:st|nd|rd|th)-?\s*level\s+(\w+)", text)
    if match:
        level = int(match.group(1))
        school = match.group(2)
        return (level, school)

    return (0, "evocation")


def _parse_casting_time(text: str) -> str:
    """Parse casting time from spell header.

    Args:
        text: Casting time text

    Returns:
        Normalized casting time
    """
    return text.strip()


def _parse_range(text: str) -> dict[str, Any]:
    """Parse spell range into structured format.

    Args:
        text: Range text (e.g., "150 feet", "Self (15-foot cone)", "Touch", "Self")

    Returns:
        Structured range object with type, optional distance, and optional area.
        Examples:
            {"type": "ranged", "distance": {"value": 120, "unit": "feet"}}
            {"type": "self", "area": {"shape": "cone", "size": {"value": 15, "unit": "feet"}}}
            {"type": "touch"}
            {"type": "self"}
    """
    import re

    text_clean = text.strip()
    text_lower = text_clean.lower()

    # Pattern: "Self (15-foot cone)" or "Self (10-foot radius)"
    # Handle various dash/hyphen characters (-, ­, ‐, ‑, –, —)
    self_area_match = re.match(
        r"self\s*\((\d+)[\s\-\u00ad\u2010-\u2014]*(?:foot|feet|mile|miles)\s+(radius|sphere|cone|cube|line|cylinder)\)",
        text_lower,
    )
    if self_area_match:
        size_value = int(self_area_match.group(1))
        shape = self_area_match.group(2)
        return {
            "type": "self",
            "area": {"shape": shape, "size": {"value": size_value, "unit": "feet"}},
        }

    # Simple special ranges
    if text_lower == "self":
        return {"type": "self"}
    if text_lower == "touch":
        return {"type": "touch"}
    if text_lower == "sight":
        return {"type": "sight"}
    if text_lower == "unlimited":
        return {"type": "unlimited"}

    # Numeric range (e.g., "150 feet", "1 mile")
    ranged_match = re.match(r"(\d+)\s+(feet|miles|foot|mile)", text_lower)
    if ranged_match:
        value = int(ranged_match.group(1))
        unit_text = ranged_match.group(2)
        # Normalize to plural
        unit = "feet" if unit_text in ("foot", "feet") else "miles"
        return {"type": "ranged", "distance": {"value": value, "unit": unit}}

    # Fallback to self for unparseable ranges
    return {"type": "self"}


def _parse_duration(text: str) -> dict[str, Any]:
    """Parse duration into structured object.

    Args:
        text: Duration text

    Returns:
        Duration object with requires_concentration and length
    """
    text_lower = text.lower().strip()

    # Check for concentration
    requires_concentration = "concentration" in text_lower

    # Remove "concentration, " prefix if present
    length = text_lower
    if requires_concentration:
        length = text_lower.replace("concentration,", "").strip()

    return {"requires_concentration": requires_concentration, "length": length}


def _parse_components(text: str) -> dict[str, Any]:
    """Parse spell components (V/S/M).

    Args:
        text: Components text (e.g., "V, S, M (a tiny ball of bat guano)")

    Returns:
        Components dict with verbal, somatic, material, material_description
    """
    import re

    components: dict[str, Any] = {
        "verbal": "V" in text.upper(),
        "somatic": "S" in text.upper(),
        "material": "M" in text.upper(),
    }

    # Extract material description from parentheses
    match = re.search(r"M\s*\(([^)]+)\)", text, re.IGNORECASE)
    if match:
        components["material_description"] = match.group(1).strip()

    return components


def _extract_damage(description: str) -> dict[str, str] | None:
    """Extract damage dice and type from spell description.

    Args:
        description: Full spell description text

    Returns:
        Damage dict with dice, type, and type_id, or None
    """
    import re

    damage_pattern = r"(\d+d\d+)\s+(acid|bludgeoning|cold|fire|force|lightning|necrotic|piercing|poison|psychic|radiant|slashing|thunder)\s+damage"
    damage_match = re.search(damage_pattern, description, re.IGNORECASE)
    if damage_match:
        damage_type = damage_match.group(2).lower()
        return {
            "dice": damage_match.group(1),
            "type": damage_type,
            "type_id": f"damage:{damage_type}",
        }
    return None


def _extract_save(description: str) -> dict[str, str] | None:
    """Extract saving throw from spell description.

    Args:
        description: Full spell description text

    Returns:
        Save dict with ability and on_success, or None
    """
    import re

    save_pattern = (
        r"(Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma)\s+saving\s+throw"
    )
    save_match = re.search(save_pattern, description, re.IGNORECASE)
    if save_match:
        ability = save_match.group(1).lower()
        ability_id = f"ability:{ability}"
        # Determine success behavior (schema values: 'none', 'half', 'negates', 'other')
        on_success = "half"
        if "half as much damage" in description.lower():
            on_success = "half"
        elif "negates" in description.lower():
            on_success = "negates"

        return {"ability": ability, "ability_id": ability_id, "on_success": on_success}
    return None


def _extract_healing(description: str) -> dict[str, Any] | None:
    """Extract healing from spell description.

    Args:
        description: Full spell description text

    Returns:
        Healing dict with dice/amount/condition, or None
    """
    import re

    # Pattern 1: Dice-based with modifier like "4d8 + 15 hit points" (Regenerate)
    dice_with_modifier_pattern = r"regains?\s+(\d+d\d+\s*[+\-]\s*\d+)\s+hit\s+points"
    dice_mod_match = re.search(dice_with_modifier_pattern, description, re.IGNORECASE)

    # Pattern 2: Dice-based like "regains a number of hit points equal to 1d8"
    dice_healing_pattern = (
        r"regains?\s+(?:a\s+number\s+of\s+)?hit\s+points\s+equal\s+to\s+(\d+d\d+)"
    )
    dice_match = re.search(dice_healing_pattern, description, re.IGNORECASE)

    # Pattern 3: "Regain all hit points" (Wish)
    full_healing_pattern = r"regains?\s+all\s+hit\s+points"
    full_match = re.search(full_healing_pattern, description, re.IGNORECASE)

    # Pattern 4: Conditional healing like "regain hit points equal to half the damage dealt"
    conditional_healing_pattern = r"regains?\s+hit\s+points\s+equal\s+to\s+(.+?)(?:\.|,|\s+Until)"
    conditional_match = re.search(conditional_healing_pattern, description, re.IGNORECASE)

    # Pattern 5: Fixed amount healing like "regain 70 hit points" or "restore up to 700 hit points"
    fixed_healing_pattern = r"(?:regains?|restore(?:s)?(?:\s+up\s+to)?)\s+(\d+)\s+hit\s+points"
    fixed_match = re.search(fixed_healing_pattern, description, re.IGNORECASE)

    if dice_mod_match:
        # Dice with modifier (like Regenerate: 4d8+15)
        return {"dice": dice_mod_match.group(1).replace(" ", "")}
    elif dice_match:
        # Dice-based (like Cure Wounds: 1d8)
        return {"dice": dice_match.group(1)}
    elif full_match:
        # Full healing (like Wish: regain all hit points)
        return {"condition": "all hit points"}
    elif conditional_match and not fixed_match:
        # Conditional healing (like Vampiric Touch: half the necrotic damage dealt)
        condition_text = conditional_match.group(1).strip()
        # Only capture if it's not a simple dice pattern we already caught
        if "d" not in condition_text or "damage" in condition_text.lower():
            return {"condition": condition_text}
    elif fixed_match:
        # Fixed amount (like Heal: 70 HP, Mass Heal: 700 HP)
        return {"amount": int(fixed_match.group(1))}

    return None


def _extract_attack(description: str) -> dict[str, str] | None:
    """Extract spell attack from spell description.

    Args:
        description: Full spell description text

    Returns:
        Attack dict with type, or None
    """
    import re

    attack_pattern = r"(?:make\s+a\s+)?(melee|ranged)\s+spell\s+attack"
    attack_match = re.search(attack_pattern, description, re.IGNORECASE)
    if attack_match:
        return {"type": attack_match.group(1).lower() + "_spell"}
    return None


def _extract_area(description: str) -> dict[str, Any] | None:
    """Extract area of effect from spell description.

    Args:
        description: Full spell description text

    Returns:
        Area dict with shape/size/unit, or None
    """
    import re

    # Pattern 1: Cylinder with dimensions like "10-foot-radius, 40-foot-high cylinder" or "10 feet tall with a 60-foot radius"
    cylinder_pattern1 = r"(\d+)-?\s*foot[-\s]*radius[-\s]*,\s*(\d+)-?\s*foot[-\s]*high\s+cylinder"
    cylinder_pattern2 = (
        r"cylinder\s+that\s+is\s+\d+\s+feet\s+tall\s+with\s+a\s+(\d+)-?\s*foot[-\s]*radius"
    )
    cylinder_match1 = re.search(cylinder_pattern1, description, re.IGNORECASE)
    cylinder_match2 = re.search(cylinder_pattern2, description, re.IGNORECASE)

    if cylinder_match1:
        return {
            "shape": "cylinder",
            "size": int(cylinder_match1.group(1)),
            "unit": "feet",
        }
    elif cylinder_match2:
        return {
            "shape": "cylinder",
            "size": int(cylinder_match2.group(1)),
            "unit": "feet",
        }

    # Pattern 2: Diameter (convert to radius) like "5-foot-diameter sphere"
    diameter_pattern = r"(\d+)-?\s*foot[-\s]*diameter\s+(sphere|cube)"
    diameter_match = re.search(diameter_pattern, description, re.IGNORECASE)
    if diameter_match:
        # Store diameter as-is (schema uses size generically)
        return {
            "shape": diameter_match.group(2).lower(),
            "size": int(diameter_match.group(1)),
            "unit": "feet",
        }

    # Pattern 3: Standard "X-foot radius sphere/cone/cube/cylinder"
    area_pattern = r"(\d+)-?\s*foot[-\s]*(radius[-\s]*)?(sphere|cone|cube|cylinder)"
    area_match = re.search(area_pattern, description, re.IGNORECASE)
    if area_match:
        return {
            "shape": area_match.group(3).lower(),
            "size": int(area_match.group(1)),
            "unit": "feet",
        }

    # Pattern 4: Just radius without shape (default to sphere)
    radius_only_pattern = r"(\d+)-?\s*foot[-\s]*radius(?!\s+(sphere|cone|cube|cylinder))"
    radius_only_match = re.search(radius_only_pattern, description, re.IGNORECASE)
    if radius_only_match:
        return {
            "shape": "sphere",
            "size": int(radius_only_match.group(1)),
            "unit": "feet",
        }

    # Pattern 5: Line spells like "100 feet long and 5 feet wide"
    line_pattern = r"(\d+)\s+feet\s+long(?:\s+and\s+(\d+)\s+feet\s+wide)?"
    line_match = re.search(line_pattern, description, re.IGNORECASE)
    if line_match:
        return {
            "shape": "line",
            "size": int(line_match.group(1)),
            "unit": "feet",
        }

    return None


def _extract_effects(description: str) -> dict[str, Any]:
    """Extract damage, healing, saves, etc. from spell description.

    Args:
        description: Full spell description text

    Returns:
        Effects dict (may be empty if no extractable effects)
    """
    effects: dict[str, Any] = {}

    # Extract each effect type using specialized helpers
    if damage := _extract_damage(description):
        effects["damage"] = damage

    if save := _extract_save(description):
        effects["save"] = save

    if healing := _extract_healing(description):
        effects["healing"] = healing

    if attack := _extract_attack(description):
        effects["attack"] = attack

    if area := _extract_area(description):
        effects["area"] = area

    return effects


def _extract_scaling(description: str, level: int) -> dict[str, Any] | None:
    """Extract scaling information from spell description.

    Args:
        description: Full spell description text
        level: Spell level (0 = cantrip)

    Returns:
        Scaling dict or None if spell doesn't scale
    """
    import re

    # Check for "At Higher Levels" section (slot scaling)
    higher_levels_match = re.search(
        r"At Higher Levels\.\s*(.+?)(?:\.|$)", description, re.IGNORECASE | re.DOTALL
    )
    if higher_levels_match:
        formula_text = higher_levels_match.group(1).strip()
        return {"type": "slot", "base_level": level, "formula": formula_text}

    # Check for character level scaling (cantrips)
    if level == 0:
        char_level_pattern = r"(?:increases|becomes).*?(?:5th|11th|17th).*?level"
        if re.search(char_level_pattern, description, re.IGNORECASE):
            # Extract the scaling formula
            formula_match = re.search(
                r"(\+?\d+d\d+).*?(?:5th|11th|17th)", description, re.IGNORECASE
            )
            if formula_match:
                return {
                    "type": "character_level",
                    "base_level": 1,
                    "formula": formula_match.group(0),
                }

    return None
