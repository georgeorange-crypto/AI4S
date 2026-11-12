"""Import discovery inputs into the configured SQLAlchemy registry without enabling tools."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sqlalchemy import func, select

from ai4s.core import canonical_url, now
from ai4s.database import SessionFactory
from ai4s.orm import CapabilityEntry, DiscoveryIndex, Resource, ResourceObservation

ROOT = Path(__file__).resolve().parents[1]


def stable_id(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:32]


def main() -> None:
    resources = json.loads((ROOT / "registries/original_resource_catalog.json").read_text(encoding="utf-8"))
    indexes = json.loads((ROOT / "registries/discovery_indexes.json").read_text(encoding="utf-8"))
    capabilities = json.loads((ROOT / "registries/runtime_dependency_audit.json").read_text(encoding="utf-8"))[
        "dependencies"
    ]
    with SessionFactory.begin() as session:
        for item in resources:
            url = canonical_url(item.get("url", ""))
            rid = stable_id(url)
            payload = json.loads(json.dumps(item, ensure_ascii=False))
            row = session.get(Resource, rid)
            if row is None:
                row = Resource(
                    resource_id=rid,
                    canonical_url=url,
                    kind=item.get("category", "unknown"),
                    name=item.get("name", ""),
                    maintainer=item.get("organization"),
                    license_status="unknown",
                    version_or_commit=None,
                    integration_status="discovered",
                    execution_risk="unreviewed",
                    notes=item.get("notes", ""),
                    source_payload=payload,
                )
                session.add(row)
            observation_id = stable_id(json.dumps(payload, sort_keys=True, ensure_ascii=False))
            if session.get(ResourceObservation, observation_id) is None:
                session.add(
                    ResourceObservation(
                        observation_id=observation_id,
                        resource_id=rid,
                        source_id="original_resource_catalog.json",
                        source_payload=payload,
                    )
                )
        for item in indexes:
            url = canonical_url(item.get("url", ""))
            iid = stable_id(url + "\0" + item.get("name", ""))
            if session.get(DiscoveryIndex, iid) is None:
                session.add(
                    DiscoveryIndex(
                        index_id=iid,
                        index_type=item.get("type", "unknown"),
                        name=item.get("name", ""),
                        url=url,
                        authority=item.get("authority", "unknown"),
                        priority=item.get("priority", ""),
                        verified_state=item.get("verified", "unverified"),
                        date_checked=item.get("date_checked"),
                        source_payload=item,
                    )
                )
        for item in capabilities:
            entry = CapabilityEntry(
                capability_id=item["id"],
                version=item["version"],
                source=item["source"],
                license=item["license"],
                integration_status=item["integration_status"],
                execution_risk=item["execution_risk"],
                permissions=item["permissions"],
                secrets=item["secrets"],
                evidence=item["evidence"],
            )
            session.merge(entry)
        session.flush()
        result = {
            "resource_entities": session.scalar(select(func.count()).select_from(Resource)),
            "resource_observations": session.scalar(select(func.count()).select_from(ResourceObservation)),
            "discovery_indexes": session.scalar(select(func.count()).select_from(DiscoveryIndex)),
            "runtime_capabilities": session.scalar(select(func.count()).select_from(CapabilityEntry)),
            "integration_status": "discovered_only",
            "imported_at": now(),
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
