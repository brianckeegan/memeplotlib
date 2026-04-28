"""Tests for the RcParams-style config and rc_context."""

from __future__ import annotations

import pytest

from memeplotlib import config, rc_context
from memeplotlib._config import _DEFAULTS, MemeplotlibConfig


@pytest.fixture(autouse=True)
def _restore_config():
    """Reset config to defaults around every test in this module."""
    config.reset()
    yield
    config.reset()


class TestMappingProtocol:
    def test_getitem_returns_default(self):
        assert config["font"] == "impact"

    def test_setitem_updates_value(self):
        config["font"] = "comic"
        assert config["font"] == "comic"

    def test_setitem_unknown_key_raises_keyerror(self):
        with pytest.raises(KeyError, match="Unknown config key 'nope'"):
            config["nope"] = "x"

    def test_getitem_unknown_key_raises_keyerror(self):
        # Force an unknown key by bypassing __setitem__ (still rejected on get)
        with pytest.raises(KeyError, match="Unknown config key 'nope'"):
            config["nope"]

    def test_delitem_resets_to_default(self):
        config["font"] = "comic"
        del config["font"]
        assert config["font"] == _DEFAULTS["font"]

    def test_delitem_unknown_key_raises(self):
        with pytest.raises(KeyError, match="Unknown config key 'bogus'"):
            del config["bogus"]

    def test_iter_yields_all_keys(self):
        keys = set(iter(config))
        assert keys == set(_DEFAULTS)

    def test_len_matches_defaults(self):
        assert len(config) == len(_DEFAULTS)

    def test_repr_shows_keys(self):
        r = repr(config)
        assert "MemeplotlibConfig" in r
        assert "'font'" in r

    def test_update_uses_validators(self):
        config.update({"font": "comic", "color": "yellow"})
        assert config["font"] == "comic"
        assert config["color"] == "yellow"

    def test_update_rejects_invalid_value(self):
        with pytest.raises(ValueError, match="'dpi' must be"):
            config.update({"dpi": "not-an-int"})


class TestValidators:
    def test_str_validator_rejects_int(self):
        with pytest.raises(ValueError, match="'font' must be a string"):
            config["font"] = 42

    def test_optional_str_accepts_none(self):
        config["cache_dir"] = None
        assert config["cache_dir"] is None

    def test_optional_str_rejects_int(self):
        with pytest.raises(ValueError, match="'cache_dir' must be a string or None"):
            config["cache_dir"] = 42

    def test_non_negative_float_accepts_int(self):
        config["fontsize"] = 100  # int coerced to float
        assert config["fontsize"] == 100.0
        assert isinstance(config["fontsize"], float)

    def test_non_negative_float_rejects_negative(self):
        with pytest.raises(ValueError, match="'fontsize' must be non-negative"):
            config["fontsize"] = -1.0

    def test_non_negative_float_rejects_string(self):
        with pytest.raises(ValueError, match="'fontsize' must be a number"):
            config["fontsize"] = "huge"

    def test_non_negative_float_rejects_bool(self):
        with pytest.raises(ValueError, match="'fontsize' must be a number"):
            config["fontsize"] = True

    def test_non_negative_int_rejects_float(self):
        with pytest.raises(ValueError, match="'dpi' must be an int"):
            config["dpi"] = 150.5

    def test_non_negative_int_rejects_negative(self):
        with pytest.raises(ValueError, match="'dpi' must be non-negative"):
            config["dpi"] = -1

    def test_non_negative_int_rejects_bool(self):
        with pytest.raises(ValueError, match="'dpi' must be an int"):
            config["dpi"] = True

    def test_style_accepts_valid(self):
        config["style"] = "lower"
        assert config["style"] == "lower"

    def test_style_rejects_invalid(self):
        with pytest.raises(ValueError, match="'style' must be one of"):
            config["style"] = "diagonal"

    def test_bool_rejects_int(self):
        with pytest.raises(ValueError, match="'cache_enabled' must be a bool"):
            config["cache_enabled"] = 1


class TestReset:
    def test_reset_restores_all_defaults(self):
        config["font"] = "comic"
        config["color"] = "yellow"
        config["dpi"] = 300
        config.reset()
        assert config["font"] == _DEFAULTS["font"]
        assert config["color"] == _DEFAULTS["color"]
        assert config["dpi"] == _DEFAULTS["dpi"]


class TestRcContext:
    def test_overrides_inside_block(self):
        original = config["font"]
        with rc_context({"font": "comic"}):
            assert config["font"] == "comic"
        assert config["font"] == original

    def test_restores_on_exception(self):
        original = config["font"]
        with pytest.raises(RuntimeError, match="boom"), rc_context({"font": "comic"}):
            raise RuntimeError("boom")
        assert config["font"] == original

    def test_nested_contexts(self):
        config["font"] = "impact"
        with rc_context({"font": "comic"}):
            assert config["font"] == "comic"
            with rc_context({"font": "arial"}):
                assert config["font"] == "arial"
            assert config["font"] == "comic"
        assert config["font"] == "impact"

    def test_none_argument_still_snapshots(self):
        config["font"] = "impact"
        with rc_context() as cfg:
            cfg["font"] = "courier"
        # Mutation inside the block is rolled back
        assert config["font"] == "impact"

    def test_validates_keys_in_rc(self):
        with (
            pytest.raises(KeyError, match="Unknown config key 'nope'"),
            rc_context({"nope": "x"}),
        ):
            pass

    def test_yields_singleton(self):
        with rc_context({"font": "comic"}) as cfg:
            assert cfg is config


class TestSingletonClass:
    def test_valid_keys_is_frozenset(self):
        assert isinstance(MemeplotlibConfig.VALID_KEYS, frozenset)
        assert "font" in MemeplotlibConfig.VALID_KEYS

    def test_construction_independent_instances(self):
        # Independent instances are valid even if not commonly used.
        cfg2 = MemeplotlibConfig()
        cfg2["font"] = "comic"
        assert cfg2["font"] == "comic"
        assert config["font"] == _DEFAULTS["font"]
