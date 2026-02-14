"""Focused tests for template resolution edge-cases."""

from __future__ import annotations

from memeplotlib._template import Template, _resolve_template


def test_resolve_template_treats_http_url_as_url_not_path():
    template = _resolve_template("https://example.com/template.png")

    assert isinstance(template, Template)
    assert template.image_url == "https://example.com/template.png"
    assert template.id == "template"


def test_resolve_template_treats_https_url_without_suffix_as_url():
    template = _resolve_template("https://example.com/templates/buzz")

    assert isinstance(template, Template)
    assert template.image_url == "https://example.com/templates/buzz"
    assert template.id == "buzz"
