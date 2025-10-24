---
applyTo: '**'
---
Provide project context and coding guidelines that AI should follow when generating code, answering questions, or reviewing changes.

# Coding and Contribution Guidelines for RA-D-PS Repository

## purpose
onboard coding agents to this repository so they can implement changes quickly without breaking ci or validation. prefer correctness and reproducibility over speed. only search the repo if information below is incomplete or proven wrong.

## repository overview
this repository provides tools to parse, validate, and export radiology annotation data (lidc/idri-style xmls) into analyzable outputs including excel dashboards, sqlite exports, and statistical utilities. it supports psychophysics and radiomics research workflows.
project type: research + data engineering toolkit
languages/runtimes: python 3.12+, shell scripts for setup and ops
tooling: pandas, openpyxl, pytest, black/ruff/mypy, optional tkinter gui for development
size: medium (feature-structured src/, mirrored tests/, docs, examples)

## model selection and switching
1. lightweight / fast models (haiku 4.5, o4-mini, sonnet 3.5, gpt-4.1-mini, gemini flash)
use for syntax fixes, boilerplate or scaffolding, small function completions, adding comments or documentation, repetitive small fixes
goal: maximize responsiveness and reduce latency
2. reasoning / premium models (sonnet 4.5, gpt-5, o3, claude opus, gemini pro)
use for complex debugging and bug tracing, cross-file refactoring, architecture-level design suggestions, algorithm planning and multi-step reasoning, high-thinking tasks
goal: maximize correctness and depth, even if slower
3. visual / multimodal models (gemini flash, opus with vision)
use for analyzing screenshots, diagrams, ui layouts, generating flowcharts or mockups, interpreting structured visual data
goal: handle image+text or design-centric workflows
4. hybrid workflow
start with a fast model (haiku 4.5) for scaffolding and repetitive fixes
switch to a reasoning model (sonnet 4.5) for refinement, optimization, debugging, or high-thinking tasks
switch to a multimodal model for ui/diagram tasks when needed
actively switch between sonnet 4.5 and haiku 4.5: use sonnet 4.5 for complex reasoning, planning, architecture decisions; use haiku 4.5 for repetitive edits, simple fixes, boilerplate generation
reminder: be quota-aware. do not default to the heaviest model unless required. if a fast pass fails to reason coherently, escalate to sonnet 4.5 or higher.

## canonical workflows (build, run, validate)
always do these in order to avoid failures.

⚠️ CRITICAL: REAL TESTS REQUIREMENT ⚠️
BEFORE making ANY code changes, ALWAYS run real tests to validate current state:
  pytest -q                                    # run ALL tests
  python3 tests/test_foundation_validation.py  # schema-agnostic foundation validation

AFTER making code changes, ALWAYS run tests to verify:
  pytest -q tests/<feature>/test_<unit>.py     # specific module tests
  pytest -q                                    # full test suite before committing

NEVER assume code works without running actual tests. Print statements and manual inspection are NOT substitutes for automated tests.

environment and bootstrap
python -m venv .venv
source .venv/bin/activate  # windows: .venv\Scripts\activate
pip install -r requirements.txt
always run pip install -r requirements.txt before building or testing

format, lint, type-check
make fmt
make lint

tests (real, no prints)
pytest -q
pytest -q tests/<feature>/test_<unit>.py
tests must include happy, edge, and failure-path cases. prefer fixtures/fakes over brittle mocks

run
python -m src.cli.parse <path/to/xml_or_dir>
python -m src.gui.app

ci / validation
make ci
prs are rejected if lint/type/test fail. keep changes small and focused

## project layout
/repo-root
  /src
    /parser/      xml parsing and normalization
    /export/      excel and sqlite writers, formatting helpers
    /analysis/    statistical and research utilities
    /gui/         optional tkinter dev ui (excluded from ci)
  /tests          mirrors src; unit and integration
  /configs        .env.example, yaml/json configs
  /scripts        setup_dev.sh, maintenance helpers
  /docs           readme extras, adr, debugging.md, api notes
  /examples       sample xmls and expected outputs for tests
  makefile
  requirements.txt
  readme.md
  contributing.md
  changelog.md
  .editorconfig
  .gitignore

naming conventions: tests in tests/<feature>/test_<unit>.py and tests/integration/test_<flow>.py, scripts named with verbs such as setup_dev.sh, reset_db.sh, gen_outputs.py
configs: pyproject.toml, ruff.toml, mypy.ini control formatting, linting, typing. .env.example lists required env vars. never commit real secrets

## coding, testing, and debug etiquette
write self-explanatory code with clear naming and small, single-purpose functions
avoid clever one-liners that reduce readability
keep pure functions when possible and isolate side effects
validate inputs early, fail fast with meaningful errors, never silently coerce
avoid magic values, use constants or enums, and document assumptions
avoid deep nesting and keep cyclomatic complexity low
prefer composition over inheritance, minimize global state, and use dependency injection
remove dead code, unused imports, and commented-out blocks
always use lowercase comments that explain why
prefer standard library unless a dependency is clearly justified

debugging etiquette: use structured contextual logs without secrets or pii
use proper log levels
reproduce issues with failing tests and add regression tests
reference issues and prs in fixes
remove debug code before commit
use feature flags to isolate risky code
for concurrency, enable race detectors or sanitizers when supported

real test policy: framework is pytest
include positive, negative, edge cases, and at least one failure-path test
prefer fixtures/fakes over brittle mocks
provide a single command: pytest -q
if external services are implied, create stubs or contract tests, never call live apis unless explicitly allowed

## ra-d-ps repo special notes
xml batches vary in element order and optional fields, parser must be order-agnostic and tolerant
radiologist attributes such as confidence, subtlety, obscuration, reason must be exported as column-grouped blocks with spacer columns between radiologists in excel
outputs must preserve raw annotations and derived difficulty metrics
hipaa compliance: use anonymized sop_uids, no patient identifiers in outputs
excel outputs must have alternating row shading, color-coded radiologist groups, dynamic sheet naming with timestamps
sqlite outputs must use normalized schema per feature group and keep forward-compatible migrations
tests must include /examples/xml fixtures and expected outputs
gui in src/gui is for dev convenience only and not required for ci

## search and trust policy
trust this document first. only use grep/find/code search if a step is missing or fails. when adding features:
1. update or add tests first (unit + integration)
2. implement in src/<feature> with minimal public surface
3. run make fmt && make lint && make test
4. update docs/examples if behavior changes
5. open a small pr with verification steps and rollback plan

## quick commands
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make fmt && make lint && pytest -q
make ci
