<!--
SYNC IMPACT REPORT
==================
Version Change: 0.0.0 (Template Draft) -> 1.0.0
Ratification Date: 2026-10-01
Last Amended Date: 2026-10-01

Modified Principles:
- Template placeholders replaced with 10 project-specific core principles:
  - I. Professional CLI UX
  - II. Reliability Over Superficial Visual Changes
  - III. Backward Compatibility
  - IV. Testability & Multi-Layered Testing
  - V. Documentation as Implementation
  - VI. Incremental Delivery & Branch Discipline
  - VII. PR Ownership & Merge Control (Human Authority)
  - VIII. End-to-End Acceptance Gate
  - IX. Scope Discipline & Proportional Refactoring
  - X. Honest & Verifiable Claims

Added Sections:
- Technical & Architectural Constraints
- Development Workflow & PR Verification Protocol
- Governance (Amendment, Versioning, and Compliance Rules)

Removed Sections:
- Generic placeholder sections SECTION_2_NAME, SECTION_3_NAME, and sample comments.

Follow-up TODOs:
- None. All placeholders have been resolved into concrete engineering policies.
-->

# film2media-cli Constitution

## Core Principles

### I. Professional CLI UX
The command-line interface MUST deliver an intentional, consistent, modern, readable, and polished user experience across all interactions.
- Arbitrary colors, inconsistent terminal formatting, erratic spacing, ad-hoc ASCII symbols, jarring prompts, and mismatched terminology are strictly forbidden.
- Interactive workflows MUST provide transparent navigation, unambiguous prompts, informative loading/progress states, graceful cancellation (e.g., clean `Ctrl+C` handling without messy stack traces), retry mechanisms, and actionable error messages.
- Output MUST remain functional and visually coherent across varying terminal geometries (from standard 80x24 terminals to wide monitors) and color capabilities (honoring `NO_COLOR` and non-TTY environments).
- Scriptability and automation MUST be preserved: commands MUST support non-interactive execution via explicit CLI arguments, routing structured data to `stdout` and diagnostic logs or prompts to `stderr`.

### II. Reliability Over Superficial Visual Changes
Functional integrity and stability MUST take precedence over cosmetic aesthetics.
- Visual updates MUST NEVER be used to mask underlying bugs, fragile parsers, or unhandled failure states.
- Every architectural or interface modification MUST preserve or enhance system stability unless an explicit functional deprecation is defined in an approved specification.
- The system MUST deliberately handle external edge cases: network timeouts, HTTP error responses, rate limiting, malformed HTML/JSON structures, missing third-party binaries (e.g., `aria2c`, `ffmpeg`), unavailable media streams, invalid user input, interrupted downloads, and upstream site structure changes. Failures MUST produce clear, actionable diagnostics rather than unhandled exceptions.

### III. Backward Compatibility
Documented commands, flags, arguments, and established user workflows MUST remain stable and supported across versions.
- Breaking changes to CLI options, core execution flows, or configuration files are prohibited unless explicitly justified, planned, and specified in an approved design specification.
- When breaking changes are unavoidable, they MUST be clearly documented in release notes, accompanied by a migration guide, and communicated with deprecation warnings prior to removal.

### IV. Testability & Multi-Layered Testing
All functionality MUST be built for verifiable testability.
- Every new feature, command, or behavioral change MUST include automated automated tests (unit and/or integration) where practical.
- Every user-facing capability MUST provide a repeatable End-to-End (E2E) verification pathway exercising the true user execution path rather than isolated internal functions.
- Bug fixes MUST include automated regression tests that isolate and reproduce the defect prior to confirming the fix.
- Test suites MUST cover primary workflows, including search query parsing, media link extraction, interactive option selection, and download manager dispatch.

### V. Documentation as Implementation
Documentation is an integral, mandatory deliverable of implementation, not an optional follow-up task.
- Any change affecting user-visible behavior, flags, configuration, or workflows MUST update corresponding documentation within the same pull request.
- Bilinguality MUST be maintained: English documentation (`README.md`) and Persian documentation (`README.fa.md`) MUST remain synchronized in content, examples, commands, installation steps, and troubleshooting instructions.
- Installation guides, dependency prerequisites, runtime requirements, configuration specifications, and known constraints MUST remain accurate and up-to-date.

### VI. Incremental Delivery & Branch Discipline
All development MUST proceed through structured, reviewable, and independently verifiable phases.
- Work MUST be partitioned into cohesive, small, and logically independent delivery phases.
- Every phase MUST be developed on its own dedicated feature or fix branch spawned from the default branch.
- Every phase MUST culminate in a single, focused pull request; bundling unrelated refactors, cosmetic tweaks, or orthogonal features into a single branch is prohibited.
- The repository MUST remain in a buildable, testable, and operational state after every merged pull request.

### VII. PR Ownership & Merge Control (Human Authority)
Final repository authority resides exclusively with the human repository owner.
- The human repository owner is the SOLE entity authorized to merge pull requests into default or protected branches.
- Automated agents, bots, or CI processes MUST NEVER merge pull requests or enable automated merge mechanisms.
- Automated agents MUST NEVER push commits directly to protected or default branches (`master`, `main`).
- Automated agents MUST construct comprehensive Pull Request descriptions detailing: implementation overview, automated test coverage, E2E verification proof, documentation modifications, known limitations, and step-by-step manual testing instructions.
- Once a Pull Request is submitted, the agent MUST halt implementation and wait for human review, verification, and explicit merge.

