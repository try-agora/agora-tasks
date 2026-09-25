"""Judge input preservation and real Sphinx builds, not a preferred regexp."""

import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

WORKSPACE = Path(os.environ.get("TASK_WORKSPACE", "/app")).resolve()
LOGS = Path(os.environ.get("VERIFIER_LOGS", "/logs/verifier")).resolve()
sys.path[:0] = [str(WORKSPACE / "src"), str(WORKSPACE / "vendor")]
PROLOG = ".. |product| replace:: Atlas SDK"


class Behavior(unittest.TestCase):
    def prepended(self, lines, prolog=PROLOG):
        from docutils.statemachine import StringList
        from sphinx.util.rst import prepend_prolog

        content = StringList(lines, source="original.rst")
        prepend_prolog(content, prolog)
        return content

    def test_roles_do_not_split_heading_from_underline(self):
        for title in (
            ":mod:`library.client`",
            ":py:class:`Customer`",
            ":py:func:`connect` API",
            ":ref:`guide-label`",
        ):
            with self.subTest(title=title):
                lines = [title, "=" * (len(title) + 4), "", "Use |product|."]
                content = self.prepended(lines)
                index = list(content).index(title)
                self.assertEqual(list(content)[index:], lines)
                self.assertLess(list(content).index(PROLOG), index)
                for offset in range(len(lines)):
                    self.assertEqual(
                        content.info(index + offset), ("original.rst", offset)
                    )

    def test_leading_fields_stay_before_prolog(self):
        fields = [
            ":author: Ada",
            ":release channel: stable",
            r":escaped\:name: value",
            ":empty:",
        ]
        lines = [
            *fields,
            "",
            ":mod:`library.client`",
            "=======================",
            "",
            "Body.",
        ]
        content = self.prepended(lines)
        self.assertEqual(list(content)[: len(fields)], fields)
        prolog_index = list(content).index(PROLOG)
        title_index = list(content).index(lines[5])
        self.assertGreater(prolog_index, len(fields) - 1)
        self.assertLess(prolog_index, title_index)
        self.assertEqual(content[title_index + 1], lines[6])
        for index in range(len(fields)):
            self.assertEqual(content.info(index), ("original.rst", index))
        self.assertEqual(content.info(title_index), ("original.rst", 5))

    def test_plain_heading_and_multiple_prolog_lines(self):
        lines = ["Plain heading", "=============", "", "Body."]
        prolog = ".. |first| replace:: One\n.. |second| replace:: Two"
        content = self.prepended(lines, prolog)
        title = list(content).index(lines[0])
        self.assertEqual(list(content)[title:], lines)
        for line in prolog.splitlines():
            self.assertLess(list(content).index(line), title)

    def test_no_prolog_is_a_noop(self):
        lines = [":mod:`library.client`", "=====================", "", "Body."]
        content = self.prepended(lines, "")
        self.assertEqual(list(content), lines)
        self.assertEqual(
            [content.info(i) for i in range(len(lines))],
            [("original.rst", i) for i in range(len(lines))],
        )

    def test_epilog_remains_after_original_document(self):
        from sphinx.util.rst import append_epilog

        lines = ["Title", "=====", "", "Body."]
        content = self.prepended(lines)
        append_epilog(content, ".. |closing| replace:: End")
        self.assertGreater(
            list(content).index(".. |closing| replace:: End"),
            list(content).index("Body."),
        )
        self.assertEqual(
            content.info(list(content).index("Title")), ("original.rst", 0)
        )

    def test_html_titles_navigation_substitution_and_metadata(self):
        from docutils import nodes
        from sphinx.application import Sphinx

        with tempfile.TemporaryDirectory(prefix="sphinx-documents-") as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            (source / "conf.py").write_text(
                "project = 'Independent API docs'\nmaster_doc = 'index'\nhtml_theme = 'basic'\n"
                + "rst_prolog = "
                + repr(PROLOG)
                + "\n"
            )
            titles = {
                "module": (":mod:`independent.client`", "independent.client"),
                "class": (":py:class:`Customer` API", "Customer API"),
                "function": (":py:func:`connect`", "connect()"),
                "metadata": (":mod:`independent.models`", "independent.models"),
                "plain": ("Plain API", "Plain API"),
            }
            (source / "index.rst").write_text(
                "API guide\n=========\n\n.. toctree::\n\n"
                + "".join(f"   {name}\n" for name in titles)
            )
            for name, (raw, _) in titles.items():
                metadata = ":author: Lin\n:version: 3\n\n" if name == "metadata" else ""
                (source / f"{name}.rst").write_text(
                    metadata
                    + raw
                    + "\n"
                    + "=" * (len(raw) + 5)
                    + "\n\nBuilt for |product|.\n"
                )
            warning = io.StringIO()
            app = Sphinx(
                str(source),
                str(source),
                str(root / "html"),
                str(root / "doctrees"),
                "html",
                status=io.StringIO(),
                warning=warning,
                freshenv=True,
            )
            app.build(force_all=True)
            self.assertEqual(app.statuscode, 0, warning.getvalue())
            index_html = (root / "html/index.html").read_text()
            for name, (_, expected) in titles.items():
                with self.subTest(document=name):
                    tree = app.env.get_doctree(name)
                    headings = list(tree.findall(nodes.title))
                    self.assertTrue(headings, "Document lost its heading")
                    self.assertEqual(headings[0].astext(), expected)
                    self.assertEqual(app.env.titles[name].astext(), expected)
                    self.assertIn("Atlas SDK", tree.astext())
                    self.assertIn(f'href="{name}.html"', index_html)
                    self.assertIn("<h1", (root / f"html/{name}.html").read_text())
            self.assertEqual(app.env.metadata["metadata"]["author"], "Lin")
            self.assertEqual(app.env.metadata["metadata"]["version"], "3")


if __name__ == "__main__":
    LOGS.mkdir(parents=True, exist_ok=True)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Behavior)
    )
    evidence = {
        "tests_run": result.testsRun,
        "failures": [{"test": str(t), "traceback": s} for t, s in result.failures],
        "errors": [{"test": str(t), "traceback": s} for t, s in result.errors],
        "passed": result.wasSuccessful(),
    }
    (LOGS / "checks.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (LOGS / "reward.txt").write_text("1\n" if result.wasSuccessful() else "0\n")
