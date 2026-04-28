"""Tests for retry/timeout behavior of the memegen client.

Uses pytest-httpserver to spin up a real local HTTP server so we can
verify retry semantics that ``responses`` cannot model (intermittent
errors, slow responses, etc.). These tests are marked
``@pytest.mark.allow_network`` to opt out of the global socket block.
"""

from __future__ import annotations

import pytest

from memeplotlib import rc_context
from memeplotlib._template import Template, TemplateNotFoundError

pytestmark = pytest.mark.allow_network


@pytest.fixture
def offline_api_base(httpserver):
    """Yield a config-bound base URL pointing at a local httpserver."""
    base = httpserver.url_for("").rstrip("/")
    with rc_context({"api_base": base, "max_retries": 3, "retry_backoff": 0.0}):
        yield base


def test_retries_on_503(httpserver, offline_api_base):
    """A 503 followed by a 200 should succeed thanks to retries."""
    # First two requests return 503, third returns valid JSON
    payload = {
        "id": "buzz",
        "name": "Buzz",
        "lines": 2,
        "blank": f"{offline_api_base}/images/buzz.png",
        "keywords": [],
        "example": {"text": []},
    }

    request_count = {"n": 0}

    def handler(request):
        request_count["n"] += 1
        from werkzeug.wrappers import Response

        if request_count["n"] < 3:
            return Response("temporarily unavailable", status=503)
        return Response(__import__("json").dumps(payload), content_type="application/json")

    httpserver.expect_request("/templates/buzz").respond_with_handler(handler)

    tmpl = Template.from_memegen("buzz")
    assert tmpl.id == "buzz"
    assert request_count["n"] == 3


def test_404_raises_template_not_found(httpserver, offline_api_base):
    httpserver.expect_request("/templates/missing").respond_with_data("not found", status=404)

    with pytest.raises(TemplateNotFoundError, match="'missing' not found"):
        Template.from_memegen("missing")


def test_timeout_respected(httpserver):
    """A short timeout should raise rather than hang."""
    import requests

    def slow_handler(request):
        import time

        from werkzeug.wrappers import Response

        time.sleep(2.0)
        return Response("too late", status=200)

    httpserver.expect_request("/templates/slow").respond_with_handler(slow_handler)

    base = httpserver.url_for("").rstrip("/")
    with (
        rc_context({"api_base": base, "api_timeout": 1, "max_retries": 0, "retry_backoff": 0.0}),
        pytest.raises((requests.Timeout, requests.ConnectionError)),
    ):
        Template.from_memegen("slow")
