"""Validate the YAML frontmatter of every concept / project / area / horizon /
goal / person+org / skill / agent note against its Pydantic schema. Run via
`uv run python SYSTEM/bin/validate_frontmatter.py`, wired into
SYSTEM/bin/lint.sh.

Folder names come from SYSTEM/bin/kb-folders.json (05 concepts/,
03 Projects/ + archive/, 02 Areas/ + Assets/, 01 Horizons/ + Goals/,
04 People/, Skills/<TYPE>/, Agents/ top-level .md only — agent working-data
subfolders are never checked).

Files named "* TEMPLATE.md" are skipped -- they carry illustrative, not
schema-valid, values by design. "<TYPE> Index.md" / "index.md" generated
indexes are also skipped.
"""

import json
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
_FOLDERS = json.loads((Path(__file__).resolve().parent / "kb-folders.json").read_text())
_CONCEPTS = _FOLDERS["concepts"]
_PROJECTS = _FOLDERS["projects"]
_AREAS = _FOLDERS["areas"]
_HORIZONS = _FOLDERS["horizons"]
_HORIZON_GOALS = _FOLDERS["horizon_goals"]
_PEOPLE = _FOLDERS["people"]

from SYSTEM.schemas.models import (  # noqa: E402
    AgentFrontmatter, AreaFrontmatter, CheckFrontmatter, ConceptFrontmatter,
    DoFrontmatter, FormatFrontmatter, GoalFrontmatter, HorizonFrontmatter,
    OrgFrontmatter, PersonFrontmatter, ProjectFrontmatter, RuleFrontmatter,
)

TARGETS = [
    ("Agents", AgentFrontmatter),
    (_CONCEPTS, ConceptFrontmatter),
    (_PROJECTS, ProjectFrontmatter),
    (f"{_PROJECTS}/archive", ProjectFrontmatter),
    (_AREAS, AreaFrontmatter),
    (f"{_AREAS}/Assets", AreaFrontmatter),
    (_HORIZONS, HorizonFrontmatter),
    (_HORIZON_GOALS, "goals-folder"),  # dispatched per-file: index → horizon, else goal
    (_PEOPLE, "people-folder"),  # dispatched per-file: type: org → org, else person
    ("Skills/DO", DoFrontmatter),
    ("Skills/CHECK", CheckFrontmatter),
    ("Skills/FORMAT", FormatFrontmatter),
    ("Skills/RULE", RuleFrontmatter),
]


def _skip(path: Path, folder: Path) -> bool:
    if path.name.endswith(" TEMPLATE.md"):
        return True
    # Generated per-TYPE index: "<TYPE> Index.md" exactly (e.g. "DO Index.md").
    if path.name == f"{folder.name} Index.md":
        return True
    if path.name == "index.md":
        # 01 Horizons/Goals/index.md is the H3 horizon note, not a generated dir index.
        if folder.as_posix().endswith("Horizons/Goals") or folder.name == "Goals":
            return False
        return True
    return False


def _extract_frontmatter(text: str):
    if not text.startswith("---"):
        return None, "no frontmatter block (file must start with ---)"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, "unterminated frontmatter block"
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return None, f"frontmatter is not valid YAML: {e}"
    if not isinstance(data, dict):
        return None, "frontmatter is not a YAML mapping"
    return data, None


def main() -> int:
    errors: list[str] = []
    checked = 0
    for rel, schema in TARGETS:
        folder = REPO_ROOT / rel
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            if _skip(path, folder):
                continue
            checked += 1
            relpath = path.relative_to(REPO_ROOT)
            data, err = _extract_frontmatter(path.read_text(encoding="utf-8"))
            if err:
                errors.append(f"{relpath}: {err}")
                continue
            try:
                if schema == "goals-folder":
                    note_type = data.get("type")
                    if path.name == "index.md" or note_type == "horizon":
                        HorizonFrontmatter.model_validate(data)
                    else:
                        GoalFrontmatter.model_validate(data)
                elif schema == "people-folder":
                    if data.get("type") == "org":
                        OrgFrontmatter.model_validate(data)
                    else:
                        PersonFrontmatter.model_validate(data)
                else:
                    schema.model_validate(data)
            except ValidationError as e:
                for issue in e.errors():
                    loc = ".".join(str(p) for p in issue["loc"]) or "(root)"
                    errors.append(f"{relpath}: {loc}: {issue['msg']}")
    if errors:
        print(f"frontmatter validation: {len(errors)} error(s) in {checked} file(s) checked:")
        for line in errors:
            print(f"  FAIL {line}")
        return 1
    print(f"frontmatter validation: OK ({checked} file(s) checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
