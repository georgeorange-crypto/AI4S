"""Safe, hash-addressed reader for the Agent Skills SKILL.md format."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from ..core import ResearchStore

MAX_SKILL_FILES = 64
MAX_SKILL_BYTES = 512_000
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KNOWN_TOOLS = {"crossref_search", "crossref_resolve"}
KNOWN_PERMISSIONS = {"crossref.search", "crossref.resolve"}
KNOWN_RULES = {"citation_identity_only", "no_abstracts", "no_claim_support_inference"}


class SkillValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SkillBundle:
    name: str
    description: str
    license: str | None
    version: str
    allowed_tools: tuple[str, ...]
    permissions: tuple[str, ...]
    rules: tuple[str, ...]
    instructions: str
    content_sha256: str
    source_path: str


class SkillRegistry:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def load(self, name: str) -> SkillBundle:
        if not NAME_PATTERN.fullmatch(name):
            raise SkillValidationError("invalid skill directory name")
        skill_dir = (self.root / name).resolve()
        if skill_dir.parent != self.root or not skill_dir.is_dir():
            raise SkillValidationError("skill path must be a direct directory under the registry root")
        files = sorted(skill_dir.rglob("*"))
        regular_files = [path for path in files if path.is_file()]
        if len(regular_files) > MAX_SKILL_FILES:
            raise SkillValidationError("skill bundle has too many files")
        for path in files:
            if path.is_symlink():
                raise SkillValidationError("symlinks are not allowed in a skill bundle")
            if path.is_file() and path.stat().st_size > MAX_SKILL_BYTES:
                raise SkillValidationError("skill bundle file exceeds the size limit")
        manifest_path = skill_dir / "SKILL.md"
        if not manifest_path.is_file():
            raise SkillValidationError("SKILL.md is required")
        manifest_text = manifest_path.read_text(encoding="utf-8")
        match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", manifest_text, flags=re.DOTALL)
        if not match:
            raise SkillValidationError("SKILL.md must start with YAML frontmatter")
        try:
            metadata = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            raise SkillValidationError(f"invalid safe YAML frontmatter: {type(exc).__name__}") from None
        if not isinstance(metadata, dict) or not all(isinstance(key, str) for key in metadata):
            raise SkillValidationError("skill frontmatter must be a YAML mapping with string keys")
        declared_name = metadata.get("name")
        description = metadata.get("description")
        if declared_name != name or not isinstance(declared_name, str) or not NAME_PATTERN.fullmatch(declared_name):
            raise SkillValidationError("skill name must match its directory and Agent Skills naming rules")
        if not isinstance(description, str) or not description.strip() or len(description) > 1024:
            raise SkillValidationError("skill description must contain 1 to 1024 characters")
        if len(declared_name) > 64 or "--" in declared_name:
            raise SkillValidationError("skill name violates the Agent Skills specification")
        allowed = metadata.get("allowed-tools", "")
        if not isinstance(allowed, str):
            raise SkillValidationError("allowed-tools must be a space-separated string")
        allowed_tools = tuple(allowed.split())
        unknown_tools = set(allowed_tools) - KNOWN_TOOLS
        if unknown_tools:
            raise SkillValidationError(f"skill requests unknown tools: {', '.join(sorted(unknown_tools))}")
        extension = metadata.get("metadata", {})
        if not isinstance(extension, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in extension.items()
        ):
            raise SkillValidationError("Agent Skills metadata values must be strings")
        permissions = _tokens(extension.get("ai4s_permissions", ""))
        rules = _tokens(extension.get("ai4s_rules", ""))
        if set(permissions) - KNOWN_PERMISSIONS:
            raise SkillValidationError("skill requests an unknown permission")
        if set(rules) - KNOWN_RULES:
            raise SkillValidationError("skill references an unknown policy rule")
        instructions = match.group(2).strip()
        if not instructions:
            raise SkillValidationError("skill instructions must not be empty")
        content_hash = hashlib.sha256()
        for path in regular_files:
            relative = path.relative_to(skill_dir).as_posix()
            content_hash.update(relative.encode("utf-8") + b"\0" + path.read_bytes())
        version = extension.get("version", "unversioned")
        if len(version) > 120:
            raise SkillValidationError("skill version is too long")
        license_name = metadata.get("license")
        if license_name is not None and not isinstance(license_name, str):
            raise SkillValidationError("skill license must be a string")
        return SkillBundle(
            name=name,
            description=description,
            license=license_name,
            version=version,
            allowed_tools=allowed_tools,
            permissions=permissions,
            rules=rules,
            instructions=instructions,
            content_sha256=content_hash.hexdigest(),
            source_path=str(skill_dir),
        )

    def activate(self, store: ResearchStore, skill: SkillBundle, approval_id: str) -> None:
        scope = skill_approval_scope(skill)
        store.consume_approvals([(approval_id, "skill_activation", scope)])


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(token.strip() for token in value.split(",") if token.strip())


def skill_approval_scope(skill: SkillBundle) -> str:
    return f"skill-activation:{skill.name}:{skill.content_sha256}"
