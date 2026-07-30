# Copyright (c) 2026, Frappe and contributors
# See license.txt

import unittest
from pathlib import Path

DOCKERFILE = Path(__file__).resolve().parents[1] / "docker" / "Dockerfile"


class TestRuntimeImageTemplate(unittest.TestCase):
	def test_runtime_is_flattened_without_changing_the_default_full_image(self):
		template = DOCKERFILE.read_text(encoding="utf-8")

		self.assertIn("# syntax=docker/dockerfile:1.10", template)
		self.assertIn("FROM ubuntu:22.04{% if doc.apply_new_build %} AS builder{% endif %}", template)
		self.assertIn("FROM builder AS runtime-files", template)
		self.assertIn("FROM runtime-files AS runtime-layers", template)
		self.assertIn("FROM scratch AS runtime", template)
		self.assertIn("FROM builder AS full", template)
		self.assertIn(
			"COPY --chown=frappe:frappe apps/{{ app.app }}/dashboard "
			"/home/frappe/frappe-bench/apps/{{ app.app }}/dashboard",
			template.split("FROM builder AS full", 1)[1],
		)

	def test_runtime_groups_are_independent_linked_layers(self):
		runtime = DOCKERFILE.read_text(encoding="utf-8").split("FROM scratch AS runtime", 1)[1]
		copies = [line for line in runtime.splitlines() if "COPY" in line and "--from=runtime-layers" in line]

		self.assertGreater(len(copies), 6)
		self.assertTrue(all(line.startswith("COPY --link --from=runtime-layers") for line in copies))

	def test_each_runtime_app_is_an_independent_linked_layer(self):
		template = DOCKERFILE.read_text(encoding="utf-8")

		self.assertIn(
			"COPY --link --from=runtime-layers "
			"/runtime-layers/apps/home/frappe/frappe-bench/apps/{{ app.app }} "
			"/home/frappe/frappe-bench/apps/{{ app.app }}",
			template,
		)

	def test_runtime_keeps_prebuilt_assets_and_only_realtime_node_modules(self):
		template = DOCKERFILE.read_text(encoding="utf-8")
		runtime_cleanup = template.split("FROM builder AS runtime-files", 1)[1]

		self.assertIn("/home/frappe/runtime/sites-assets", template)
		self.assertIn("-name node_modules", runtime_cleanup)
		self.assertIn('"socket.io", "@redis/client", "superagent", "cookie"', template)
		self.assertIn("NODE_PATH=/home/frappe/runtime/socketio/node_modules", template)
		self.assertIn(
			"target=/home/frappe/frappe-bench/apps/{{ app.app }}/dashboard/node_modules",
			template.split("{% if doc.apply_new_build %}", 1)[1],
		)

	def test_runtime_preserves_declared_system_packages(self):
		template = DOCKERFILE.read_text(encoding="utf-8")
		runtime_cleanup = template.split("FROM builder AS runtime-files", 1)[1]

		self.assertNotIn("apt-get purge", runtime_cleanup)
		self.assertNotIn("rm -rf /etc/fonts /usr/share/fonts", runtime_cleanup)


if __name__ == "__main__":
	unittest.main()
