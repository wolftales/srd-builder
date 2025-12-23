# Dependency Update Plan for Vulnerabilities

**Date:** 2025-12-22
**Author:** Gemini-CLI

## 1. Summary

This plan outlines the necessary steps to address identified security vulnerabilities in the project's Python dependencies. A total of 8 vulnerabilities were found across 4 packages: `pypdf`, `pdfminer-six`, `filelock`, and `pip`.

The analysis indicates that all vulnerabilities can be remediated by updating to safe versions without introducing breaking changes that would require code modification within the `srd-builder` project.

## 2. Vulnerable Packages and Safe Versions

The `pip-audit` tool identified the following vulnerabilities:

| Name         | Current Version | Vulnerability IDs                                | Fix Version(s)      |
| :----------- | :-------------- | :----------------------------------------------- | :------------------ |
| `filelock`   | `3.20.0`        | `CVE-2025-68146`                                 | `3.20.1`            |
| `pdfminer-six` | `20250506`      | `CVE-2025-64512`, `GHSA-f83h-ghpp-7wcc`          | `20251107`          |
| `pip`        | `24.0`          | `CVE-2025-8869`                                  | `25.3`              |
| `pypdf`      | `5.9.0`         | `CVE-2025-55197`, `CVE-2025-62707`, `CVE-2025-62708`, `CVE-2025-66019` | `6.0.0`, `6.1.3`, `6.4.0` |

## 3. Breaking Change Analysis and Migration Steps

A thorough review of release notes for the affected packages revealed no breaking changes relevant to `srd-builder` given its current usage and Python version requirements (`>=3.11`).

### `pypdf`

*   **Current Version:** `5.9.0`
*   **Target Safe Version:** `>=6.4.0` (to incorporate all identified fixes).
*   **Breaking Changes Noted:** `pypdf` v6.0.0 dropped support for Python 3.8.
*   **Impact on Project:** None. The `srd-builder` project specifies `requires-python = ">=3.11"`, so it already does not support Python 3.8.
*   **Migration Steps:** No code changes are anticipated. Updating the version constraint in `pyproject.toml` should be sufficient.

### `pdfminer-six`

*   **Current Version:** `20250506`
*   **Target Safe Version:** `>=20251107`.
*   **Breaking Changes Noted:** Recent versions dropped support for Python 3.6 and 3.7.
*   **Impact on Project:** None. The `srd-builder` project specifies `requires-python = ">=3.11"`, so it already does not support these older Python versions. `pdfminer-six` is a transitive dependency of `camelot-py`. Explicitly pinning the version is recommended for clarity and to ensure the correct version is installed.
*   **Migration Steps:** No code changes are anticipated. Adding an explicit version constraint in `pyproject.toml` should be sufficient.

### `filelock`

*   **Current Version:** `3.20.0`
*   **Target Safe Version:** `>=3.20.1`.
*   **Breaking Changes Noted:** No API-level breaking changes. The update is a security patch to address a TOCTOU race condition.
*   **Impact on Project:** None. `filelock` is a transitive dependency, likely for development tools like `pre-commit`. Updating `pre-commit` should resolve this.
*   **Migration Steps:** No code changes are anticipated.

### `pip`

*   **Current Version:** `24.0`
*   **Target Safe Version:** `>=25.3`.
*   **Impact on Project:** `pip` is a system/environment tool, not a project dependency managed directly via `pyproject.toml`.
*   **Migration Steps:** This requires a manual upgrade in the development environment.

## 4. Proposed `pyproject.toml` Updates

To address the vulnerabilities, the following changes are proposed for the `pyproject.toml` file:

```toml
# pyproject.toml
[project]
name = "srd-builder"
version = "0.5.0"
requires-python = ">=3.11" # Already compliant
dependencies = [
  "pymupdf>=1.23.7",
  "pypdf>=6.4.0",              # Updated from >=3.9.0 to >=6.4.0
  "camelot-py[cv]>=0.11.0",    # No change needed here directly, as it pulls pdfminer-six
  "pdfminer-six>=20251107",   # Added explicit dependency to ensure safe version
  "orjson>=3.10.7",
  "python-slugify>=8.0.4",
  "jsonschema>=4.23.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2",
  "pytest-cov>=5.0",
  "ruff>=0.6.9",
  "mypy>=1.13.0",
  "pre-commit>=4.5.1"        # Updated from >=4.0.1 to >=4.5.1 to get updated filelock
]
```

## 5. Recommended Action Plan

1.  **Update `pyproject.toml`**: Apply the proposed changes to `pyproject.toml`.
2.  **Rebuild Environment**: After updating `pyproject.toml`, run `make init` to reinstall dependencies with the new versions. This will update `pypdf`, `pdfminer-six`, `pre-commit` (and thus `filelock`).
3.  **Upgrade `pip`**: Manually upgrade `pip` in the development environment by running:
    ```bash
    python -m pip install --upgrade pip
    ```
4.  **Verify**: Re-run `pip-audit` to confirm that all reported vulnerabilities are resolved.
5.  **Run Tests**: Execute the project's full test suite (`make test-all`) to ensure no unexpected regressions occur due to the dependency updates.
6.  **Run Build and Release Check**: Execute `make bundle` and `make release-check` to confirm build integrity.
