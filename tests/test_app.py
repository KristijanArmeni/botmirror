"""Tests for app.py functions."""

import pytest
from app import create_word_diff_html, _placeholder_fig

# Color constants used in diff highlighting
MATCHING_COLOR = "#d4edda"  # Green background for matching text
DELETED_COLOR = "#f8d7da"  # Red background for deleted text (reference only)
INSERTED_COLOR = "#d1ecf1"  # Blue background for inserted text (compared only)


class TestCreateWordDiffHtml:
    """Tests for the create_word_diff_html function."""

    def test_identical_texts(self):
        """Test diff of identical texts."""
        text1 = "Hello world test"
        text2 = "Hello world test"

        html1, html2 = create_word_diff_html(text1, text2)

        # Both should be highlighted as matching (green)
        assert MATCHING_COLOR in html1  # Green background for matching
        assert MATCHING_COLOR in html2
        assert "Hello" in html1
        assert "world" in html1
        assert "test" in html1

    def test_completely_different_texts(self):
        """Test diff of completely different texts."""
        text1 = "Hello world"
        text2 = "Goodbye earth"

        html1, html2 = create_word_diff_html(text1, text2)

        # Text1 words should be red (deleted)
        assert DELETED_COLOR in html1  # Red background
        assert "Hello" in html1
        assert "world" in html1

        # Text2 words should be blue (inserted)
        assert INSERTED_COLOR in html2  # Blue background
        assert "Goodbye" in html2
        assert "earth" in html2

    def test_partial_word_changes(self):
        """Test diff with some matching and some different words."""
        text1 = "I support this regulation"
        text2 = "I oppose this regulation"

        html1, html2 = create_word_diff_html(text1, text2)

        # Should have both matching (green) and different colors
        assert MATCHING_COLOR in html1  # Green for matching words
        assert DELETED_COLOR in html1  # Red for 'support'
        assert MATCHING_COLOR in html2  # Green for matching words
        assert INSERTED_COLOR in html2  # Blue for 'oppose'

        # Check specific words
        assert "support" in html1
        assert "oppose" in html2

    def test_empty_texts(self):
        """Test diff with empty texts."""
        # Empty first text
        html1, html2 = create_word_diff_html("", "Hello")
        assert html1 == "Hello"  # Returns second text as-is
        assert html2 == "Hello"

        # Empty second text
        html1, html2 = create_word_diff_html("Hello", "")
        assert html1 == "Hello"  # Returns first text as-is
        assert html2 == "Hello"

        # Both empty
        html1, html2 = create_word_diff_html("", "")
        assert html1 == ""
        assert html2 == ""

    def test_none_inputs(self):
        """Test diff with None inputs."""
        html1, html2 = create_word_diff_html(None, "Hello")
        assert html2 == "Hello"

        html1, html2 = create_word_diff_html("Hello", None)
        assert html1 == "Hello"

    def test_whitespace_differences(self):
        """Test diff handling of whitespace changes."""
        text1 = "Hello world"
        text2 = "Hello  world"  # Extra space

        html1, html2 = create_word_diff_html(text1, text2)

        # Should highlight the whitespace difference
        assert "Hello" in html1
        assert "world" in html1
        assert "Hello" in html2
        assert "world" in html2

    def test_line_break_handling(self):
        """Test diff with line breaks."""
        text1 = "Line 1\nLine 2"
        text2 = "Line 1\nLine 2 modified"

        html1, html2 = create_word_diff_html(text1, text2)

        # Should preserve line breaks
        assert "\n" in html1 or "↵" in html1
        assert "\n" in html2 or "↵" in html2
        assert "Line" in html1
        assert "modified" in html2

    def test_special_characters(self):
        """Test diff with special characters."""
        text1 = "Hello & goodbye"
        text2 = "Hello & farewell"

        html1, html2 = create_word_diff_html(text1, text2)

        # Should handle special characters properly
        assert "&" in html1
        assert "&" in html2
        assert "goodbye" in html1
        assert "farewell" in html2

    @pytest.mark.parametrize(
        "text1,text2",
        [
            ("Hello world", "Hello world"),
            ("", "test"),
            ("test", ""),
            ("Line1\nLine2", "Line1\nDifferent"),
            ("  spaced  ", "spaced"),
        ],
    )
    def test_diff_parametrized(self, text1, text2):
        """Parametrized test for various text combinations."""
        html1, html2 = create_word_diff_html(text1, text2)

        # Basic sanity checks
        assert isinstance(html1, str)
        assert isinstance(html2, str)
        # Should produce some HTML spans if texts are not empty
        if text1 and text2 and text1 != text2:
            assert "<span" in html1 or "<span" in html2

    def test_html_safety(self):
        """Test that HTML characters are handled safely."""
        text1 = "Hello <script>alert('xss')</script>"
        text2 = "Hello <div>safe</div>"

        html1, html2 = create_word_diff_html(text1, text2)

        # Should contain the literal text (not executed as HTML)
        assert "script" in html1
        assert "div" in html2


class TestPlaceholderFig:
    """Tests for the _placeholder_fig function."""

    def test_placeholder_fig_creation(self):
        """Test basic placeholder figure creation."""
        fig = _placeholder_fig("Test message")

        # Should return a plotly figure
        assert hasattr(fig, "data")
        assert hasattr(fig, "layout")

    def test_placeholder_fig_with_annotation(self):
        """Test placeholder figure with annotation text."""
        annotation_text = "No data available"
        fig = _placeholder_fig(annotation_text)

        # Check annotation was added
        assert len(fig.layout.annotations) > 0
        assert fig.layout.annotations[0].text == annotation_text

    def test_placeholder_fig_empty_annotation(self):
        """Test placeholder figure with empty annotation."""
        fig = _placeholder_fig("")

        # Should still create a figure
        assert hasattr(fig, "data")
        assert hasattr(fig, "layout")

    def test_placeholder_fig_styling(self):
        """Test placeholder figure has correct styling."""
        fig = _placeholder_fig("Test")

        # Check axis ranges
        assert fig.layout.xaxis.range == (0, 1)
        assert fig.layout.yaxis.range == (0, 1)

        # Check that template is set (plotly_white template should have white background)
        assert hasattr(fig.layout, "template")
