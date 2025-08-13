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


# Monkey patch the method into pl.Expr
pl.Expr.find_partials_pl = find_partials_pl


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
    df: pl.DataFrame, reference_text: str, exclude_hash: str
) -> pl.DataFrame:
    """Calculate similarity scores against reference text."""
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
        )
        .sort(by="similarity", descending=True)
    )


def get_template_df(df_filt: pl.DataFrame, content_hash: str) -> pl.DataFrame:
    """Format selected text with dates for display."""
    return (
        df_filt.filter(pl.col("content_hash") == content_hash)
        .explode(pl.col("modify_date"), pl.col("comment"))
        .sort(by="modify_date")
        .with_columns(pl.col("modify_date").dt.strftime("%B %d, %Y at %I:%M %p UTC"))
    )
