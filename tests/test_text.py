"""Tests for text encoding and wrapping utilities."""

from memeplotlib._text import apply_style, decode_text_from_url, encode_text_for_url, wrap_text


class TestEncodeTextForUrl:
    def test_spaces_to_underscores(self):
        assert encode_text_for_url("hello world") == "hello_world"

    def test_underscore_doubled(self):
        assert encode_text_for_url("hello_world") == "hello__world"

    def test_dash_doubled(self):
        assert encode_text_for_url("hello-world") == "hello--world"

    def test_question_mark(self):
        assert encode_text_for_url("what?") == "what~q"

    def test_ampersand(self):
        assert encode_text_for_url("this & that") == "this_~a_that"

    def test_percent(self):
        assert encode_text_for_url("100%") == "100~p"

    def test_hash(self):
        assert encode_text_for_url("#1") == "~h1"

    def test_slash(self):
        assert encode_text_for_url("yes/no") == "yes~sno"

    def test_backslash(self):
        assert encode_text_for_url("a\\b") == "a~bb"

    def test_angle_brackets(self):
        assert encode_text_for_url("<html>") == "~lhtml~g"

    def test_double_quotes(self):
        assert encode_text_for_url('"hi"') == "''hi''"

    def test_newline(self):
        assert encode_text_for_url("line1\nline2") == "line1~nline2"

    def test_empty_string(self):
        assert encode_text_for_url("") == ""

    def test_no_special_chars(self):
        assert encode_text_for_url("simple") == "simple"

    def test_multiple_spaces(self):
        assert encode_text_for_url("a b c") == "a_b_c"


class TestDecodeTextFromUrl:
    def test_underscores_to_spaces(self):
        assert decode_text_from_url("hello_world") == "hello world"

    def test_double_underscore(self):
        assert decode_text_from_url("hello__world") == "hello_world"

    def test_tilde_escapes(self):
        assert decode_text_from_url("what~q") == "what?"
        assert decode_text_from_url("this_~a_that") == "this & that"


class TestWrapText:
    def test_short_text_unchanged(self):
        assert wrap_text("hello", max_chars_per_line=30) == "hello"

    def test_long_text_wraps(self):
        text = "this is a much longer text that should be wrapped"
        result = wrap_text(text, max_chars_per_line=20)
        assert "\n" in result
        for line in result.split("\n"):
            assert len(line) <= 20

    def test_single_word_no_wrap(self):
        assert wrap_text("superlongword", max_chars_per_line=30) == "superlongword"


class TestApplyStyle:
    def test_upper(self):
        assert apply_style("hello world", "upper") == "HELLO WORLD"

    def test_lower(self):
        assert apply_style("HELLO WORLD", "lower") == "hello world"

    def test_none(self):
        assert apply_style("Hello World", "none") == "Hello World"

    def test_already_upper(self):
        assert apply_style("HELLO", "upper") == "HELLO"
