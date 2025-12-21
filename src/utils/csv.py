"""CSV utility functions for thread-safe CSV operations."""

from csv import QUOTE_NONNUMERIC
from pathlib import Path
from threading import Lock
from typing import IO

import pandas as pd

# Thread-safe lock for CSV write operations
CSV_WRITE_LOCK = Lock()


def thread_safe_csv_append(
    file_path: Path | IO[str],
    data_line: list,
    quoting=QUOTE_NONNUMERIC,
) -> None:
    """Thread-safe function to append a line to a CSV file.

    Args:
        file_path: Path to the CSV file or file handle
        data_line: List of values to append as a row
        quoting: CSV quoting mode (default: QUOTE_NONNUMERIC)
        header: Whether to write header (default: False)
        index: Whether to write index (default: False)
    """
    with CSV_WRITE_LOCK:
        pd.DataFrame(data_line, dtype=str).T.to_csv(
            file_path, mode="a", quoting=quoting, header=False, index=False
        )
