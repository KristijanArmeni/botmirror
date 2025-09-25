import polars as pl
from rapidfuzz import fuzz


def find_partials_pl(self, ref: str) -> pl.Expr:
    """
    Calculate fuzzy string similarity using rapidfuzz.

    Args:
        self: The Polars expression (string column)
        ref: Reference string to compare against

    Returns:
        pl.Expr: Expression that computes similarity scores
    """

    def compute_similarity(series: pl.Series) -> pl.Series:
        # Convert to list for rapidfuzz processing
        strings = series.to_list()
        # Calculate similarity scores
        scores = [fuzz.ratio(s, ref) if s is not None else None for s in strings]
        return pl.Series(scores, dtype=pl.Float64)

    # Use map_batches to apply the function and return an expression
    return self.map_batches(compute_similarity, return_dtype=pl.Float64)


def get_embedding_similarity_pl(
    self, ref: str, model_name: str = "all-MiniLM-L6-v2"
) -> pl.Expr:
    """
    Calculate semantic similarity using sentence embeddings.

    Args:
        self: The Polars expression (string column)
        ref: Reference string to compare against
        model_name: Sentence transformer model to use (default: all-MiniLM-L6-v2)
                   - 22MB model, 384-dim embeddings
                   - Good balance of speed vs quality

    Returns:
        pl.Expr: Expression that computes similarity scores (0-100 scale)
    """

    def compute_similarity(series: pl.Series) -> pl.Series:
        # Import here to avoid loading if not used
        from sentence_transformers import SentenceTransformer, util

        # Load model (this happens each time - we'll optimize later)
        model = SentenceTransformer(model_name)

        # Convert series to list for processing
        comments: list[str] = series.to_list()

        # Embed reference text
        ref_embedding = model.encode([ref])

        # Embed all comments in one batch call
        comment_embeddings = model.encode([s for s in comments if s is not None])

        # Calculate cosine similarities using built-in utility
        # Educational: Cosine similarity measures angle between vectors
        # - 1.0 = identical meaning, 0 = orthogonal, -1 = opposite
        similarities = util.cos_sim(ref_embedding, comment_embeddings)[0]

        # Convert from [-1, 1] to [0, 100] scale to match rapidfuzz output
        # Educational: (sim + 1) * 50 converts [-1,1] -> [0,100]
        # This makes embedding similarity comparable with string similarity
        scaled_similarities = [(float(sim) + 1) * 50 for sim in similarities]

        return pl.Series(scaled_similarities, dtype=pl.Float64)

    # Use map_batches to apply function, matching existing pattern
    return self.map_batches(compute_similarity, return_dtype=pl.Float64)


# Monkey patch the method into pl.Expr
pl.Expr.find_partials_pl = find_partials_pl
pl.Expr.get_embedding_similarity_pl = get_embedding_similarity_pl


def get_duplicate_groups(df: pl.DataFrame) -> pl.DataFrame:
    """Group by content_hash and filter for duplicates."""
    return (
        df.group_by("content_hash")
        .agg(pl.len(), pl.col("comment"), pl.col("modify_date"))
        .filter(pl.col("len") > 1)
        .sort(by="len", descending=True)
    )


def create_choices_dict(df_filt: pl.DataFrame) -> dict:
    """Create choices dictionary from filtered duplicate data."""
    return {
        row["content_hash"]: row["len"]
        for row in df_filt.iter_rows(named=True)
        if row["content_hash"]
    }


def get_reference_text(df_filt: pl.DataFrame, content_hash: str) -> str:
    """Extract reference text for a given content hash."""
    return (
        df_filt.filter(pl.col("content_hash") == content_hash).select(pl.col("comment"))
    ).to_series()[0][0]


def calculate_similarities(
    df: pl.DataFrame,
    reference_text: str,
    exclude_hash: str,
    string_weight: float = 0.3,
    embedding_weight: float = 0.7,
) -> pl.DataFrame:
    """
    Calculate similarity scores against reference text using both string and embedding similarity.

    Educational notes:
    - String similarity (rapidfuzz): Good for exact matches and word overlap
    - Embedding similarity: Good for semantic meaning and context
    - Weighted combination: Balances both approaches for robust similarity

    Args:
        df: DataFrame with comments to compare
        reference_text: Text to compare against
        exclude_hash: Content hash to exclude from comparison
        string_weight: Weight for string-based similarity (0.0-1.0)
        embedding_weight: Weight for embedding-based similarity (0.0-1.0)

    Returns:
        DataFrame with comment, similarity scores, and weighted combination

    Note: Weights should sum to 1.0 for intuitive interpretation
    """
    return (
        df.filter(
            pl.col("content_hash") != exclude_hash,
            pl.col(
                "is_duplicate"
            ),  # only do similarity for those that have duplicates (i.e. templates)
        )
        .select(
            pl.col("comment"),
            pl.col("comment").find_partials_pl(ref=reference_text).alias("similarity"),
            pl.col("comment")
            .get_embedding_similarity_pl(ref=reference_text)
            .alias("embedding_similarity"),
        )
        .with_columns(
            # Create weighted similarity combination
            # Educational: Weighted average allows balancing different similarity types
            (
                pl.col("similarity") * string_weight
                + pl.col("embedding_similarity") * embedding_weight
            ).alias("similarity_w")
        )
        .sort(by="similarity_w", descending=True)
    )


def get_template_df(df_filt: pl.DataFrame, content_hash: str) -> pl.DataFrame:
    """Format selected text with dates for display."""
    return (
        df_filt.filter(pl.col("content_hash") == content_hash)
        .explode(pl.col("modify_date"), pl.col("comment"))
        .sort(by="modify_date")
        .with_columns(pl.col("modify_date").dt.strftime("%B %d, %Y at %I:%M %p UTC"))
    )
