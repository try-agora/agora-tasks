"""Independent SQLite outcomes for the public bulk-upsert contract."""

import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

WORKSPACE = Path(os.environ.get("TASK_WORKSPACE", "/app")).resolve()
LOGS = Path(os.environ.get("VERIFIER_LOGS", "/logs/verifier")).resolve()
sys.path[:0] = [str(WORKSPACE / "src"), str(WORKSPACE / "vendor")]


class Behavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import django
        from django.conf import settings

        settings.configure(
            DATABASES={
                "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
            },
            INSTALLED_APPS=[],
            USE_I18N=False,
            SECRET_KEY="isolated-verifier",
        )
        django.setup()
        from django.db import connection, models

        class Owner(models.Model):
            name = models.CharField(max_length=40)

            class Meta:
                app_label = "checks"

        class Record(models.Model):
            code = models.CharField(max_length=60, db_column="External Key")
            scope = models.IntegerField(db_column="Tenant Number", default=1)
            payload = models.CharField(max_length=80, db_column="select")
            untouched = models.IntegerField(default=17, db_column="Stable Number")
            owner = models.ForeignKey(
                Owner, on_delete=models.CASCADE, db_column="Owner Ref", null=True
            )

            class Meta:
                app_label = "checks"
                constraints = [
                    models.UniqueConstraint(
                        fields=["code", "scope"], name="unique_code_scope"
                    )
                ]

        class Keyed(models.Model):
            key = models.IntegerField(primary_key=True, db_column="Row Key")
            value = models.IntegerField(db_column="from")

            class Meta:
                app_label = "checks"

        class Assignment(models.Model):
            owner = models.ForeignKey(
                Owner, on_delete=models.CASCADE, db_column="Principal Ref", unique=True
            )
            value = models.IntegerField(db_column="Value Number")

            class Meta:
                app_label = "checks"

        cls.connection = connection
        cls.Owner, cls.Record, cls.Keyed, cls.Assignment = (
            Owner,
            Record,
            Keyed,
            Assignment,
        )
        cls.tables = (Owner, Record, Keyed, Assignment)

    def setUp(self):
        with self.connection.schema_editor() as editor:
            for model in self.tables:
                editor.create_model(model)

    def tearDown(self):
        with self.connection.schema_editor() as editor:
            for model in reversed(self.tables):
                editor.delete_model(model)

    def upsert(self, objects, **kwargs):
        return self.Record.objects.bulk_create(
            objects,
            update_conflicts=True,
            update_fields=kwargs.pop("update_fields", ["payload"]),
            unique_fields=["code", "scope"],
            **kwargs,
        )

    def test_mixed_existing_new_compound_target(self):
        self.Record.objects.create(code="alpha", scope=1, payload="old")
        self.Record.objects.create(code="alpha", scope=2, payload="keep")
        self.upsert(
            [
                self.Record(code="alpha", scope=1, payload="new", untouched=99),
                self.Record(code="beta", payload="insert"),
            ]
        )
        self.assertEqual(
            list(
                self.Record.objects.order_by("code", "scope").values_list(
                    "code", "scope", "payload", "untouched"
                )
            ),
            [
                ("alpha", 1, "new", 17),
                ("alpha", 2, "keep", 17),
                ("beta", 1, "insert", 17),
            ],
        )

    def test_explicit_primary_key_target(self):
        self.Keyed.objects.create(key=7, value=10)
        result = self.Keyed.objects.bulk_create(
            [self.Keyed(key=7, value=11), self.Keyed(key=9, value=12)],
            update_conflicts=True,
            update_fields=["value"],
            unique_fields=["key"],
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(
            list(self.Keyed.objects.order_by("key").values_list("key", "value")),
            [(7, 11), (9, 12)],
        )

    def test_pk_alias_with_custom_primary_column(self):
        self.Keyed.objects.create(key=41, value=1)
        self.Keyed.objects.bulk_create(
            [self.Keyed(key=41, value=2)],
            update_conflicts=True,
            update_fields=["value"],
            unique_fields=["pk"],
        )
        self.assertEqual(self.Keyed.objects.get(pk=41).value, 2)

    def test_foreign_key_conflict_target(self):
        owner = self.Owner.objects.create(name="owner")
        self.Assignment.objects.create(owner=owner, value=4)
        self.Assignment.objects.bulk_create(
            [self.Assignment(owner=owner, value=8)],
            update_conflicts=True,
            update_fields=["value"],
            unique_fields=["owner"],
        )
        self.assertEqual(
            list(self.Assignment.objects.values_list("owner_id", "value")),
            [(owner.pk, 8)],
        )

    def test_foreign_key_update_field(self):
        first = self.Owner.objects.create(name="first")
        second = self.Owner.objects.create(name="second")
        self.Record.objects.create(code="x", payload="before", owner=first)
        self.upsert(
            [self.Record(code="x", payload="after", owner=second)],
            update_fields=["payload", "owner"],
        )
        row = self.Record.objects.get(code="x")
        self.assertEqual(
            (row.owner_id, row.payload, row.untouched), (second.pk, "after", 17)
        )

    def test_batches_are_atomic_on_later_invalid_row(self):
        from django.db import IntegrityError

        self.Record.objects.create(code="keep", payload="original")
        with self.assertRaises(IntegrityError):
            self.upsert(
                [
                    self.Record(code="keep", payload="changed"),
                    self.Record(code="bad", payload=None),
                ],
                batch_size=1,
            )
        self.assertEqual(
            list(self.Record.objects.values_list("code", "payload")),
            [("keep", "original")],
        )

    def test_bulk_execution_and_parameter_binding(self):
        from django.test.utils import CaptureQueriesContext

        text = "雪'); DROP TABLE checks_record; --"
        rows = [self.Record(code=f"key-{i}", payload=text) for i in range(37)]
        with patch.object(
            self.Record,
            "save",
            side_effect=AssertionError("Per-row save is not bulk upsert"),
        ):
            with CaptureQueriesContext(self.connection) as queries:
                self.upsert(rows, batch_size=100)
        writes = [
            q
            for q in queries
            if q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "SELECT"))
        ]
        self.assertEqual(len(writes), 1, "Expected one set-based statement")
        self.assertEqual(self.Record.objects.filter(payload=text).count(), 37)

    def test_empty_input(self):
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(self.connection) as queries:
            self.assertEqual(self.upsert([]), [])
        self.assertEqual(len(queries), 0)

    def test_ordinary_insert_and_ignore_conflicts(self):
        self.Record.objects.bulk_create([self.Record(code="a", payload="original")])
        self.Record.objects.bulk_create(
            [
                self.Record(code="a", payload="wrong"),
                self.Record(code="b", payload="new"),
            ],
            ignore_conflicts=True,
        )
        self.assertEqual(
            list(self.Record.objects.order_by("code").values_list("code", "payload")),
            [("a", "original"), ("b", "new")],
        )

    def test_rejects_primary_key_updates(self):
        with self.assertRaises(ValueError):
            self.Keyed.objects.bulk_create(
                [self.Keyed(key=1, value=2)],
                update_conflicts=True,
                update_fields=["key"],
                unique_fields=["key"],
            )
        self.assertEqual(self.Keyed.objects.count(), 0)

    def test_rejects_missing_update_fields(self):
        with self.assertRaises(ValueError):
            self.Record.objects.bulk_create(
                [self.Record(code="x", payload="y")],
                update_conflicts=True,
                unique_fields=["code", "scope"],
            )

    def test_plain_names_still_work(self):
        owner = self.Owner.objects.create(name="before")
        self.Owner.objects.bulk_create(
            [self.Owner(id=owner.pk, name="after")],
            update_conflicts=True,
            update_fields=["name"],
            unique_fields=["id"],
        )
        self.assertEqual(self.Owner.objects.get(pk=owner.pk).name, "after")


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
    # Exceptions raised by the submitted library in these exercised operations
    # are task failures, just as wrong database rows are; harness crashes escape.
    (LOGS / "reward.txt").write_text("1\n" if result.wasSuccessful() else "0\n")
