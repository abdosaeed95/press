# Copyright (c) 2026, Frappe and contributors
# See license.txt

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from press.press.doctype.deploy_candidate.docker_output_parsers import DockerBuildOutputParser


class TestDockerBuildOutputParser(unittest.TestCase):
	def get_parser(self, build_steps):
		with patch("press.press.doctype.deploy_candidate.docker_output_parsers.now_datetime"):
			return DockerBuildOutputParser(SimpleNamespace(build_steps=build_steps))

	def test_checkpoint_step_accepts_named_and_legacy_buildkit_stages(self):
		for stage in ("builder", "stage-0"):
			with self.subTest(stage=stage):
				step = SimpleNamespace(stage_slug="pre", step_slug="python")
				parser = self.get_parser([step])

				parser._parse_line(f"#8 [{stage} 8/40] RUN echo ready `#stage-pre-python`")

				self.assertIs(parser.steps[8], step)
				self.assertEqual(step.status, "Running")
				self.assertEqual(step.command, "echo ready")

	def test_named_stage_without_checkpoint_is_ignored(self):
		parser = self.get_parser([])

		parser._parse_line("#8 [builder 8/40] RUN echo ready")

		self.assertFalse(parser.steps)


if __name__ == "__main__":
	unittest.main()
