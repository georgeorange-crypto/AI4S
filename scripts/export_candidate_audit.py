"""Export a transparent candidate checklist; discovery data is never promoted to verified."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sources = [
    ("resource_candidate", ROOT / "registries/original_resource_catalog.json"),
    ("discovery_index", ROOT / "registries/discovery_indexes.json"),
]
fields = [
    "candidate_class",
    "name",
    "url",
    "organization_or_authority",
    "priority",
    "license_status",
    "maintenance_status",
    "execution_risk",
    "smoke_test",
    "integration_status",
    "discovery_notes",
]
with (ROOT / "docs/INTEGRATION_CANDIDATES.csv").open("w", newline="", encoding="utf-8-sig") as target:
    writer = csv.DictWriter(target, fieldnames=fields)
    writer.writeheader()
    count = 0
    for kind, path in sources:
        for row in json.loads(path.read_text(encoding="utf-8")):
            writer.writerow(
                {
                    "candidate_class": kind,
                    "name": row.get("name", ""),
                    "url": row.get("url", ""),
                    "organization_or_authority": row.get("organization", row.get("authority", "")),
                    "priority": row.get("priority", ""),
                    "license_status": "unknown_not_audited",
                    "maintenance_status": "not_checked",
                    "execution_risk": "unreviewed_do_not_execute",
                    "smoke_test": "not_run",
                    "integration_status": "discovered",
                    "discovery_notes": row.get("adoption_risk", row.get("notes", "")),
                }
            )
            count += 1
print(f"wrote {count} candidate records")
