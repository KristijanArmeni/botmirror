<div align="center">

# Botmirror

**A tool for analyzing comment similarity and detecting bot-like patterns in regulatory data from Mirrulations**

<a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white"></a>
<a href="https://pola.rs/"><img alt="Polars" src="https://img.shields.io/badge/Polars-1.32+-orange?logo=polars&logoColor=white"></a>
<a href="https://plotly.com/"><img alt="Plotly" src="https://img.shields.io/badge/Plotly-6.2+-blue?logo=plotly&logoColor=white"></a>
<a href="https://shiny.posit.co/py/"><img alt="Shiny" src="https://img.shields.io/badge/Shiny-1.4+-green?logo=python&logoColor=white"></a>
<a href="https://rapidfuzz.github.io/RapidFuzz/"><img alt="RapidFuzz" src="https://img.shields.io/badge/RapidFuzz-3.13+-red?logo=python&logoColor=white"></a>
<a href="https://duckdb.org/"><img alt="DuckDB" src="https://img.shields.io/badge/DuckDB-1.3+-yellow?logo=duckdb&logoColor=white"></a>

</div>

## Features

- Interactive web interface for comment similarity analysis
- Side-by-side diff visualization with semantic highlighting
- Duplicate detection and template comment grouping
- Scalable processing of large regulatory comment datasets

## Installation

```bash
uv sync
```

## Usage

Run the Shiny web application:
```bash
shiny run app.py
```

Then open your browser to `http://localhost:8000` to access the interactive interface.

## Environment Setup

Create a `.env` file with:
```
MIRRULATIONS_FOLDER=/path/to/mirrulations/data
MIRRULATIONS_PARQUET_HIVE=/path/to/parquet/files
```

## Project Structure

- `app.py` - Main Shiny web application with interactive interface
- `data.py` - Data loading and preprocessing utilities
- `botmirror.py` - Fuzzy string matching and similarity calculations
- `viz.py` - Rich console visualization for diffs
- `data2parquet.py` - Data format conversion utilities
- `notebook.py` - Jupyter notebook utilities