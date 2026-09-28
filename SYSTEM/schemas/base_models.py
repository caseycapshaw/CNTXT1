"""Canonical, shared frontmatter schemas — one class per note type.

Meant to be pulled into any downstream repo unmodified. Instance-local
customization (subclassing, extra classes like AgentFrontmatter) lives in
SYSTEM/schemas/models.py, not here.
"""

from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class AuthorshipMixin(BaseModel):
    """Optional authorship/write-permission keys, valid on any note type.

    `author_type` is a WRITE-PERMISSION SWITCH, not credit (adopted 2026-08-20
    from the metarelating pattern): `human` -> body is read-only to machines
    (propose changes, never edit in place); `script` -> producer-owned (fix
    the generator and re-run, never hand-edit); `assistant` -> machine-editable
    per normal rules. Absence means normal editability — it is not a gap.
    """

    author: Optional[str] = None
    author_type: Optional[Literal["human", "assistant", "script"]] = None


def _validate_iso_date(value: object) -> str:
    # Unquoted YAML dates (e.g. `updated: 2026-07-09`) parse to native `date`
    # objects, not strings — normalize those to ISO text rather than forcing
    # every note to switch to quoted date strings.
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            date.fromisoformat(value)
        except ValueError as e:
            raise ValueError(f"must be an ISO date (YYYY-MM-DD), got {value!r}") from e
        return value
    raise ValueError(f"must be an ISO date (YYYY-MM-DD) or date, got {value!r}")


def _require_wikilinks(v: object, field: str) -> object:
    """serves:/horizon:/owner-style up-link values are wikilinks, or a list of them."""
    if v is None:
        return v
    items = v if isinstance(v, list) else [v]
    for item in items:
        if not (isinstance(item, str) and item.startswith("[[") and item.endswith("]]")):
            raise ValueError(f'{field}: entries must be wikilinks ("[[slug]]")')
    return v


