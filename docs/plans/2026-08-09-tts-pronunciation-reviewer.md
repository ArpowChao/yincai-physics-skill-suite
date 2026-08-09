# TTS Pronunciation Reviewer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a local-first agent workflow that marks confirmed Mandarin pronunciation substitutions and math expressions, lets teachers review suggestions in a browser, and exports a TTS-only transcript without changing the source transcript.

**Architecture:** Keep one deterministic Python core for phrase matching, formula expansion, span-safe replacement, CLI export, and a small local HTTP API. Serve a dependency-free HTML/CSS/JavaScript review surface from the repository. Store shared confirmed rules in versioned JSON while keeping personal overrides in browser storage or ignored local files.

**Tech Stack:** Python 3 standard library, `unittest`, vanilla HTML/CSS/JavaScript, Playwright for browser verification, repository-scoped Codex skill.

### Task 1: Core phrase conversion

**Files:**
- Create: `tests/test_tts_pronunciation.py`
- Create: `scripts/tts_pronunciation.py`
- Create: `data/tts-pronunciation/verified.json`

1. Write failing tests proving longest-phrase matching, source preservation, verified replacement output, and custom override priority.
2. Run `python -m unittest tests.test_tts_pronunciation -v` and confirm the missing module failure.
3. Implement the smallest loader, matcher, change record, and span-safe renderer needed by the tests.
4. Run the focused tests and confirm they pass.

### Task 2: Formula narration and subtitle preservation

**Files:**
- Modify: `tests/test_tts_pronunciation.py`
- Modify: `scripts/tts_pronunciation.py`
- Create: `data/tts-pronunciation/formulas.json`

1. Add failing tests for `x² + y² = z²`, square roots, simple fractions, and preservation of SRT timestamp lines.
2. Run the focused tests and confirm the formula expectations fail.
3. Implement formula-line detection and configurable token expansion without changing timestamps.
4. Run the focused tests and confirm they pass.

### Task 3: Local HTTP API and CLI

**Files:**
- Modify: `tests/test_tts_pronunciation.py`
- Modify: `scripts/tts_pronunciation.py`

1. Add failing tests for JSON analysis responses and file export.
2. Implement `analyze` and `serve` commands using only the standard library.
3. Verify the CLI creates separate `.tts.txt` and `.changes.json` files while leaving the input unchanged.

### Task 4: Teacher review web interface

**Files:**
- Create: `showcase/tts-pronunciation/index.html`
- Create: `showcase/tts-pronunciation/styles.css`
- Create: `showcase/tts-pronunciation/app.js`
- Create: `tests/browser_tts_pronunciation.py`

1. Add a failing Playwright flow for loading the sample, receiving marked suggestions, ignoring a change, adding a personal rule, and downloading/copying the TTS transcript.
2. Build a three-region proofing desk: source transcript, review rail, and generated speech transcript.
3. Support TXT/SRT/VTT import, confirmed-rule auto-application, accept/ignore/edit actions, local personal rules, and export.
4. Run the browser flow and confirm there are no console or page errors.

### Task 5: Repository skill

**Files:**
- Create: `.agents/skills/prepare-tts-transcript/SKILL.md`
- Create: `.agents/skills/prepare-tts-transcript/agents/openai.yaml`

1. Initialize the skill with the system skill creator.
2. Replace placeholders with concise instructions for analyzing files, opening the local reviewer, preserving source text, and exporting results.
3. Validate the skill with `quick_validate.py`.

### Task 6: Documentation, privacy boundaries, and verification

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `.gitignore`
- Modify: `tests/test_repository_layout.py`

1. Add a failing repository test for the new skill, confirmed dictionaries, and local-only override boundary.
2. Document the agent-first usage path and privacy model.
3. Run the full unit suite, repository audit, skill validation, browser flow, and responsive layout audit at 320, 390, 768, 1024, and 1440 pixels.
4. Inspect one narrow and one wide screenshot before reporting completion.
