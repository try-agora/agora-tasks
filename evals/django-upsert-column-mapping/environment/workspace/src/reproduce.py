"""Public minimal reproduction; the hidden verifier uses different models."""

import django
from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
    USE_I18N=False,
    SECRET_KEY="public-reproduction",
)
django.setup()
from django.db import connection, models  # noqa: E402 -- configure Django first.


class Shipment(models.Model):
    tracking = models.CharField(max_length=40, unique=True, db_column="Tracking Code")
    status = models.CharField(max_length=30, db_column="Delivery Status")

    class Meta:
        app_label = "reproduction"


with connection.schema_editor() as editor:
    editor.create_model(Shipment)
Shipment.objects.create(tracking="P-1", status="queued")
Shipment.objects.bulk_create(
    [
        Shipment(tracking="P-1", status="sent"),
        Shipment(tracking="P-2", status="queued"),
    ],
    update_conflicts=True,
    update_fields=["status"],
    unique_fields=["tracking"],
)
assert list(
    Shipment.objects.order_by("tracking").values_list("tracking", "status")
) == [
    ("P-1", "sent"),
    ("P-2", "queued"),
]
print("Mixed insert/update preserved physical column mappings.")
