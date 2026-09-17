from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "ai-video-editing-susume"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in {"a", "link", "script", "img"}:
            return
        values = dict(attrs)
        attribute = "href" if tag in {"a", "link"} else "src"
        value = values.get(attribute)
        if value:
            self.links.append(value)


class RepositoryTests(unittest.TestCase):
    def test_manifest_paths_exist(self) -> None:
        manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], PLUGIN.name)
        for field in ("skills",):
            self.assertTrue((PLUGIN / manifest[field]).exists())
        for field in ("composerIcon", "logo"):
            self.assertTrue((PLUGIN / manifest["interface"][field]).exists())

    def test_marketplace_points_to_plugin(self) -> None:
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], PLUGIN.name)
        self.assertEqual(entry["source"]["path"], "./plugins/ai-video-editing-susume")
        self.assertIn(entry["policy"]["installation"], {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"})

    def test_skill_is_compact(self) -> None:
        skill = PLUGIN / "skills" / "ai-video-editing-susume" / "SKILL.md"
        self.assertLessEqual(len(skill.read_text(encoding="utf-8").splitlines()), 200)

    def test_html_internal_links_exist(self) -> None:
        docs = ROOT / "docs"
        failures: list[str] = []
        for page in docs.rglob("*.html"):
            parser = LinkParser()
            parser.feed(page.read_text(encoding="utf-8"))
            for link in parser.links:
                if link.startswith(("http://", "https://", "mailto:", "#", "data:")):
                    continue
                clean = link.split("#", 1)[0].split("?", 1)[0]
                if not clean:
                    continue
                target = (page.parent / clean).resolve()
                if not target.exists():
                    failures.append(f"{page.relative_to(ROOT)} -> {link}")
        self.assertEqual(failures, [])

    def test_no_private_absolute_paths_or_secrets(self) -> None:
        patterns = [
            re.compile(r"/Users/[A-Za-z0-9._-]+/"),
            re.compile(r"/home/[A-Za-z0-9._-]+/"),
            re.compile(r"(?i)(api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"][^'\"]+"),
        ]
        failures: list[str] = []
        for path in ROOT.rglob("*"):
            if (
                not path.is_file()
                or ".git" in path.parts
                or "__pycache__" in path.parts
                or path.suffix.lower() in {".pyc", ".png", ".jpg", ".gif", ".woff", ".woff2"}
            ):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in patterns:
                if pattern.search(text):
                    failures.append(str(path.relative_to(ROOT)))
                    break
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