### VIII. End-to-End Acceptance Gate
No feature, refactor, or bug fix is deemed complete solely because automated unit tests pass.
A task or phase reaches completion ONLY when all of the following conditions are met:
1. Automated unit and integration tests pass successfully.
2. An end-to-end verification path has been executed and confirmed.
3. Regression verification has confirmed existing workflows remain unbroken.
4. User documentation (including bilingual parity in `README.md` and `README.fa.md`) has been updated.
5. A clean, focused, reviewable Pull Request has been prepared for human evaluation.

### IX. Scope Discipline & Proportional Refactoring
Implementation efforts MUST maintain strict scope boundaries.
- Developers and agents MUST NOT refactor, restyle, or redesign unrelated modules during feature or bug fix implementation.
- Introduction of external third-party dependencies MUST be strictly minimized and requires compelling technical justification.
- Wholesale rewrites driven merely by aesthetic preferences or stylistic imperfections in existing code are prohibited.
- Refactoring MUST be opportunistic, incremental, and strictly scoped to improving the reliability, maintainability, testability, or UX of the specific component under active development.

### X. Honest & Verifiable Claims
Verification claims MUST reflect verified reality without exaggeration or unverified assumptions.
- An agent or developer MUST NEVER claim a feature or fix works unless it has been explicitly executed and tested.
- Unit test execution MUST NEVER be conflated with or represented as End-to-End verification.
- Output reports MUST explicitly distinguish between automated test suite passes and manual interactive verification.
- When environment limitations (e.g., sandbox restrictions, lack of network access to target media hosts, missing external binaries) prevent complete verification, the limitation and the unverified components MUST be documented transparently.

## Technical & Architectural Constraints

### Platform & Environment Requirements
- The application MUST support standard Python environments (Python 3.8+) across Linux, macOS, and Windows.
- System dependencies (such as external download accelerators like `aria2c` or media tooling like `ffmpeg`) MUST be detected gracefully at runtime, providing clear installation instructions if missing, without terminating ungracefully.

### Architectural Separation
- The application architecture MUST maintain clean boundaries between:
  1. Network & Scraping Layer: HTTP requests, rate limiting, cookie handling, and upstream HTML parsing.
  2. Core Business Logic: Media metadata extraction, quality filtering, link resolution, and state modeling.
  3. CLI Interface Layer: Terminal presentation, prompts, interactive menus, progress indicators, and formatting.
  4. Process & Execution Layer: External process invocation, download job coordination, and subprocess management.

### Error Handling & Process Discipline
- Unhandled Python exceptions MUST NOT leak raw stack traces to standard terminal users during standard operational failures.
- CLI exit codes MUST be meaningful and consistent:
  - `0`: Successful execution.
  - `1`: Operational or runtime error (network failure, missing resource, external error).
  - `2`: Invalid CLI invocation, bad flags, or invalid arguments.
  - `130`: Script terminated via user interruption (`SIGINT` / `Ctrl+C`).

## Development Workflow & PR Verification Protocol

### Spec Kit Lifecycle
All non-trivial enhancements MUST follow the structured Spec Kit development lifecycle:
1. **Specification** (`/speckit-specify`): Define user requirements, acceptance criteria, and edge cases.
2. **Clarification** (`/speckit-clarify`): Resolve ambiguities before planning.
3. **Planning** (`/speckit-plan`): Establish technical architecture, testing strategy, and component design.
4. **Task Breakdown** (`/speckit-tasks`): Generate an ordered, dependency-aware list of executable tasks.
5. **Implementation & Verification** (`/speckit-implement`): Implement incrementally on a feature branch, satisfying all testing and documentation requirements.

### Pull Request Submission Requirements
Every Pull Request created by or with automated assistance MUST contain:
- **Title**: Semantic title reflecting scope (e.g., `feat(cli): add interactive quality selector`).
- **Summary**: Concise explanation of what was changed and why.
- **Verification Proof**:
  - Test commands executed and full test runner output.
  - E2E reproduction steps and observed output.
  - Clarification of what was automated vs. manually verified.
- **Documentation Parity Check**: Verification that both `README.md` and `README.fa.md` have been updated if applicable.
- **Merge Prohibition Notice**: Explicit statement reminding that only the human repository owner may merge the PR.

## Governance

### Authority & Precedence
This Constitution represents the supreme engineering authority for `film2media-cli`. Its principles supersede ad-hoc development habits, personal preferences, and automated agent heuristics. All specifications, architecture plans, implementation tasks, and pull reviews MUST comply with this document.

### Amendment Procedure
Amendments to this Constitution MUST follow a formal process:
1. Proposed changes MUST be submitted via an amendment pull request modifying `.specify/memory/constitution.md`.
2. The pull request MUST document the rationale for the change, its impact on existing workflows, and any required migrations.
3. The amendment takes effect ONLY upon explicit review and merge by the human repository owner.

### Versioning Policy
The Constitution follows Semantic Versioning (`MAJOR.MINOR.PATCH`):
- **MAJOR**: Incompatible changes, deletions, or structural redefinitions of core principles.
- **MINOR**: Addition of new principles, material expansion of governance standards, or structural additions.
- **PATCH**: Non-semantic clarifications, typographical corrections, or wording refinements.

### Compliance Review
All Spec Kit artifacts (specifications, architecture plans, task lists, and pull request reviews) MUST include an explicit compliance check against the 10 Core Principles defined herein. Any deviation MUST be documented, justified, and approved by the human repository owner.

**Version**: 1.0.0 | **Ratified**: 2026-10-01 | **Last Amended**: 2026-10-01