class SkillMetaMixin(BaseModel):
    """Optional skill bookkeeping. `version` (a QUOTED string) is the contract
    version — bumped on every ADOPTED line in SYSTEM/skill-impact.md;
    `updated` is the last-rewrite ISO date."""

    version: Optional[str] = None
    updated: Optional[str] = None

    @field_validator("updated", mode="before")
    @classmethod
    def _check_skill_updated(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        return _validate_iso_date(v)


class DoFrontmatter(SkillMetaMixin, AuthorshipMixin):
    """Frontmatter schema for Skills/DO/*.md — agent-executable runbooks
    that perform a recurring task and produce an outcome."""

    type: Literal["do"] = "do"
    domain: str
    trigger: str
    frequency: str
    tools: list[str] | str = Field(default_factory=list)
    owner: Optional[str] = None
    model: str = "claude-sonnet-5"
    status: Literal["active", "draft", "superseded"] = "active"
    tags: list[str] = Field(default_factory=lambda: ["do"])
    aliases: list[str] = Field(default_factory=list)
    summary: str


class CheckFrontmatter(SkillMetaMixin, AuthorshipMixin):
    """Frontmatter schema for Skills/CHECK/*.md — agent-executable
    runbooks that verify or audit something and produce a verdict."""

    type: Literal["check"] = "check"
    domain: str
    trigger: str
    frequency: str
    tools: list[str] | str = Field(default_factory=list)
    owner: Optional[str] = None
    model: str = "claude-sonnet-5"
    status: Literal["active", "draft", "superseded"] = "active"
    tags: list[str] = Field(default_factory=lambda: ["check"])
    aliases: list[str] = Field(default_factory=list)
    summary: str


class FormatFrontmatter(SkillMetaMixin, AuthorshipMixin):
    """Frontmatter schema for Skills/FORMAT/*.md — agent-executable
    runbooks that produce or structure an artifact in a defined shape."""

    type: Literal["format"] = "format"
    domain: str
    trigger: str
    frequency: str
    tools: list[str] | str = Field(default_factory=list)
    owner: Optional[str] = None
    model: str = "claude-sonnet-5"
    status: Literal["active", "draft", "superseded"] = "active"
    tags: list[str] = Field(default_factory=lambda: ["format"])
    aliases: list[str] = Field(default_factory=list)
    summary: str


class RuleFrontmatter(SkillMetaMixin, AuthorshipMixin):
    """Frontmatter schema for Skills/RULE/*.md — standing conventions
    and policies an agent must always follow."""

    type: Literal["rule"] = "rule"
    domain: str
    trigger: str
    frequency: str = "always"
    tools: list[str] | str = Field(default_factory=list)
    owner: Optional[str] = None
    model: str = "claude-sonnet-5"
    status: Literal["active", "draft", "superseded"] = "active"
    tags: list[str] = Field(default_factory=lambda: ["rule"])
    aliases: list[str] = Field(default_factory=list)
    summary: str


class ConceptFrontmatter(AuthorshipMixin):
    """Frontmatter schema for 05 concepts/*.md — evergreen, rewritten in place."""

    type: Literal["concept"] = "concept"
    description: str  # one stable sentence — single-sources the index one-liner
    updated: str
    status: Literal["current", "stale"] = "current"
    tags: list[str] = Field(default_factory=lambda: ["concept"])
    resource: Optional[str] = None

    @field_validator("updated", mode="before")
    @classmethod
    def _check_iso_date(cls, v: object) -> str:
        return _validate_iso_date(v)


class ProjectFrontmatter(AuthorshipMixin):
    """Frontmatter schema for 03 Projects/*.md — GTD H1: goal-directed
    workstreams with a genuine endpoint (the endpoint test) and a lifecycle
    status. `pending` = the Someday/Maybe bucket (opened, waiting on a
    trigger; exempt from the next-action audit like `paused`). Live projects
    must carry an `area:` up-link — the 02 Areas/ note the project serves
    ("[[<area-slug>]]"); `serves:` optionally points at a goal/horizon and
    never replaces `area:`."""

    type: Literal["project"] = "project"
    description: str
    status: Literal["pending", "active", "paused", "done"] = "active"
    started: Optional[str] = None
    updated: str
    area: Optional[str] = None
    serves: Optional[list[str] | str] = None
    tags: list[str] = Field(default_factory=lambda: ["project"])

    @field_validator("started", "updated", mode="before")
    @classmethod
    def _check_iso_date(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        return _validate_iso_date(v)

    @field_validator("area")
    @classmethod
    def _area_required_when_live(cls, v, info):
        # status is declared before area, so it is available in info.data
        if info.data.get("status", "active") != "done" and not v:
            raise ValueError('live projects must carry an area: up-link ("[[<area-slug>]]")')
        return v

    @field_validator("serves")
    @classmethod
    def _serves_wikilinks(cls, v):
        return _require_wikilinks(v, "serves")


class PersonFrontmatter(AuthorshipMixin):
    """Frontmatter schema for 04 People/*.md — one note per person,
    the single source of truth for per-person detail."""

    model_config = {"populate_by_name": True}

    type: Literal["person"] = "person"
    status: Literal["active", "exec", "dormant", "departing", "tbc"] = "active"
    org: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    reports_to: Optional[str] = Field(default=None, alias="reports-to")
    location: Optional[str] = None
    # Relationship to the KB owner — side-of-family in the value when it
    # matters (e.g. "brother-in-law — {{spouse}}'s brother"). Relations
    # frontmatter: seek relationships by rg over frontmatter first.
    relation: Optional[str] = None
    tags: list[str] = Field(default_factory=lambda: ["person"])
    aliases: list[str] = Field(default_factory=list)


class OrgFrontmatter(AuthorshipMixin):
    """A business/vendor note living in 04 People/ beside the people
    (relations frontmatter). `found-by:` is the up-link to the person who
    brought the relationship into the household. Up-links only: the org
    never lists its clients — assets point here via `serviced-by:`."""

    model_config = {"populate_by_name": True}

    type: Literal["org"] = "org"
    status: Literal["active", "dormant"] = "active"
    org: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    found_by: Optional[str] = Field(default=None, alias="found-by")
    tags: list[str] = Field(default_factory=lambda: ["org"])
    aliases: list[str] = Field(default_factory=list)

    @field_validator("found_by")
    @classmethod
    def _found_by_wikilink(cls, v):
        return _require_wikilinks(v, "found-by")


class AreaFrontmatter(AuthorshipMixin):
    """GTD H2 — ongoing responsibilities (02 Areas/, sub-areas in
    02 Areas/Assets/). Never `done`; maintained to a standard (`## Standard`)
    and reviewed on cadence (`review:` + `reviewed:`). Sub-areas up-link a
    parent via `area:`; areas may declare `serves:` (→ a goal note or a
    horizon). Asset sub-areas may carry `owner:` (the owner's name |
    household | "[[Full Name]]") and `serviced-by:` (→ a `type: org` note)."""

    model_config = {"populate_by_name": True}

    type: Literal["area"] = "area"
    description: str
    status: Literal["current"] = "current"
    updated: str
    review: Literal["weekly", "monthly", "quarterly"]
    reviewed: str
    area: Optional[str] = None
    serves: Optional[list[str] | str] = None
    owner: Optional[str] = None
    serviced_by: Optional[list[str] | str] = Field(default=None, alias="serviced-by")
    tags: list[str] = Field(default_factory=lambda: ["area"])
    aliases: list[str] = Field(default_factory=list)

    @field_validator("serviced_by")
    @classmethod
    def _serviced_by_wikilinks(cls, v):
        return _require_wikilinks(v, "serviced-by")

    @field_validator("updated", "reviewed", mode="before")
    @classmethod
    def _check_iso_date(cls, v: object) -> str:
        return _validate_iso_date(v)

    @field_validator("serves")
    @classmethod
    def _serves_wikilinks(cls, v):
        return _require_wikilinks(v, "serves")


class GoalFrontmatter(AuthorshipMixin):
    """GTD H3 outcome — one note in 01 Horizons/Goals/<slug>.md. Up-links the
    H3 index via `horizon: "[[goals]]"`. No review cadence of its own —
    reviewing Goals/index.md walks these. Areas/projects point here with
    an optional `serves:`."""

    type: Literal["goal"] = "goal"
    description: str
    status: Literal["current"] = "current"
    updated: str
    horizon: str
    order: int
    tags: list[str] = Field(default_factory=lambda: ["goal"])

    @field_validator("updated", mode="before")
    @classmethod
    def _check_iso_date(cls, v: object) -> str:
        return _validate_iso_date(v)

    @field_validator("horizon")
    @classmethod
    def _horizon_wikilink(cls, v: str) -> str:
        if not (isinstance(v, str) and v.startswith("[[") and v.endswith("]]")):
            raise ValueError('horizon: must be a wikilink ("[[goals]]")')
        return v


class HorizonFrontmatter(AuthorshipMixin):
    """GTD H3–H5 orientation notes (01 Horizons/ — H3 is Goals/index.md with
    aliases: [goals]; H4 vision.md; H5 purpose-principles.md). Reviewed on
    cadence like areas; content is rewritten in place."""

    type: Literal["horizon"] = "horizon"
    level: Literal["H3", "H4", "H5"]
    description: str
    status: Literal["current"] = "current"
    updated: str
    review: Literal["quarterly", "yearly"]
    reviewed: str
    tags: list[str] = Field(default_factory=lambda: ["horizon"])
    aliases: list[str] = Field(default_factory=list)

    @field_validator("updated", "reviewed", mode="before")
    @classmethod
    def _check_iso_date(cls, v: object) -> str:
        return _validate_iso_date(v)
