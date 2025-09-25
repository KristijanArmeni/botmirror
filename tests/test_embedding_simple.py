#!/usr/bin/env python3
"""
Simple test script to verify embedding similarity works before full integration.
Run this after: uv sync (to install sentence-transformers)
"""

import polars as pl
from botmirror import get_embedding_similarity_pl  # noqa: F401 - needed for monkey patching


def test_embedding_similarity():
    """Test embedding similarity with some example comments."""
    print("Testing embedding similarity...")

    # Create test data
    test_comments = [
        "I support this regulation because it protects public health.",
        "This regulation is beneficial for public health and safety.",
        "I oppose this regulation because it destroys public health.",
        "The weather is nice today.",
        "Cats are better than dogs.",
    ]

    reference_text = "I support this regulation for health protection."

    # Create DataFrame
    df = pl.DataFrame({"comment": test_comments})

    print(f"Reference: {reference_text}")
    print("\nTest comments:")
    for i, comment in enumerate(test_comments):
        print(f"{i + 1}. {comment}")

    # Test embedding similarity
    print(f"\n{'=' * 50}")
    print("EMBEDDING SIMILARITY RESULTS:")
    print(f"{'=' * 50}")

    result_df = df.select(
        pl.col("comment"),
        pl.col("comment")
        .get_embedding_similarity_pl(ref=reference_text)
        .alias("embedding_similarity"),
    ).sort(by="embedding_similarity", descending=True)

    print(result_df)

    # Verify results make sense
    similarities = result_df["embedding_similarity"].to_list()
    print(f"\nSimilarity scores: {[f'{s:.4f}' for s in similarities]}")

    # The first two should be most similar (both about supporting regulation)
    # The opposition comment should be lower
    # Weather and cats should be lowest
    SUPPORTIVE1 = 0
    SUPPORTIVE2 = 1
    OPPOSED = 2
    UNRELATED1 = 3
    UNRELATED2 = 4
    assert similarities[SUPPORTIVE1] > similarities[OPPOSED]
    assert similarities[SUPPORTIVE2] > similarities[OPPOSED]

    assert similarities[SUPPORTIVE1] > similarities[UNRELATED1]
    assert similarities[SUPPORTIVE2] > similarities[UNRELATED1]

    assert similarities[SUPPORTIVE1] > similarities[UNRELATED2]
    assert similarities[SUPPORTIVE2] > similarities[UNRELATED2]

    assert similarities[OPPOSED] > similarities[UNRELATED2]
    assert similarities[OPPOSED] > similarities[UNRELATED2]

    print("\n✅ Embedding similarity test completed successfully!")
