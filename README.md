# Botmirror

A tool for analyzing and detecting bot-like comments in regulatory data from Mirrulations.

## Installation

```bash
uv sync
```

## Environment Setup

Create a `.env` file with:
```
MIRRULATIONS_FOLDER=/path/to/mirrulations/data
MIRRULATIONS_PARQUET_HIVE=/path/to/parquet/files
```

## Project Structure

- `data.py` - Data loading and preprocessing utilities
- `detector.py` - Fuzzy string matching for bot detection  
- `viz.py` - Rich console visualization for diffs
- `data2parquet.py` - Data format conversion utilities
- `notebook.py` - Jupyter notebook utilities