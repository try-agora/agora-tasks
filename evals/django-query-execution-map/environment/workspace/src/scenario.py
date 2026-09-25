"""Read-only ORM execution audit scenario. No external services."""

import django
from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[],
    DEBUG=False,
    USE_I18N=False,
    SECRET_KEY="local-navigation-scenario",
)
django.setup()

from django.db import connection, models  # noqa: E402


class Entry(models.Model):
    label = models.CharField(max_length=40)
    active = models.BooleanField(default=True)

    class Meta:
        app_label = "navigation"


def run_cases(observe):
    """observe(name, action, queryset) executes each action exactly once."""
    with connection.schema_editor() as editor:
        editor.create_model(Entry)
    try:
        Entry.objects.bulk_create(
            [
                Entry(label="first"),
                Entry(label="second"),
                Entry(label="hidden", active=False),
            ]
        )
        queryset = Entry.objects.filter(active=True).order_by("id")
        observe("model_first", lambda: list(queryset), queryset)
        observe("model_cached", lambda: list(queryset), queryset)
        flat = (
            Entry.objects.filter(active=True)
            .order_by("id")
            .values_list("label", flat=True)
        )
        observe("flat_first", lambda: list(flat), flat)
        fresh = Entry.objects.filter(active=True)
        observe("exists_first", fresh.exists, fresh)
    finally:
        with connection.schema_editor() as editor:
            editor.delete_model(Entry)


if __name__ == "__main__":
    run_cases(lambda name, action, queryset: print(name, action()))
