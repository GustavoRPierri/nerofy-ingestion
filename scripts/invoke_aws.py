#!/usr/bin/env python3
"""Invoca o handler via SAM CLI apontando para AWS real.

Uso:
    python scripts/invoke_aws.py                # event item/updated (padrão)
    python scripts/invoke_aws.py item
    python scripts/invoke_aws.py transactions
    python scripts/invoke_aws.py connector
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

_EVENT_FILES = {
    "item":         "events/sqs_item_update.json",
    "transactions": "events/sqs_transactions.json",
    "connector":    "events/sqs_connector.json",
}

def main() -> None:
    event_type = sys.argv[1] if len(sys.argv) > 1 else "item"
    event_file = ROOT / _EVENT_FILES.get(event_type, _EVENT_FILES["item"])

    if not event_file.exists():
        print(f"ERRO: arquivo de evento não encontrado: {event_file}")
        sys.exit(1)

    print(f"Invocando via SAM: {event_type} → {event_file.name}")

    result = subprocess.run(
        [
            "sam", "local", "invoke", "IngestionFunction",
            "--event", str(event_file),
            "--profile", "nerofy",
            "--region", "sa-east-1",
        ],
        cwd=str(ROOT),
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
