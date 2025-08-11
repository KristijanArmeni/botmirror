import marimo

__generated_with = "0.14.16"
app = marimo.App(width="columns")


@app.cell(column=0)
def _():
    # from datetime import datetime
    import marimo as mo
    import polars as pl
    from data import fetch_comments_df
    from detector import (
        get_duplicate_groups,
        create_choices_dict,
        get_reference_text,
        calculate_similarity,
        format_selected_text,
    )

    return (
        fetch_comments_df,
        mo,
        pl,
        get_duplicate_groups,
        create_choices_dict,
        get_reference_text,
        calculate_similarity,
        format_selected_text,
    )


@app.cell
def _(mo):
    text_input = mo.ui.text(placeholder="Enter Docket ID")
    return (text_input,)


@app.cell
def _(text_input):
    text_input
    return


@app.cell
def _(fetch_comments_df, mo, text_input):
    with mo.status.spinner(title="Fetching comments. Be patient...") as _spinner:
        df = fetch_comments_df(docket_id=text_input.value)
    return (df,)


@app.cell
def _(df, mo):
    mo.stop(df.is_empty(), mo.md("No data in yet, type DocketID above."))
    return


@app.cell
def _(df, mo):
    mo.md(f"""**Fetched {len(df):,} comments!**""")
    return


@app.cell
def _(mo):
    mo.md(r"""## Raw Data Explorer""")
    return


@app.cell
def _(df, mo):
    mo.stop(df.is_empty(), mo.md("No data to explore yet..."))
    return


@app.cell
def _(df, pl):
    (
        df.select(
            pl.col("docket_id"),
            pl.col("agency_code"),
            pl.col("modify_date"),
            pl.col("comment"),
            pl.col("content_hash"),
        )
    )
    return


@app.cell
def _(df, get_duplicate_groups):
    df_filt = get_duplicate_groups(df)
    return (df_filt,)


@app.cell
def _(df_filt, create_choices_dict):
    choices_dict = create_choices_dict(df_filt)
    return (choices_dict,)


@app.cell
def _(choices_dict, mo):
    dropdown_dict = mo.ui.dropdown(
        options=choices_dict,
        value=list(choices_dict.keys())[0],
        label="Choose comment ID",
    )
    return (dropdown_dict,)


@app.cell
def _(mo):
    mo.md(r"""## Duplicate Posts Explorer""")
    return


@app.cell
def _(df, mo):
    mo.stop(df.is_empty(), mo.md("No posts to explore yet..."))
    return


@app.cell
def _(dropdown_dict, mo):
    mo.hstack([dropdown_dict, mo.md(f"Number of repeats: {dropdown_dict.value}")])
    return


@app.cell
def _(df_filt, dropdown_dict, format_selected_text):
    sel_text = format_selected_text(df_filt, dropdown_dict.selected_key)
    return (sel_text,)


@app.cell
def _(mo, sel_text):
    sel_rows = [
        f"DATE:{row['modify_date']}\nTEXT:{row['comment']}"
        for row in sel_text.iter_rows(named=True)
    ]
    text = "\n\n====\n\n".join(sel_rows[0:100])
    mo.ui.text_area(value=text, rows=100)
    return


@app.cell(column=1)
def _():
    # Fuzzy matching functionality is now in detector.py
    return


@app.cell
def _(df_filt, dropdown_dict, get_reference_text):
    reference_text = get_reference_text(df_filt, dropdown_dict.selected_key)
    return (reference_text,)


@app.cell
def _(df, dropdown_dict, reference_text, calculate_similarity):
    df_sim = calculate_similarity(df, reference_text, dropdown_dict.selected_key)
    return (df_sim,)


@app.cell
def _(df_sim):
    df_sim
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
