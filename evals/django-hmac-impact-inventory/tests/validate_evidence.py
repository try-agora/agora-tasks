"""Maintainer calibration: independently witness source facts in pinned Django.

TASK_WORKSPACE=.../environment/workspace python -I -B tests/validate_evidence.py
No agent output is used. This is not a model trial or a required agent strategy.
"""

# ruff: noqa: E402 -- verify the fixture before importing it; configure Django before models.

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_behavior as evidence

root = evidence.WORKSPACE
assert evidence.source_digest() == (evidence.HERE / "source.sha256").read_text().strip()
catalog = json.loads((root / "src/entrypoints.json").read_text())
evidence.validate_source_evidence(catalog)
sys.path.extend([str(root / "vendor"), str(root / "src")])

import django
from django.conf import settings

settings.configure(
    SECRET_KEY="local-fixture-not-a-production-secret",
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"],
    USE_I18N=False,
)
django.setup()

from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.backends.signed_cookies import SessionStore
from django.core import signing
from django.db import connection
from django.http import HttpRequest, HttpResponse
from django.middleware import csrf
from django.utils.crypto import constant_time_compare

with connection.schema_editor() as editor:
    editor.create_model(User)
user = User(username="fixture", email="fixture@example.invalid")
user.set_password("fixture-password")
user.save()


def request():
    value = HttpRequest()
    value.user = user
    value.session = SessionStore()
    value.session._session_cache = {}
    return value


session = request().session
session["sample"] = "value"
session.save()
encoded = session.encode({"sample": "value"})
signed = signing.dumps({"sample": "value"})
token = default_token_generator.make_token(user)
response = HttpResponse()
response.set_signed_cookie("sample", "value")
cookie_request = request()
cookie_request.COOKIES["sample"] = response.cookies["sample"].value
login_request = request()
authenticated_request = request()
authenticated_request.session.update(
    {
        auth.SESSION_KEY: str(user.pk),
        auth.BACKEND_SESSION_KEY: "django.contrib.auth.backends.ModelBackend",
        auth.HASH_SESSION_KEY: user.get_session_auth_hash(),
    }
)

cases = {
    "signing.dumps": lambda: signing.dumps({"sample": "value"}),
    "signing.loads": lambda: signing.loads(signed),
    "signing.get_cookie_signer": signing.get_cookie_signer,
    "session.encode": lambda: session.encode({"sample": "value"}),
    "session.decode": lambda: session.decode(encoded),
    "cookie_session.save": session.save,
    "cookie_session.load": session.load,
    "cookie_session.cycle_key": session.cycle_key,
    "cookie_session.create": session.create,
    "http.set_signed_cookie": lambda: response.set_signed_cookie("sample", "value"),
    "http.get_signed_cookie": lambda: cookie_request.get_signed_cookie("sample"),
    "password_reset.make_token": lambda: default_token_generator.make_token(user),
    "password_reset.check_token": lambda: default_token_generator.check_token(
        user, token
    ),
    "auth.login": lambda: auth.login(
        login_request, user, "django.contrib.auth.backends.ModelBackend"
    ),
    "auth.get_user": lambda: auth.get_user(authenticated_request),
    "auth.update_session_auth_hash": lambda: auth.update_session_auth_hash(
        authenticated_request, user
    ),
    "user.set_password": lambda: user.set_password("fixture-password"),
    "user.check_password": lambda: user.check_password("fixture-password"),
    "user.has_usable_password": user.has_usable_password,
    "csrf.get_token": lambda: csrf.get_token(request()),
    "csrf._does_token_match": lambda: csrf._does_token_match("a" * 32, "a" * 32),
    "crypto.constant_time_compare": lambda: constant_time_compare("a", "a"),
}
assert cases.keys() == catalog.keys()
all_edges = set()
for name, action in cases.items():
    observed = set()

    def profile(frame, event, arg):
        if event != "call" or frame.f_back is None:
            return
        nodes = []
        for current in (frame.f_back, frame):
            file = Path(current.f_code.co_filename)
            if not file.is_relative_to(root / "src/django"):
                return
            nodes.append(
                file.relative_to(root / "src").as_posix()
                + ":"
                + current.f_code.co_qualname
            )
        observed.add((*nodes, frame.f_back.f_lineno))

    sys.setprofile(profile)
    try:
        result = action()
    finally:
        sys.setprofile(None)
    if name in {
        "password_reset.check_token",
        "user.check_password",
        "user.has_usable_password",
        "csrf._does_token_match",
        "crypto.constant_time_compare",
    }:
        assert result is True, (name, result)
    if name == "auth.get_user":
        assert result.pk == user.pk
    expected_path, _ = evidence.shortest_path(catalog[name])
    actual_path, _ = evidence.shortest_path(catalog[name], observed)
    assert len(expected_path) == len(actual_path), (name, expected_path, actual_path)
    all_edges.update(observed)
    print(
        f"PASS {name}: reachable={bool(actual_path)}, shortest_edges={max(0, len(actual_path) - 1)}"
    )

for edge in evidence.EDGES:
    assert any(
        (a, b) == edge[:2] and line in evidence.call_range(edge)
        for a, b, line in all_edges
    ), edge
print(
    f"Validated {len(catalog)} entrypoints and {len(evidence.EDGES)} independently observed call edges."
)
