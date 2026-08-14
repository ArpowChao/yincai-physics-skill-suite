from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
EXPECTED = {
    "prepare-tts-transcript",
    "zh-tw-proofread",
    "physics-framework-checker",
    "physics-one-page-architect",
    "physics-slide-enhancer",
    "physics-worksheet-generator",
    "physics-literacy-question-creator",
    "physics-visual-style-guide",
    "physics-question-qa-checker",
    "physics-ppt-upgrader",
    "physics-misconception-prompting",
    "physics-unit-package-qc",
}
HEADINGS = {
    "## Inputs",
    "## Workflow",
    "## Output contract",
    "## Stop conditions",
    "## Common mistakes",
}
ABSOLUTE_PATH_RE = re.compile(r"file:///|[A-Za-z]:[\\/]")


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    _, raw, _ = text.split("---", 2)
    result = {}
    for line in raw.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip("\"'")
    return result


def validate() -> list[str]:
    errors = []
    present = {
        path.name
        for path in SKILLS_ROOT.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    }
    if present != EXPECTED:
        errors.append(f"skill set mismatch: expected={sorted(EXPECTED)} present={sorted(present)}")
    for name in sorted(EXPECTED):
        skill_path = SKILLS_ROOT / name / "SKILL.md"
        if not skill_path.exists():
            continue
        text = skill_path.read_text(encoding="utf-8")
        meta = frontmatter(text)
        if set(meta) != {"name", "description"}:
            errors.append(f"{name}: frontmatter must contain only name and description")
        if meta.get("name") != name:
            errors.append(f"{name}: frontmatter name mismatch")
        if not meta.get("description", "").startswith("Use when"):
            errors.append(f"{name}: description must start with 'Use when'")
        if ABSOLUTE_PATH_RE.search(text):
            errors.append(f"{name}: contains an absolute path")
        for heading in HEADINGS:
            if heading not in text:
                errors.append(f"{name}: missing {heading}")
        metadata = SKILLS_ROOT / name / "agents" / "openai.yaml"
        if not metadata.exists():
            errors.append(f"{name}: missing agents/openai.yaml")
        elif f"${name}" not in metadata.read_text(encoding="utf-8"):
            errors.append(f"{name}: default prompt does not mention ${name}")

    data_files = [
        ROOT / "data" / "curriculum" / "stage5-physics.json",
        ROOT / "data" / "curriculum" / "project-node-catalog.json",
        ROOT / "data" / "curriculum" / "project-node-overrides.json",
        ROOT / "data" / "rubrics" / "nine-step.json",
        ROOT / "data" / "rubrics" / "literacy-eight-criteria.json",
        ROOT / "data" / "schemas" / "review-record.schema.json",
        ROOT / "data" / "schemas" / "ppt-review-result.schema.json",
        ROOT / "data" / "terminology" / "physics-terms.json",
        ROOT / "data" / "tts-pronunciation" / "submission.json",
        ROOT / "integrations" / "google-apps-script" / "tts-pronunciation" / "appsscript.json",
    ]
    for path in data_files:
        if not path.exists():
            errors.append(f"missing data file: {path.relative_to(ROOT)}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Validation failed with {len(errors)} error(s).")
        return 1
    print(f"Validation passed: {len(EXPECTED)} skills and shared data are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
