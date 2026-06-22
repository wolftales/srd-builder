"""Unit tests for ``scripts/audit_dataset_quality.py``.

The audit script is a dev/CI tool, not a runtime module, so it isn't
importable as ``srd_builder.*``. Tests inject ``scripts/`` onto
``sys.path`` the same way ``test_exemplars_validate.py`` does and then
exercise individual check functions against synthetic, in-memory
distributions — no PDF, no real dist tree.

The ``unknown_word`` check is the focus here because it has external
state (``pyspellchecker`` dictionary, auto-built domain dictionary) and
is the easiest to silently break.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import audit_dataset_quality as audit  # noqa: E402


def test_name_tokens_drops_short_tokens_punctuation_and_digits() -> None:
    assert audit._name_tokens("Bag of Holding") == ["bag", "holding"]
    assert audit._name_tokens("+1 Longsword") == ["longsword"]
    assert audit._name_tokens("Yuan-ti Pureblood") == ["yuan", "pureblood"]
    assert audit._name_tokens("Bigby\u2019s Hand") == ["bigby", "hand"]
    assert audit._name_tokens("Will-o'-Wisp") == ["will", "wisp"]


def test_build_domain_dictionary_unions_all_dataset_name_tokens() -> None:
    distributions = {
        "spell": [{"name": "Fireball"}, {"name": "Magic Missile"}],
        "monster": [{"name": "Aboleth"}, {"name": "Mind Flayer"}],
        "lineage": [{"name": "Tiefling"}],
    }
    tokens = audit._build_domain_dictionary(distributions)
    assert {"fireball", "magic", "missile", "aboleth", "mind", "flayer", "tiefling"} <= tokens


def test_check_unknown_words_flags_typos_only() -> None:
    distributions = {
        "monster": [{"id": "monster:aboleth", "name": "Aboleth"}],
        "spell": [{"id": "spell:fireball", "name": "Fireball"}],
    }
    checker = audit._build_spellchecker(distributions)
    assert checker is not None, "pyspellchecker must be installed for this test"

    items = [
        {"id": "spell:legit", "name": "Magic Missile"},
        {"id": "spell:typo", "name": "Magic Missle"},
        {"id": "monster:typo", "name": "Drangonborn Aboleth"},
    ]
    findings = list(audit.check_unknown_words_in_names("spell", items, checker))

    codes = {f.code for f in findings}
    assert codes == {"unknown_word"}
    details = "\n".join(f.detail for f in findings)
    assert "missle" in details
    assert "drangonborn" in details
    # Real words (and domain words) must not fire.
    assert "magic" not in details
    assert "aboleth" not in details
    assert "missile" not in details


def test_check_unknown_words_is_silent_when_spellchecker_missing() -> None:
    items = [{"id": "spell:typo", "name": "Drangonborn"}]
    findings = list(audit.check_unknown_words_in_names("spell", items, None))
    assert findings == []


def test_check_unknown_words_skips_items_without_string_name() -> None:
    distributions: dict[str, list[dict[str, object]]] = {"spell": []}
    checker = audit._build_spellchecker(distributions)
    items: list[dict[str, object]] = [
        {"id": "spell:nameless"},
        {"id": "spell:none", "name": None},
        {"id": "spell:empty", "name": ""},
    ]
    findings = list(audit.check_unknown_words_in_names("spell", items, checker))
    assert findings == []
