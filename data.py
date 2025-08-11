from pathlib import Path
from rich.console import Console
import json
import polars as pl
from glob import glob
import hashlib
from dotenv import dotenv_values

MIRRULATIONS_FOLDER = dotenv_values()["MIRRULATIONS_FOLDER"]
MIRRULATIONS_PARQUET = dotenv_values()["MIRRULATIONS_PARQUET_HIVE"]

console = Console()


def load_data_json_attributes(json_fname: str) -> dict:
    """Load json and grab 'attributes' field"""
    with open(json_fname) as fh:
        d = json.load(fh)["data"]["attributes"]

    return d


def load_mirrulations_parquet(docket_id: str) -> pl.DataFrame:
    """Load hive-partition parquet from MIRRULATIONS_FOLDER"""
    lf = (
        pl.scan_parquet(source=MIRRULATIONS_PARQUET, hive_partitioning=True)
        .filter(pl.col("docket_id") == docket_id)
        .drop(pl.col("raw_json"))
    )

    return lf.collect()


def fetch_comments_df(docket_id: str, is_parquet=True):
    """Load comments json and populate a polars data frame"""

    # loads json
    if not is_parquet:
        comment_path = f"specific/{docket_id}/raw-data/comments"
        full_path = Path(MIRRULATIONS_FOLDER, comment_path)

        # list all .json files in docket folder
        all_json = glob(str(Path(full_path, "*.json")))

        data_json = []
        skipped_count = 0
        for jsonf in all_json:
            try:
                data = load_data_json_attributes(jsonf)
                data_json.append(data)
            except (KeyError, json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Skipping {jsonf}: {e}")
                skipped_count += 1
                continue

        total_files = len(all_json)
        processed_files = len(data_json)

        console.print(f"Processed {processed_files}/{total_files} comments. Skipped 0!")
        if skipped_count > 0:
            console.print(f"Skipped {skipped_count} comments due to errors")

        if not data_json:
            console.print("No valid JSON files found")
            return pl.DataFrame()

        try:
            df = pl.DataFrame(data_json, infer_schema_length=None)
            # Drop columns that are entirely null
            cols_to_keep = [col for col in df.columns if not df[col].is_null().all()]

        except pl.ComputeError as e:
            print(f"Schema error: {e}")
            print("Attempting to normalize data types...")

            # Normalize all values to strings to handle mixed types
            normalized_data = []
            for record in data_json:
                normalized_record = {
                    k: str(v) if v is not None else None for k, v in record.items()
                }
                normalized_data.append(normalized_record)

            df = pl.DataFrame(normalized_data)

    # parquet files
    df = load_mirrulations_parquet(docket_id=docket_id)

    # Drop columns that are entirely null
    cols_to_keep = [col for col in df.columns if not df[col].is_null().all()]
    df = df.select(cols_to_keep)

    TIME_COLUMNS = ["modifyDate", "receiveDate", "postedDate"]

    # Cast time columns to datetime if they exist in the dataframe
    existing_time_cols = [col for col in TIME_COLUMNS if col in df.columns]

    for col in existing_time_cols:
        df = df.with_columns(pl.col(col).str.to_datetime(format=None, strict=False))

    # Check if comment column exists before processing duplicates
    # Find duplicate comments
    df = df.with_columns(pl.col("comment").is_duplicated().alias("is_duplicate"))

    # Create SHA256 hash of comments for unique identifier
    df = df.with_columns(
        pl.col("comment")
        .map_elements(
            lambda x: hashlib.sha256(str(x).encode()).hexdigest()
            if x is not None
            else None,
            return_dtype=pl.String,
        )
        .alias("content_hash")
    )

    return df
