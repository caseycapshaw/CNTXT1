"""Validate the YAML frontmatter of every Knowledge/Concepts/Initiatives/People/
Skills note against its Pydantic schema. Run via
`uv run python SYSTEM/bin/validate_frontmatter.py`, wired into
SYSTEM/bin/lint.sh.

Files named "* TEMPLATE.md" are skipped -- they carry illustrative, not
schema-valid, values by design. Each Skills/<TYPE>/ folder's own generated
index file ("<TYPE> Index.md" exactly) is also skipped -- it's a pure map
with no frontmatter at all.
"""

import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from SYSTEM.schemas.models import (  # noqa: E402
    AgentFrontmatter, CheckFrontmatter, ConceptFrontmatter, DoFrontmatter,
    FormatFrontmatter, InitiativeFrontmatter, PersonFrontmatter, RuleFrontmatter,
)

TARGETS = [
    ("Knowledge/Agents", AgentFrontmatter),
    ("Knowledge/Concepts", ConceptFrontmatter),
    ("Knowledge/Initiatives", InitiativeFrontmatter),
    ("Knowledge/People", PersonFrontmatter),
    ("Knowledge/Skills/DO", DoFrontmatter),
    ("Knowledge/Skills/CHECK", CheckFrontmatter),
    ("Knowledge/Skills/FORMAT", FormatFrontmatter),
    ("Knowledge/Skills/RULE", RuleFrontmatter),
]


def _skip(path: Path, folder: Path) -> bool:
    if path.name.endswith(" TEMPLATE.md"):
        return True
    # Generated per-TYPE index: "<TYPE> Index.md" exactly (e.g. "DO Index.md").
    if path.name == f"{folder.name} Index.md":
        return True
    # Generated per-directory index (SYSTEM/bin/build_directory_indexes.py) —
    # a pure map with no frontmatter.
    if path.name == "index.md":
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
