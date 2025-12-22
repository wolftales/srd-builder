"""Tests for prose extraction with boundary detection."""


def test_split_by_known_headers_handles_cross_references():
    """Test that headers with cross-references don't bleed across boundaries.

    Regression test for bug where "incapacitated" in Grappled's text
    was matched when searching for "Incapacitated" header, causing:
    - Grappled section to be cut short
    - Incapacitated section to include Grappled's text
    """
    from srd_builder.extract.extract_prose import split_by_known_headers

    # Simulate the actual PDF text structure with references
    text = """
    Grappled A grappled creature's speed becomes 0, and it can't benefit from
    any bonus to its speed. The condition ends if the grappler is incapacitated
    (see the condition). The condition also ends if an effect removes the
    grappled creature from the reach of the grappler.
    Incapacitated An incapacitated creature can't take actions or reactions.
    """

    headers = ["Grappled", "Incapacitated"]
    sections = split_by_known_headers(text, headers, validate_boundaries=False)

    assert len(sections) == 2, f"Expected 2 sections, got {len(sections)}"

    # Grappled section should contain full text including the reference to "incapacitated"
    grappled = sections[0]
    assert grappled["name"] == "Grappled"
    assert "grappled creature's speed becomes 0" in grappled["raw_text"]
    assert "grappler is incapacitated" in grappled["raw_text"]
    assert "reach of the grappler" in grappled["raw_text"]

    # Incapacitated section should NOT contain Grappled's text
    incapacitated = sections[1]
    assert incapacitated["name"] == "Incapacitated"
    assert "An incapacitated creature can't take actions" in incapacitated["raw_text"]
    assert "grappled creature" not in incapacitated["raw_text"]
    assert "grappler is incapacitated" not in incapacitated["raw_text"]


def test_split_by_known_headers_validates_boundaries():
    """Test that boundary validation catches cross-contamination."""
    from srd_builder.extract.extract_prose import split_by_known_headers

    # Text with deliberate cross-contamination (Blinded section contains Charmed header)
    contaminated_text = """
    Blinded A blinded creature can't see and automatically fails any ability
    check that requires sight. Attack rolls against the creature have advantage.
    Charmed A charmed creature can't attack the charmer.
    """

    headers = ["Blinded", "Charmed"]
    sections = split_by_known_headers(contaminated_text, headers, validate_boundaries=True)

    # Should still extract both sections
    assert len(sections) == 2

    # Blinded section should have NO warnings (doesn't contain other headers)
    blinded = sections[0]
    assert blinded["name"] == "Blinded"
    assert "warnings" not in blinded or len(blinded["warnings"]) == 0

    # Each section should be clean
    assert "Charmed" not in blinded["raw_text"]
    assert "Blinded" not in sections[1]["raw_text"] or sections[1]["raw_text"].startswith("Charmed")


def test_split_by_known_headers_case_sensitive():
    """Test that header matching is case-sensitive to avoid false matches."""
    from srd_builder.extract.extract_prose import split_by_known_headers

    # Test with headers that appear in lowercase as references
    text = """
    Prone A prone creature's only movement option is to crawl. The creature
    is considered prone until it stands up.
    Restrained A restrained creature's speed becomes 0.
    """

    headers = ["Prone", "Restrained"]
    sections = split_by_known_headers(text, headers, validate_boundaries=False)

    assert len(sections) == 2

    # Prone section should include the lowercase "prone" reference
    prone = sections[0]
    assert prone["name"] == "Prone"
    assert "considered prone until" in prone["raw_text"]

    # Restrained section should not contain Prone's text
    restrained = sections[1]
    assert restrained["name"] == "Restrained"
    assert "crawl" not in restrained["raw_text"]
    assert "considered prone" not in restrained["raw_text"]


def test_validate_section_boundaries_ignores_lowercase_references():
    """Test that validation doesn't flag lowercase condition references as contamination."""
    from srd_builder.extract.extract_prose import _validate_section_boundaries

    # Text with lowercase reference to another condition
    text = "Paralyzed A paralyzed creature is incapacitated (see the condition) and can't move."

    # Should not warn about "incapacitated" reference since it's lowercase
    headers = ["Paralyzed", "Incapacitated"]
    warnings = _validate_section_boundaries("Paralyzed", text, headers)

    # Should have no warnings - lowercase "incapacitated" is a valid reference
    assert len(warnings) == 0, f"Unexpected warnings: {warnings}"


def test_validate_section_boundaries_detects_capitalized_contamination():
    """Test that validation catches actual header bleeding (capitalized)."""
    from srd_builder.extract.extract_prose import _validate_section_boundaries

    # Text with actual capitalized header from another condition
    text = "Prone A prone creature's only movement. Restrained A restrained creature's speed is 0."

    headers = ["Prone", "Restrained"]
    warnings = _validate_section_boundaries("Prone", text, headers)

    # Should warn about capitalized "Restrained" header appearing in Prone section
    assert len(warnings) > 0
    assert any("Restrained" in w for w in warnings)
    assert any("cross-contamination" in w for w in warnings)


def test_split_by_known_headers_with_multiple_references():
    """Test handling of multiple condition references in a single section."""
    from srd_builder.extract.extract_prose import split_by_known_headers

    text = """
    Unconscious An unconscious creature is incapacitated (see the condition),
    can't move or speak, and is unaware of its surroundings. The creature drops
    whatever it's holding and falls prone. The creature automatically fails
    Strength and Dexterity saving throws.
    """

    # Even though "incapacitated" and "prone" appear in the text,
    # they're lowercase references and shouldn't interfere
    headers = ["Unconscious"]
    sections = split_by_known_headers(text, headers, validate_boundaries=False)

    assert len(sections) == 1
    unconscious = sections[0]
    assert "is incapacitated" in unconscious["raw_text"]
    assert "falls prone" in unconscious["raw_text"]
    assert "automatically fails" in unconscious["raw_text"]
