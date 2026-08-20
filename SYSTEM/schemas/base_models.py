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


class DoFrontmatter(AuthorshipMixin):
    """Frontmatter schema for CONTENT/Skills/DO/*.md — agent-executable runbooks
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


class CheckFrontmatter(AuthorshipMixin):
    """Frontmatter schema for CONTENT/Skills/CHECK/*.md — agent-executable
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


class FormatFrontmatter(AuthorshipMixin):
    """Frontmatter schema for CONTENT/Skills/FORMAT/*.md — agent-executable
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


class RuleFrontmatter(AuthorshipMixin):
    """Frontmatter schema for CONTENT/Skills/RULE/*.md — standing conventions
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
    """Frontmatter schema for CONTENT/Concepts/*.md — evergreen, rewritten in place."""

    type: Literal["concept"] = "concept"
    updated: str
    status: Literal["current", "stale"] = "current"
    tags: list[str] = Field(default_factory=lambda: ["concept"])
    resource: Optional[str] = None

    @field_validator("updated", mode="before")
    @classmethod
    def _check_iso_date(cls, v: object) -> str:
        return _validate_iso_date(v)


class InitiativeFrontmatter(AuthorshipMixin):
    """Frontmatter schema for CONTENT/Initiatives/*.md — goal-directed
    workstreams with a lifecycle status."""

    type: Literal["initiative"] = "initiative"
    description: str
    status: Literal["active", "paused", "done"] = "active"
    started: Optional[str] = None
    updated: str
    tags: list[str] = Field(default_factory=lambda: ["initiative"])

    @field_validator("started", "updated", mode="before")
    @classmethod
    def _check_iso_date(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        return _validate_iso_date(v)


class PersonFrontmatter(AuthorshipMixin):
    """Frontmatter schema for CONTENT/People/*.md — one note per person,
    the single source of truth for per-person detail."""

    model_config = {"populate_by_name": True}

    type: Literal["person"] = "person"
    status: Literal["active", "exec", "dormant", "departing", "tbc"] = "active"
    org: Optional[str] = None
    team: Optional[str] = None
    role: Optional[str] = None
    reports_to: Optional[str] = Field(default=None, alias="reports-to")
    location: Optional[str] = None
    tags: list[str] = Field(default_factory=lambda: ["person"])
    aliases: list[str] = Field(default_factory=list)
