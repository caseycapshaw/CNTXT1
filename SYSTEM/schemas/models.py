"""Instance-local schema layer. Re-exports the shared base classes unchanged
(a downstream repo would subclass instead, e.g. to add a required `owner`
field), and defines the classes that are a local decision rather than part of
the shared schema (AgentFrontmatter).
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from SYSTEM.schemas.base_models import (
    CheckFrontmatter, ConceptFrontmatter, DoFrontmatter, FormatFrontmatter,
    InitiativeFrontmatter, PersonFrontmatter, RuleFrontmatter,
    _validate_iso_date,
)


class AgentFrontmatter(BaseModel):
    """Frontmatter schema for Knowledge/Agents/*.md — real Claude Code subagent
    definitions, symlinked into ~/.claude/agents/ for direct use, and also
    launchable as CMUX pane-worker system prompts (--append-system-prompt).

    `version` is a QUOTED string (bare x.10 parses as the YAML float x.1);
    bump per the revision-history rule in the domain-advisor TEMPLATE;
    supersede, never revert. `updated` is optional ISO date.
    """
    name: str
    description: str
    version: Optional[str] = None
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
    tools: list[str] | None = None
    color: Literal["red", "green", "yellow", "cyan", "pink", "blue", "purple", "orange"] | None = None
    status: Literal["active", "draft", "deprecated"] = "active"
    tags: list[str] = Field(default_factory=list)
    updated: Optional[str] = None

    @field_validator("updated", mode="before")
    @classmethod
    def _check_updated(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        return _validate_iso_date(v)


__all__ = [
    "AgentFrontmatter",
    "CheckFrontmatter",
    "ConceptFrontmatter",
    "DoFrontmatter",
    "FormatFrontmatter",
    "InitiativeFrontmatter",
    "PersonFrontmatter",
    "RuleFrontmatter",
]
