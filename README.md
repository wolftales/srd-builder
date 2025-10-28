# srd-builder

**srd-builder** is a reproducible extraction and normalization pipeline for the *System Reference Document* (SRD) rulesets — starting with **D&D 5.1** and expanding to **5.2.1 (2024)** and beyond.

It builds structured, license-compliant datasets directly from the official PDF releases under *Creative Commons BY 4.0*, producing clean, machine-readable outputs such as:

- `monsters.json`
- `equipment.json`
- `spells.json`
- `rules.json`
- `index.json`

Future outputs may include **YAML**, **SQLite**, or **Parquet** formats.

---

## Quick Start

```bash
# Clone
git clone https://github.com/wolftales/srd-builder.git
cd srd-builder

# Install dependencies
pip install -r requirements.txt

# Build SRD 5.1 (PDF must be placed in rulesets/srd_5_1/raw/)
python scripts/build.py --ruleset srd_5_1 --out rulesets/srd_5_1/data

# Validate and inspect
python scripts/validate.py --ruleset srd_5_1
python scripts/diff_report.py --a srd_5_1 --b srd_5_2_1
````

---

## Repository Structure

```
srd-builder/
├── rulesets/
│   ├── srd_5_1/
│   │   ├── raw/                # PDFs (ignored in git)
│   │   ├── manifest.json
│   │   └── data/
│   └── srd_5_2_1/
│       ├── raw/
│       ├── manifest.json
│       └── data/
├── scripts/                    # Core pipeline
│   ├── build.py
│   ├── pdf_segment.py
│   ├── parse_monsters.py
│   ├── parse_spells.py
│   ├── parse_equipment.py
│   ├── parse_rules.py
│   ├── postprocess.py
│   ├── validate.py
│   └── diff_report.py
├── schemas/                    # JSON Schema definitions
├── tests/                      # Golden fixtures and CI validations
└── .github/workflows/build.yml # CI: validate + package artifacts
```

---

## Project Goals

| Goal                        | Description                                                |
| --------------------------- | ---------------------------------------------------------- |
| **Reproducible Extraction** | Deterministically build SRD datasets from official PDFs    |
| **License Compliance**      | Maintain CC-BY attribution and metadata provenance         |
| **Format Flexibility**      | Output JSON, YAML, SQLite, or Parquet via a unified schema |
| **Edition Awareness**       | Configurable per-edition manifests (5.1, 5.2.1, etc.)      |
| **Transparency**            | Publish build logs, PDF hashes, and diff reports           |
| **Community Friendly**      | Modular, inspectable, and scriptable for other projects    |

---

## Licensing

| Component                 | License   | Notes                                        |
| ------------------------- | --------- | -------------------------------------------- |
| **Code**                  | MIT       | See [LICENSE](LICENSE)                       |
| **Extracted SRD Content** | CC-BY 4.0 | Includes attribution to Wizards of the Coast |
| **Generated Datasets**    | CC-BY 4.0 | Redistributable with attribution             |

---

## Attribution Example

```text
Portions of the materials used are © Wizards of the Coast LLC
and released under the Creative Commons Attribution 4.0 International License.
See https://dnd.wizards.com/resources/systems-reference-document
```

---

## Roadmap

| Milestone  | Description                                | Status        |
| ---------- | ------------------------------------------ | ------------- |
| **v0.1.0** | Base schema + SRD 5.1 parser + JSON output | ✅ In progress |
| **v0.2.0** | SRD 5.2.1 support + diff reporting         | ⏳ Next        |
| **v0.3.0** | SQLite output + schema validation          | ⏳ Planned     |
| **v1.0.0** | Public API + dataset release automation    | 🔮 Future     |

---

## Contributing

Pull requests are welcome!
Please review the [CONTRIBUTING.md](CONTRIBUTING.md) and ensure that:

* You do **not** commit SRD PDFs.
* All code passes `pytest` and `validate.py`.
* JSON outputs remain deterministic across runs.

---

## Inspiration

Born out of the need for *structured, open, and rebuildable SRD data* — powering solo play engines, virtual tabletops, and AI-assisted narrative systems.

---

> “Build once. Verify always. Share freely.”
> — *The srd-builder ethos*

---

## `LICENSE`

[MIT LICENSE](LICENSE.md)

---

## `LICENSE-CC-BY-4.0.txt` (for datasets)

*(Place this alongside generated datasets or releases)*
→ include the plain text of [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode.txt).

---
