"""Instance-local schema layer. Re-exports the shared base classes unchanged
(a downstream repo would subclass instead, e.g. to add a required `owner`
field), and defines the classes that are a local decision rather than part of
the shared schema (AgentFrontmatter).
"""

from typing import Literal
from pydantic import BaseModel, Field
from SYSTEM.schemas.base_models import (
    CheckFrontmatter, ConceptFrontmatter, DoFrontmatter, FormatFrontmatter,
    InitiativeFrontmatter, PersonFrontmatter, RuleFrontmatter,
)


class AgentFrontmatter(BaseModel):
    """Frontmatter schema for CONTENT/Agents/*.md — real Claude Code subagent
    definitions, symlinked into ~/.claude/agents/ for direct use, and also
    launchable as CMUX pane-worker system prompts (--append-system-prompt).
    """
    name: str
    description: str
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
    tools: list[str] | None = None
    color: Literal["red", "green", "yellow", "cyan", "pink", "blue", "purple", "orange"] | None = None
    status: Literal["active", "draft", "deprecated"] = "active"
    tags: list[str] = Field(default_factory=list)


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
