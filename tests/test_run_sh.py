"""The launcher must keep a user's private workspace across runs."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent.parent / "run.sh"


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copyfile(SCRIPT, self.root / "run.sh")
        for name in ("AGENTS.md", "CLAUDE.md", "LICENSE", ".gitignore", "salary_lookup.py"):
            (self.root / name).write_text("source\n")
        for name in (".claude", "portal-skills/skills", ".hermes", "cv", "cover_letters", "documents",
                     "templates", "tools", "job_scraper", "upskill", "company_research"):
            (self.root / name).mkdir(parents=True)
        (self.root / "cv/main_example.tex").write_text("source\n")
        (self.root / "bin").mkdir()
        docker = self.root / "bin/docker"
        docker.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$DOCKER_LOG"\n')
        docker.chmod(0o755)
        self.log = self.root / "docker.log"
        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.root / 'bin'}:{self.env['PATH']}"
        self.env["DOCKER_LOG"] = str(self.log)

    def run_launcher(self):
        return subprocess.run(["sh", "run.sh"], cwd=self.root, env=self.env,
                              capture_output=True, text=True)

    def test_first_run_initializes_and_later_run_preserves_changes(self):
        first = self.run_launcher()
        self.assertEqual(first.returncode, 0, first.stderr)
        private = self.root / "work"
        self.assertEqual((private / "cv/main_example.tex").read_text(), "source\n")
        self.assertTrue((private / ".agents/skills").is_dir())
        self.assertFalse((private / "run.sh").exists())
        (private / "cv/main_example.tex").write_text("private edit\n")
        (self.root / ".runtime/hermes/auth.json").write_text("{}")
        second = self.run_launcher()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((private / "cv/main_example.tex").read_text(), "private edit\n")
        calls = self.log.read_text().splitlines()
        self.assertEqual(calls.count("compose run --rm hermes auth add openai-codex --type oauth"), 1)
        self.assertEqual(calls.count("compose run --rm hermes model"), 1)
        self.assertEqual(calls.count("compose run --rm hermes"), 2)

    def test_existing_uninitialized_workspace_is_not_overwritten(self):
        private = self.root / "work"
        private.mkdir(parents=True)
        (private / "profile.txt").write_text("keep\n")
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to overwrite", result.stderr)
        self.assertEqual((private / "profile.txt").read_text(), "keep\n")

    def test_standard_agents_directory_is_copied(self):
        (self.root / "portal-skills").rename(self.root / ".agents")
        result = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / "work/.agents/skills").is_dir())
        self.assertFalse((self.root / "work/portal-skills").exists())


if __name__ == "__main__":
    unittest.main()
