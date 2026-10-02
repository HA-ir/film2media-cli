# Phase 3 Quality Checklist: Robust DOM Scraper & Network Reliability

**Purpose**: Validate specification completeness, testability, and governance quality of Phase 3 requirements before implementation
**Created**: 2026-10-02
**Feature**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md) | **Tasks**: [tasks.md](../tasks.md)

**Review Ownership**: Reviewer-owned quality review artifact. Mark an item `[x]` only when the reviewer confirms the requirement-quality criterion is satisfied.

---

## 1. Scope Discipline & Boundary Quality

- [ ] CHK001 Are Phase 3 boundaries strictly limited to DOM scraping (`beautifulsoup4`) and HTTP transport (`f2m.net.client`)? [Clarity, Plan §Phase 3]
- [ ] CHK002 Are non-goals explicitly specified prohibiting UI redesign, new CLI flags (`--json`/`--plain`), and downloader changes (`sudo` removal)? [Completeness, Spec §5, Plan §Technical Context]
- [ ] CHK003 Does the task list prevent drive-by refactorings of unrelated CLI and downloader logic? [Consistency, Constitution Principle IX]

---

## 2. Scraping Resilience & Contract Quality

- [ ] CHK004 Are all 6 core scraping concepts (categories, listing cards, pagination, quick search, movie posts, multi-season series posts) explicitly specified with DOM extraction rules? [Completeness, Spec §FR-001–FR-007]
- [ ] CHK005 Are fallback rules defined for missing optional metadata (IMDb ID, rating, year, trailer) to prevent extraction crashes? [Coverage, Spec §Clarifications]
- [ ] CHK006 Is the behavior for malformed or unparseable HTML explicitly required to raise `F2MParseError` rather than raw Python exceptions (`AttributeError`, `IndexError`)? [Clarity, Spec §FR-008, Tasks §T008]
- [ ] CHK007 Does the scraper consume Phase 2 typed domain entities without defining duplicate models? [Consistency, Spec §1, Data-Model §1]

---

## 3. Network Transport & Mirror Failover

- [ ] CHK008 Are retry limits, retryable HTTP status codes (`429`, `502`, `503`, `504`), and exponential backoff intervals specifically defined? [Clarity, Spec §FR-011, Plan §Research]
- [ ] CHK009 Is ordered mirror failover across `ConfigurationProfile.mirrors` specified with URL path and query preservation? [Completeness, Spec §FR-012, Tasks §T013]
- [ ] CHK010 Is session-transient domain redirect handling specified to prevent silent on-disk configuration mutation (`DEF-005`)? [Safety, Spec §FR-013, Research §3]
- [ ] CHK011 Are low-level transport errors normalized into `F2MNetworkError` with actionable diagnostics? [Clarity, Spec §FR-014, Tasks §T015]

---

## 4. Testability & Offline E2E Coverage

- [ ] CHK012 Are unit tests specified for all DOM scraper components using offline fixtures with reordered attributes and extra whitespace? [Coverage, Tasks §T010]
- [ ] CHK013 Are unit tests specified for `HttpClient` verifying retries, backoff, mirror failover, and proxy routing with mock handlers? [Coverage, Tasks §T016]
- [ ] CHK014 Are E2E scenarios defined executing actual CLI subprocesses for search, post parsing, mirror fallback, and malformed HTML error handling? [Completeness, Tasks §T021–T024]
- [ ] CHK015 Is the preservation of all 28 Phase 1 and Phase 2 regression tests enforced as a mandatory gate? [Regression, Spec §SC-005, Tasks §T028]

---

## 5. Documentation & Reviewability

- [ ] CHK016 Are bilingual documentation updates (`README.md` and `README.fa.md`) required for scraper architecture, network retries, timeouts, and mirror failover? [Parity, Constitution Principle V, Tasks §T025–T026]
- [ ] CHK017 Is human-only merge authority explicitly enforced with agent halting instructions? [Governance, Constitution Principle VII, Tasks §T034]
- [ ] CHK018 Is a mandatory 8-step verification gate defined blocking completion until all tests, static checks, and manual validations pass? [Quality Gate, Tasks §Phase 7]

---

## Notes

- Mark items `[x]` only after reviewer evaluation confirms the requirement-quality criterion is satisfied.
- Leave items unchecked when they still require clarification, correction, or reviewer evaluation.
