"""Database outcomes, not patch similarity or navigation-tool use, determine reward."""

import json
import os
from pathlib import Path
import sys
import unittest

WORKSPACE = Path(os.environ.get("TASK_WORKSPACE", "/app")).resolve()
LOGS = Path(os.environ.get("VERIFIER_LOGS", "/logs/verifier")).resolve()
sys.path[:0] = [str(WORKSPACE / "src"), str(WORKSPACE / "vendor")]


class Behavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import django
        from django.conf import settings

        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            INSTALLED_APPS=[],
            USE_I18N=False,
            SECRET_KEY="isolated-verifier",
        )
        django.setup()
        from django.db import connection, models

        class Primary(models.Model):
            primary_id = models.AutoField(primary_key=True)
            quantity = models.IntegerField(default=0)

            class Meta:
                app_label = "checks"

        class Secondary(models.Model):
            secondary_id = models.AutoField(primary_key=True)
            score = models.IntegerField(default=0)

            class Meta:
                app_label = "checks"

        class Record(Primary, Secondary):
            label = models.CharField(max_length=30, default="")

            class Meta:
                app_label = "checks"

        class Descendant(Record):
            depth = models.IntegerField(default=0)

            class Meta:
                app_label = "checks"

        class SingleChild(Primary):
            label = models.CharField(max_length=30, default="")

            class Meta:
                app_label = "checks"

        class SecondaryBranch(Secondary):
            branch = models.IntegerField(default=0)

            class Meta:
                app_label = "checks"

        class DeepRecord(Primary, SecondaryBranch):
            label = models.CharField(max_length=30, default="")

            class Meta:
                app_label = "checks"

        class OwnKeyRecord(Primary, Secondary):
            own_id = models.AutoField(primary_key=True)

            class Meta:
                app_label = "checks"

        class StringParent(models.Model):
            code = models.CharField(max_length=30, primary_key=True)
            title = models.CharField(max_length=30, default="")

            class Meta:
                app_label = "checks"

        class StringRecord(Primary, StringParent):
            class Meta:
                app_label = "checks"

        cls.connection = connection
        cls.tables = (
            Primary, Secondary, Record, Descendant, SingleChild,
            SecondaryBranch, DeepRecord, OwnKeyRecord, StringParent, StringRecord,
        )
        for model in cls.tables:
            setattr(cls, model.__name__, model)

    def setUp(self):
        with self.connection.schema_editor() as editor:
            for model in self.tables:
                editor.create_model(model)

    def tearDown(self):
        with self.connection.schema_editor() as editor:
            for model in reversed(self.tables):
                editor.delete_model(model)

    def records(self, model=None):
        model = model or self.Record
        # Independent key spaces: confusing a child's PK with another parent's
        # PK corrupts a real, unrelated row instead of silently matching nothing.
        self.Secondary.objects.create(secondary_id=11, score=900)
        self.Secondary.objects.create(secondary_id=23, score=901)
        first = model.objects.create(primary_id=11, secondary_id=71, quantity=2, score=10)
        second = model.objects.create(primary_id=23, secondary_id=93, quantity=5, score=20)
        return first, second

    def assert_unrelated(self):
        self.assertEqual(
            list(self.Secondary.objects.filter(pk__in=[11, 23]).order_by("pk").values_list("score", flat=True)),
            [900, 901],
        )

    def test_update_secondary_parent_and_count(self):
        first, second = self.records()
        self.assertEqual(self.Record.objects.update(score=42), 2)
        for item in (first, second):
            item.refresh_from_db()
            self.assertEqual((item.quantity, item.score), (2 if item.pk == first.pk else 5, 42))
        self.assert_unrelated()

    def test_filter_keeps_unselected_and_unrelated_rows(self):
        first, second = self.records()
        self.assertEqual(self.Record.objects.filter(quantity=2).update(score=44), 1)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.score, second.score), (44, 20))
        self.assert_unrelated()

    def test_inherited_filter_membership_survives_updates(self):
        first, second = self.records()
        self.assertEqual(
            self.Record.objects.filter(quantity=2, score=10).update(quantity=8, score=88, label="done"),
            1,
        )
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.quantity, first.score, first.label), (8, 88, "done"))
        self.assertEqual((second.quantity, second.score, second.label), (5, 20, ""))
        self.assert_unrelated()

    def test_expression_updates_both_parents(self):
        from django.db.models import F

        first, second = self.records()
        self.assertEqual(self.Record.objects.update(quantity=F("quantity") + 3, score=F("score") * 2), 2)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.quantity, first.score), (5, 20))
        self.assertEqual((second.quantity, second.score), (8, 40))
        self.assert_unrelated()

    def test_descendant_updates_grandparent(self):
        first, second = self.records(self.Descendant)
        self.assertEqual(self.Descendant.objects.filter(pk=first.pk).update(score=61, depth=3), 1)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.score, first.depth, second.score), (61, 3, 20))
        self.assert_unrelated()

    def test_non_primary_branch_updates_ancestor(self):
        first, second = self.records(self.DeepRecord)
        self.assertEqual(self.DeepRecord.objects.filter(pk=first.pk).update(score=62, branch=4), 1)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.score, first.branch, second.score), (62, 4, 20))
        self.assert_unrelated()

    def test_child_with_independent_primary_key(self):
        self.Primary.objects.create(primary_id=99, quantity=900)
        self.Secondary.objects.create(secondary_id=99, score=901)
        item = self.OwnKeyRecord.objects.create(own_id=99, primary_id=31, secondary_id=73, quantity=2, score=3)
        self.assertEqual(self.OwnKeyRecord.objects.update(quantity=17, score=19), 1)
        item.refresh_from_db()
        self.assertEqual((item.quantity, item.score), (17, 19))
        self.assertEqual(self.Primary.objects.get(pk=99).quantity, 900)
        self.assertEqual(self.Secondary.objects.get(pk=99).score, 901)

    def test_parent_keys_need_not_be_integers(self):
        unrelated = self.StringParent.objects.create(code="12", title="unchanged")
        item = self.StringRecord.objects.create(primary_id=12, code="customer-A", title="old")
        self.assertEqual(self.StringRecord.objects.update(title="new"), 1)
        item.refresh_from_db()
        unrelated.refresh_from_db()
        self.assertEqual((item.title, unrelated.title), ("new", "unchanged"))

    def test_empty_and_no_match_querysets(self):
        first, second = self.records()
        self.assertEqual(self.Record.objects.none().update(score=8), 0)
        self.assertEqual(self.Record.objects.filter(score=-1).update(quantity=9, score=8), 0)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.score, second.score), (10, 20))
        self.assert_unrelated()

    def test_primary_parent_only(self):
        first, second = self.records()
        self.assertEqual(self.Record.objects.update(quantity=12), 2)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.quantity, second.quantity), (12, 12))
        self.assertEqual((first.score, second.score), (10, 20))
        self.assert_unrelated()

    def test_child_table_only(self):
        first, second = self.records()
        self.assertEqual(self.Record.objects.filter(score=10).update(label="chosen"), 1)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.label, second.label), ("chosen", ""))
        self.assertEqual((first.score, second.score), (10, 20))

    def test_single_parent_regression(self):
        item = self.SingleChild.objects.create(quantity=4, label="old")
        self.assertEqual(self.SingleChild.objects.update(quantity=9, label="new"), 1)
        item.refresh_from_db()
        self.assertEqual((item.quantity, item.label), (9, "new"))

    def test_single_table_regression(self):
        from django.db.models import F

        first = self.Primary.objects.create(quantity=4)
        second = self.Primary.objects.create(quantity=8)
        self.assertEqual(self.Primary.objects.filter(quantity=4).update(quantity=F("quantity") + 2), 1)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.quantity, second.quantity), (6, 8))

    def test_transaction_rollback_preserves_all_tables(self):
        from django.db import transaction

        first, second = self.records()
        with self.assertRaisesRegex(ValueError, "rollback"):
            with transaction.atomic():
                self.Record.objects.update(quantity=99, score=98, label="temporary")
                raise ValueError("rollback")
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((first.quantity, first.score, first.label), (2, 10, ""))
        self.assertEqual((second.quantity, second.score, second.label), (5, 20, ""))
        self.assert_unrelated()

    def test_bulk_statement_count_does_not_grow_per_object(self):
        from django.test.utils import CaptureQueriesContext

        for number in range(25):
            self.Record.objects.create(primary_id=number + 1, secondary_id=number + 101, score=number)
        with CaptureQueriesContext(self.connection) as captured:
            count = self.Record.objects.update(score=81)
        self.assertEqual(count, 25)
        self.assertEqual(list(self.Record.objects.values_list("score", flat=True)), [81] * 25)
        # One preselection plus a bulk UPDATE is enough; the slack permits
        # different valid set-based implementations and transaction statements.
        self.assertLessEqual(len(captured), 6, "bulk update became a per-object loop")


if __name__ == "__main__":
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / "reward.txt").unlink(missing_ok=True)
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Behavior)
    )
    if result.testsRun == 0 and not result.errors:
        raise RuntimeError("no behavioral checks executed")
    evidence = {
        "tests_run": result.testsRun,
        "failures": [{"test": str(test), "traceback": trace} for test, trace in result.failures],
        "errors": [{"test": str(test), "traceback": trace} for test, trace in result.errors],
        "passed": result.wasSuccessful(),
    }
    (LOGS / "checks.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (LOGS / "reward.txt").write_text("1\n" if result.wasSuccessful() else "0\n")
