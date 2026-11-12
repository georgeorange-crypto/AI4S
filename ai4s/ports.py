"""Replaceable interfaces; provider-specific integrations must implement these ports."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolContext:
    project_id: str
    workflow_id: str
    principal_id: str
    budget_id: str
    trace_id: str
    approval_id: str | None = None


class ModelGateway(Protocol):
    def generate(self, messages: list[Mapping[str, str]], policy: Mapping[str, Any]) -> Mapping[str, Any]: ...


class AgentHarness(Protocol):
    def execute(self, task: Mapping[str, Any], context: ToolContext) -> Mapping[str, Any]: ...


class ToolAdapter(Protocol):
    name: str
    version: str

    def healthcheck(self) -> Mapping[str, Any]: ...
    def invoke(self, input_data: Mapping[str, Any], context: ToolContext) -> Mapping[str, Any]: ...


class ExperimentExecutor(Protocol):
    def submit(self, contract_id: str, idempotency_key: str) -> str: ...
    def status(self, job_id: str) -> Mapping[str, Any]: ...
    def cancel(self, job_id: str) -> None: ...


class ArtifactStore(Protocol):
    def store_artifact(
        self, workflow_id: str, name: str, content: bytes, root: str, media_type: str
    ) -> Mapping[str, str]: ...
    def get_artifact(self, artifact_id: str) -> bytes: ...


class ResourceRegistry(Protocol):
    def ingest(self, resources_path: str, discoveries_path: str) -> Mapping[str, int]: ...
    def list(self, status: str | None = None) -> list[Mapping[str, Any]]: ...
