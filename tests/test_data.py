"""Shared test fixtures and configuration for botmirror tests."""

import pytest
import polars as pl
from pathlib import Path


@pytest.fixture
def sample_comments_df():
    """Sample DataFrame with comment data for testing."""
    return pl.DataFrame(
        {
            "content_hash": ["hash1", "hash2", "hash3", "hash1", "hash2"],
            "comment": [
                "This is a test comment about regulation.",
                "Another comment with different content.",
                "Unique comment without duplicates.",
                "This is a test comment about regulation.",  # Duplicate of hash1
                "Another comment with different content.",  # Duplicate of hash2
            ],
            "is_duplicate": [True, True, False, True, True],
            "modify_date": [
                "2024-01-01T10:00:00",
                "2024-01-02T11:00:00",
                "2024-01-03T12:00:00",
                "2024-01-04T13:00:00",
                "2024-01-05T14:00:00",
            ],
        }
    ).with_columns(pl.col("modify_date").str.to_datetime())


@pytest.fixture
def sample_text_pairs():
    """Sample text pairs for diff testing."""
    return [
        ("Hello world", "Hello world"),  # Identical
        ("Hello world", "Hello there"),  # Word difference
        ("", "Hello"),  # Empty vs text
        ("Line 1\nLine 2", "Line 1\nLine 2 modified"),  # Line break + change
        ("  spaced  ", "spaced"),  # Whitespace differences
        ("Hello world", ""),  # Text vs empty
    ]


@pytest.fixture
def test_data_path():
    """Path to test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def sample_similarity_data():
    """Sample data for similarity calculations."""
    return pl.DataFrame(
        {
            "content_hash": ["hash1", "hash2", "hash3", "hash4"],
            "comment": [
                "The proposed regulation is beneficial for public health.",
                "This proposed regulation benefits public health significantly.",
                "I oppose this regulation completely.",
                "Completely different topic about environment.",
            ],
            "is_duplicate": [True, True, True, False],
            "similarity": [95.0, 90.0, 15.0, 5.0],
        }
    )


@pytest.fixture
def empty_df():
    """Empty DataFrame with expected schema."""
    return pl.DataFrame(
        {"content_hash": [], "comment": [], "is_duplicate": [], "modify_date": []},
        schema={
            "content_hash": pl.String,
            "comment": pl.String,
            "is_duplicate": pl.Boolean,
            "modify_date": pl.Datetime,
        },
    )
