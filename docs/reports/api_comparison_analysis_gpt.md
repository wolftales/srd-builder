## What those APIs provide that SRD-Builder does not (SRD-focused)

### dnd5eapi.co (D&D 5e API)

* **A public, read-only REST API** with predictable resource URLs (collections + `/.../{index}` items). ([dnd5e.magical20.com][1])
* **Consistent cross-linking by URL** inside payloads (e.g., a spell references damage type via a nested object with a `url`). ([dnd5e.magical20.com][1])
* **“Discovery first” list endpoints**: list calls return lightweight objects (index/name/url), then clients fetch details per resource. ([5e-bits.github.io][2])
* **Published API documentation + OpenAPI spec** (their repo explicitly says docs are generated from a bundled OpenAPI spec). ([GitHub][3])

### 5e-bits (D&D 5e SRD API: REST + GraphQL)

* Everything above **plus GraphQL**, which solves “N requests for N monsters” and lets clients ask for *exactly* the fields they need. ([5e-bits.github.io][2])
* **Explicit API versioning by SRD year** (`/api/2014`, next planned `/api/2024`). ([GitHub][3])
* **Resource discovery helpers** (endpoints that list resources for an endpoint, plus filtering notes). ([5e-bits.github.io][4])

### Open5e

* **Much broader than SRD** unless you filter: SRD + other OGL sources, and it exposes the source via `document__slug` / `document__title`. ([api.open5e.com][5])
* **First-class filtering / pagination / ordering** in list endpoints (DRF style: `count/next/previous/results`). ([api.open5e.com][5])
* **Browsable API + built-in schema/docs endpoints** (swagger-ui / redoc). ([api.open5e.com][6])
* Note: Open5e’s “general search endpoint” documented as `/search/?text=...` currently returned a 404 in my test, so you can’t rely on it without verifying their current path/version.

## What you’ve done that’s good (SRD-Builder strengths)

From your repo’s stated goals/output:

* **You own the extraction pipeline**: PDF → normalized JSON + SQLite + markdown/text output, which is the hard/valuable part. ([GitHub][7])
* **Multiple artifacts for different consumers** (JSON + SQLite + markdown) instead of only “API-shaped” data. ([GitHub][7])
* **You’re positioned for determinism and reproducibility** (a builder that can re-run when SRD/inputs change) rather than a one-off dataset dump. ([GitHub][7])

## Organization/modeling differences you’re likely missing (vs the API-first projects)

### 1) Canonical resource identity + linking

API-first datasets are designed around:

* stable `index`/`slug`
* a canonical `url`
* references expressed as `{ index, name, url }` objects

That pattern makes it easy to:

* cache
* de-duplicate
* “hydrate” details lazily
* generate client SDKs

**SRD-Builder can keep your richer normalized schema**, but you’ll want a *thin “API projection” layer* that adds canonical IDs and cross-links.

### 2) Versioning as a contract

5e-bits treats “SRD year” as part of the URL contract. ([GitHub][3])
You already produce “dist” outputs; you’re one step away from **publishing versioned datasets** (and later versioned endpoints) as a stable contract.

### 3) Search, filtering, pagination

Open5e’s list endpoints are designed for real app consumption: `count/next/previous/results` plus server-side filters. ([api.open5e.com][5])
SRD-Builder today looks “builder-first,” not “query-first.”

## Presentation: how the API output differs (and what to copy)

### dnd5eapi / 5e-bits REST

* **List endpoints are lightweight** (index/name/url). ([5e-bits.github.io][2])
* **Detail endpoints are heavy** (full object).
* Payloads include **URL references** to related resources. ([dnd5e.magical20.com][1])

### Open5e REST

* **List endpoints can be heavy** (their default list includes many fields). ([api.open5e.com][5])
* Strong **source attribution inside each record** via `document__*`. ([api.open5e.com][5])
* Clear **pagination contract** (`count/next/previous/results`). ([api.open5e.com][5])

## What’s missing (practical gaps SRD-Builder should plan for)

If your goal includes being a backend for apps/tools (not just a dataset builder):

1. **A stable public “resource model”**

* `id` / `slug` / `index`
* canonical `url`
* “reference object” pattern for relationships

2. **An API projection**

* Even if your internal schema stays normalized, expose an API-friendly shape:

  * list shape (small)
  * detail shape (full)
  * consistent field naming and enums

3. **OpenAPI spec (minimum)**

* If you ever publish endpoints, an OpenAPI spec unlocks docs/SDKs/tests (exactly what 5e-bits does). ([GitHub][3])

4. **Filtering/pagination contract**

* Pick one pattern and standardize it:

  * `limit/offset` or `page/page_size`
  * `count + next` style (Open5e) ([api.open5e.com][5])
  * basic filters for SRD use-cases (CR, level, school, class, type)

5. **Source/licensing metadata per record**

* Open5e is very explicit about which document a record came from. ([open5e.com][8])
  Even if you’re SRD-only, recording provenance helps later (SRD 5.1 vs future, errata, etc.).

## What to prioritize (a realistic roadmap)

If I were sequencing this for SRD-Builder:

1. **Define “Public Resource Contract v1” (data-only)**

* For each major entity (monsters, spells, items, conditions, classes, races):

  * `index`, `name`, `url`, `source` (SRD version), and relationship references as `{index,name,url}`

2. **Generate “API projection JSON” alongside your current outputs**

* `dist/api/v1/{resource}.json` (full)
* `dist/api/v1/{resource}_index.json` (lightweight list)

3. **Add a tiny read-only service (optional, but high leverage)**

* FastAPI or similar:

  * `/v1/{resource}` list (filters + pagination)
  * `/v1/{resource}/{index}` detail
* Ship OpenAPI from day 1.

4. **Then decide: GraphQL or not**

* If you expect UIs to frequently “ask for just 3 fields,” GraphQL becomes worth it (this is exactly 5e-bits’ rationale). ([5e-bits.github.io][2])
  Otherwise, stick to REST + sparse field selection (`?fields=...`) as a simpler middle ground.

If you want, I’ll turn this into a concrete SRD-Builder design doc outline (files + schemas + endpoint list) aligned to how you already structure `dist/` outputs.

[1]: https://dnd5e.magical20.com/ "D&D 5th Edition API"
[2]: https://5e-bits.github.io/docs/tutorials/beginner/graphql "GraphQL Fundamentals | D&D 5e SRD API"
[3]: https://github.com/5e-bits/5e-srd-api "GitHub - 5e-bits/5e-srd-api: REST API to access D&D 5th Edition SRD database"
[4]: https://5e-bits.github.io/docs/api/get-list-of-all-available-resources-for-an-endpoint?utm_source=chatgpt.com "Get list of all available resources for an endpoint. | D&D 5e ..."
[5]: https://api.open5e.com/monsters/?cr=3 "Monster List – Django REST framework"
[6]: https://api.open5e.com/ "Open5E Api – Django REST framework"
[7]: https://github.com/wolftales/srd-builder "GitHub - wolftales/srd-builder"
[8]: https://open5e.com/api-docs "Api Docs - Open5e"
