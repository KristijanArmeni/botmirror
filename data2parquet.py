"""
Mostly copied from: https://github.com/jayqi/mirrulations-hive-partitioned-parquet
"""

import duckdb


def docket2parquet(data_dir: str, out_dir):
    """
    Parses .json mirrulations data in <data_dir> and stores output as hive partitions parquet
    in <out_dir>.
    """
    conn = duckdb.connect()

    # Calculate dynamic positions based on data_dir path
    # mirrulations structure: mirrulations/bulk/raw-data/agency_code/docket_id/comments/
    base_segments = (
        len([p for p in data_dir.split("/") if p]) + 1
    )  # 1-based indexing in split_part()
    agency_pos = (
        base_segments + 4
    )  # +1 for mirrulations, +3 for bulk/raw-data/agency_code
    docket_pos = (
        base_segments + 5
    )  # +1 for mirrulations, +4 for bulk/raw-data/agency_code/docket_id

    query = f"""\
    CREATE OR REPLACE VIEW src_comment_files AS
    SELECT
    filename,
    content,
    split_part(filename, '/', {agency_pos}) as agency_code,
    split_part(filename, '/', {docket_pos}) as docket_id,
    split_part(split_part(filename, '/', {docket_pos}), '-', 2) as year,

    FROM read_text('{data_dir}/mirrulations/bulk/raw-data/*/*/*/comments/*.json');

    CREATE OR REPLACE VIEW comments_parsed AS
    SELECT
    f.agency_code,
    f.docket_id,
    f.year,

    json_extract_string(f.content, '$.data.id') as comment_id,

    json_extract_string(f.content, '$.data.attributes.category') as category,
    json_extract_string(f.content, '$.data.attributes.comment') as comment,
    json_extract_string(f.content, '$.data.attributes.documentType') as document_type,
    json_extract_string(f.content, '$.data.attributes.modifyDate')::TIMESTAMP as modify_date,
    json_extract_string(f.content, '$.data.attributes.postedDate')::TIMESTAMP as posted_date,
    json_extract_string(f.content, '$.data.attributes.receiveDate')::TIMESTAMP as receive_date,
    json_extract_string(f.content, '$.data.attributes.subtype') as subtype,
    json_extract_string(f.content, '$.data.attributes.title') as title,
    json_extract_string(f.content, '$.data.attributes.withdrawn')::BOOLEAN as withdrawn,

    f.content AS raw_json
    FROM src_comment_files f;

    COPY (
    SELECT *
    FROM comments_parsed
    ) TO '{out_dir}/comments'
    (FORMAT PARQUET,
    PARTITION_BY (agency_code, year, docket_id),
    COMPRESSION SNAPPY);
    """

    conn.query(query)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("data_dir", type=str)
    parser.add_argument("out_dir", type=str)

    args = parser.parse_args()

    docket2parquet(data_dir=args.data_dir, out_dir=args.out_dir)
