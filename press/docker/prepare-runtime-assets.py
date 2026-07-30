# Copyright (c) 2026, Frappe and contributors
# See license.txt

from __future__ import annotations

import json
import sys
from pathlib import Path


def prepare_runtime_assets(assets_path: Path, excluded_apps_path: Path) -> None:
	excluded_apps = set(excluded_apps_path.read_text(encoding="utf-8").split())

	for manifest_path in (
		assets_path / "assets.json",
		assets_path / "assets-rtl.json",
	):
		assets = json.loads(manifest_path.read_text(encoding="utf-8"))
		assets = {
			key: value
			for key, value in assets.items()
			if value.split("/", 3)[2] not in excluded_apps
		}
		missing_assets = [
			value
			for value in assets.values()
			if value.startswith("/assets/")
			and not (assets_path / value.removeprefix("/assets/")).exists()
		]
		if missing_assets:
			raise RuntimeError(
				f"{manifest_path.name} references missing runtime assets: {', '.join(missing_assets)}"
			)

		manifest_path.write_text(
			json.dumps(assets, separators=(",", ":"), sort_keys=True),
			encoding="utf-8",
		)


if __name__ == "__main__":
	prepare_runtime_assets(Path(sys.argv[1]), Path(sys.argv[2]))
