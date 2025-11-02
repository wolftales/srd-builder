"""Test version consistency across the codebase.

Ensures __version__ in __init__.py is the single source of truth and that
version references in code/data files are consistent.

Note: srd-builder uses two version numbers (package version and schema version).
See docs/ARCHITECTURE.md#version-management for details.
"""

import json
import re
from pathlib import Path

import pytest

from srd_builder import __version__


def test_version_format():
    """Version should follow semantic versioning format."""
    assert re.match(
        r"^\d+\.\d+\.\d+$", __version__
    ), f"Version '{__version__}' doesn't match semantic versioning (X.Y.Z)"


def test_build_module_uses_version_constant():
    """build.py should import and use __version__, not hardcode it."""
    build_path = Path("src/srd_builder/build.py")
    content = build_path.read_text(encoding="utf-8")

    # Should import __version__
    assert "from . import __version__" in content, "build.py must import __version__ from package"

    # Should not hardcode version strings like "0.5.1"
    # Allow version in URLs or comments, but not in code
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        # Skip comments and URLs
        if line.strip().startswith("#") or "github.com" in line:
            continue
        # Check for hardcoded version patterns (not in f-strings with __version__)
        if re.search(r'["\']0\.\d+\.\d+["\']', line) and "__version__" not in line:
            pytest.fail(f"build.py:{i} appears to hardcode a version: {line.strip()}")


def test_normalized_fixture_version_matches():
    """Normalized fixture should match current __version__."""
    fixture_path = Path("tests/fixtures/srd_5_1/normalized/monsters.json")
    if not fixture_path.exists():
        pytest.skip("Normalized fixture not found")

    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    expected_generated_by = f"srd-builder v{__version__}"

    assert "_meta" in data, "Fixture missing _meta section"
    assert "generated_by" in data["_meta"], "Fixture _meta missing generated_by"

    actual = data["_meta"]["generated_by"]
    assert actual == expected_generated_by, (
        f"Fixture has outdated version. Expected '{expected_generated_by}', "
        f"got '{actual}'. Run: python -c \"from pathlib import Path; "
        f"import json; from srd_builder import __version__; "
        f"from srd_builder.parse_monsters import parse_monster_records; "
        f"from srd_builder.postprocess import clean_monster_record; "
        f"raw = json.loads(Path('tests/fixtures/srd_5_1/raw/monsters.json').read_text()); "
        f"parsed = parse_monster_records(raw); "
        f"processed = [clean_monster_record(m) for m in parsed]; "
        f"doc = {{'_meta': {{'ruleset': 'srd_5_1', 'schema_version': '1.2.0', "
        f"'source': 'SRD_CC_v5.1', 'build_report': '../build_report.json', "
        f"'generated_by': f'srd-builder v{{__version__}}'}}, 'items': processed}}; "
        f"Path('tests/fixtures/srd_5_1/normalized/monsters.json').write_text("
        f"json.dumps(doc, indent=2, ensure_ascii=False) + '\\n')\""
    )


def test_template_files_have_version_note():
    """Template files should note that version is a placeholder."""
    template_dir = Path("docs/templates")
    if not template_dir.exists():
        return

    for template_path in template_dir.glob("TEMPLATE_*.json"):
        content = template_path.read_text(encoding="utf-8")
        data = json.loads(content)

        if "_meta" in data and "generated_by" in data["_meta"]:
            generated_by = data["_meta"]["generated_by"]
            # Templates can have any version, but let's check they're marked as templates
            assert (
                "srd-builder" in generated_by
            ), f"{template_path.name} should reference srd-builder in generated_by"


def test_golden_test_uses_version_constant():
    """Golden test should import and use __version__, not hardcode it."""
    test_path = Path("tests/test_golden_monsters.py")
    content = test_path.read_text(encoding="utf-8")

    # Should import __version__
    assert (
        "from srd_builder import __version__" in content
    ), "test_golden_monsters.py must import __version__"

    # Should use it in _meta function
    assert (
        'f"srd-builder v{__version__}"' in content
    ), "test_golden_monsters.py should use __version__ in generated_by"

    # Should not hardcode version strings
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("#"):
            continue
        # Check for hardcoded version patterns (not in f-strings with __version__)
        if re.search(r'["\']srd-builder v0\.\d+\.\d+["\']', line):
            pytest.fail(
                f"test_golden_monsters.py:{i} appears to hardcode a version: {line.strip()}"
            )


def test_version_not_hardcoded_in_source():
    """Source code should not hardcode package version strings.

    Note: This allows extractor_version, schema_version, etc. which track
    format versions independent of package version.
    """
    src_dir = Path("src/srd_builder")

    for py_file in src_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            # __init__.py is allowed to define __version__
            continue

        content = py_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Skip comments, URLs, and lines that use __version__
            if line.strip().startswith("#") or "github.com" in line or "__version__" in line:
                continue

            # Skip legitimate format versions (extractor_version, schema_version)
            if "extractor_version" in line or "schema_version" in line:
                continue

            # Check for hardcoded package version patterns like "srd-builder v0.5.1"
            if re.search(r'["\']srd-builder v0\.\d+\.\d+["\']', line):
                pytest.fail(
                    f"{py_file.name}:{i} hardcodes package version (should use __version__): {line.strip()}"
                )


def test_changelog_or_docs_mention_current_version():
    """Current version should be mentioned in release docs."""
    # Check ROADMAP.md for current version
    roadmap = Path("docs/ROADMAP.md")
    if roadmap.exists():
        content = roadmap.read_text(encoding="utf-8")
        version_mentioned = (
            f"v{__version__}" in content
            or f"**v{__version__}**" in content
            or __version__ in content
        )
        assert version_mentioned, f"ROADMAP.md should mention current version {__version__}"


def test_readme_mentions_current_version():
    """README should mention current version in roadmap."""
    readme = Path("README.md")
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        # Should mention version somewhere (roadmap, changelog, etc.)
        assert (
            f"v{__version__}" in content or __version__ in content
        ), f"README.md should mention current version {__version__}"
