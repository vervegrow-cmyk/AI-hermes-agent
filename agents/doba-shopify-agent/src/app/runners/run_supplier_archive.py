from __future__ import annotations

import bootstrap
import json

from src.modules.supplier_archive.runners.archive import run_supplier_archive


def main() -> None:
    result = run_supplier_archive()
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

