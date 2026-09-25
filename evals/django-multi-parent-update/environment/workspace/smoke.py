"""One public reproduction; not used by the hidden verifier."""

from pathlib import Path
import sys

root = Path(__file__).resolve().parent
sys.path[:0] = [str(root / "src"), str(root / "vendor")]

import django
from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
    USE_I18N=False,
    SECRET_KEY="local-reproduction",
)
django.setup()

from django.db import connection, models


class Account(models.Model):
    account_id = models.AutoField(primary_key=True)
    balance = models.IntegerField(default=0)

    class Meta:
        app_label = "repro"


class Profile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    rating = models.IntegerField(default=0)

    class Meta:
        app_label = "repro"


class Customer(Account, Profile):
    class Meta:
        app_label = "repro"


with connection.schema_editor() as editor:
    for model in (Account, Profile, Customer):
        editor.create_model(model)

unrelated = Profile.objects.create(profile_id=11, rating=900)
customer = Customer.objects.create(account_id=11, profile_id=73, rating=10)
matched = Customer.objects.update(rating=42)
customer.refresh_from_db()
unrelated.refresh_from_db()
assert matched == 1, matched
assert customer.rating == 42, f"Target customer still has rating {customer.rating}"
assert unrelated.rating == 900, f"Unrelated profile changed to {unrelated.rating}"
print("PASS: intended parent updated; unrelated parent preserved")
