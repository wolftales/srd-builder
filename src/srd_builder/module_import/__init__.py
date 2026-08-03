"""Module-content import: publication in, mountable content package out.

This is the producer side of the module-content work described in
`docs/planning/`. It is deliberately separate from the SRD dataset pipeline: the
SRD builder compiles one known ruleset document, while this compiles arbitrary
adventure publications through a per-source profile.

Compiled packages contain publication text and MUST NOT be written into the
repository. Build output belongs under `build/`, which is gitignored.
"""

from __future__ import annotations

from srd_builder.module_import.profile import SourceProfile
from srd_builder.module_import.source import PublicationIdentity, open_source, probe_identity

__all__ = ["PublicationIdentity", "SourceProfile", "open_source", "probe_identity"]
