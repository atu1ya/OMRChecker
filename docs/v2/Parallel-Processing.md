# Parallel Processing Implementation

## Overview

OMRChecker now supports parallel processing of images using multi-threading. Images within each folder are processed concurrently, significantly improving processing speed for large batches.

## Key Features

### 1. **Thread-Based Parallelization**
- Uses Python's `ThreadPoolExecutor` for concurrent image processing
- Parallelization occurs **per folder**, not globally
- Each folder's images are processed independently

### 2. **Thread-Safe Operations & Result Ordering**
- **CSV Writing**: Results are collected and sorted by input order before writing to CSV
- **Ordered Output**: CSV rows maintain the same order as input files, regardless of processing completion order
- **Stats Tracking**: Protected counters for accurate file statistics
- **Logging**: Synchronized logging to prevent garbled output

### 3. **Configurable Worker Threads**
- Default: 4 worker threads
- Configurable via `config.json`: `outputs.max_parallel_workers`
- Range: 1-16 workers
- Set to 1 for sequential (original) behavior

### 4. **Automatic Mode Detection**
- **Interactive Mode**: When `show_image_level > 0`, automatically switches to sequential processing (max_workers=1)
- **Batch Mode**: When `show_image_level = 0`, uses configured parallel workers

## Configuration

Add to your `config.json`:

```json
{
  "outputs": {
    "max_parallel_workers": 4,
    ...other configs...
  }
}
```

**Options:**
- `1`: Sequential processing (original behavior)
- `2-4`: Light parallelization (good for I/O bound operations)
- `4-8`: Moderate parallelization (recommended for most systems)
- `8-16`: Heavy parallelization (for powerful multi-core systems)

## Architecture Changes

### Modified Files

1. **`src/entry.py`**
   - Added imports: `ThreadPoolExecutor`, `as_completed`, `Lock`
   - Added thread-safe locks: `CSV_WRITE_LOCK`, `STATS_LOCK`, `LOGGER_LOCK`
   - New function: `process_single_file()` - Extracted single file processing logic
   - Modified function: `process_directory_files()` - Now uses ThreadPoolExecutor

2. **`src/schemas/defaults/config.py`**
   - Added default: `"max_parallel_workers": 4`

3. **`src/schemas/config_schema.py`**
   - Added schema validation for `max_parallel_workers`

### Function Refactoring

#### Before:
```python
def process_directory_files(...):
    for file_path in omr_files:
        # Process file
        ...
```

#### After:
```python
def process_single_file(file_info):
    """Process a single OMR file and return results with CSV data"""
    result = {
        "file_counter": idx,
        "csv_writes": []  # Store CSV writes for later
    }
    # Process file...
    # Store CSV data instead of writing immediately
    result["csv_writes"].append({"file": csv_file, "data": row_data})
    return result

def process_directory_files(...):
    """Process files in parallel using ThreadPoolExecutor"""
    max_workers = config.processing.max_parallel_workers

    # Prepare file tasks
    file_tasks = [(file_path, idx, ...) for ...]

    # Process in parallel
    if max_workers > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_single_file, task): task
                       for task in file_tasks}

            # Collect results as they complete
            results = []
            for future in as_completed(futures):
                results.append(future.result())

            # Sort by file_counter to maintain input order
            results.sort(key=lambda r: r["file_counter"])

            # Write CSV in correct order
            for result in results:
                for csv_write in result["csv_writes"]:
                    thread_safe_csv_append(csv_write["file"], csv_write["data"])
    else:
        # Sequential processing
        for task in file_tasks:
            result = process_single_file(task)
            # Write immediately in sequential mode
            for csv_write in result["csv_writes"]:
                thread_safe_csv_append(csv_write["file"], csv_write["data"])
```

## Thread Safety & Result Ordering

### Result Collection & Ordering
When using parallel processing, files complete in non-deterministic order (based on processing speed). To ensure CSV output maintains the same order as input files:

1. **Deferred CSV Writes**: `process_single_file()` stores CSV data in the result dict instead of writing immediately
2. **Result Collection**: All results are collected as threads complete
3. **Sorting**: Results are sorted by `file_counter` (input order)
4. **Sequential Writing**: CSV rows are written in sorted order

This ensures that the output CSV always matches the input file order, making it easier to correlate results with inputs.

### Protected Resources

1. **CSV File Writes**
   ```python
   # CSV writes are sorted before writing
   results.sort(key=lambda r: r["file_counter"])
   for result in results:
       for csv_write in result["csv_writes"]:
           with CSV_WRITE_LOCK:
               pd.DataFrame(...).to_csv(...)
   ```

2. **Statistics Counters**
   ```python
   with STATS_LOCK:
       STATS.files_not_moved += 1
   ```

3. **Logger Output**
   ```python
   with LOGGER_LOCK:
       logger.info(...)
   ```

### Safe Operations (No Lock Needed)
- File reading (read-only)
- Image processing (per-file state)
- Template operations (copied per file)

## Performance Impact

### Expected Speedup
- **Single Core**: ~1x (same as sequential)
- **Dual Core (2 workers)**: ~1.7-1.8x
- **Quad Core (4 workers)**: ~3-3.5x
- **8 Core (8 workers)**: ~5-7x

*Actual speedup depends on:*
- CPU core count
- I/O speed (SSD vs HDD)
- Image complexity
- Number of preprocessors

### Resource Usage
- **Memory**: Slightly higher (multiple images in memory)
- **CPU**: More efficient utilization of multi-core systems
- **I/O**: May saturate on slower disks with many workers

## Limitations & Considerations

1. **GIL (Global Interpreter Lock)**
   - Python's GIL limits true parallelism for CPU-bound operations
   - However, OMR processing includes I/O (reading images, writing CSV)
   - NumPy/OpenCV operations release the GIL
   - Net result: Significant speedup despite GIL

2. **Interactive Mode**
   - Cannot parallelize when showing images (`show_image_level > 0`)
   - Automatically falls back to sequential processing

3. **Memory Constraints**
   - More workers = more images in memory simultaneously
   - Reduce workers if encountering memory issues

4. **Shared State**
   - Template state is managed per-thread
   - SaveImageOps needs proper reset per file

## Testing

### Basic Test
```bash
# Sequential
uv run main.py --input inputs/sample1 --output outputs/test --max-workers 1

# Parallel (4 workers)
uv run main.py --input inputs/sample1 --output outputs/test --max-workers 4
```

### Benchmark
```bash
# Time sequential processing
time uv run main.py --input inputs/samples --output outputs/seq --max-workers 1

# Time parallel processing
time uv run main.py --input inputs/samples --output outputs/par --max-workers 4

# Compare results
diff -r outputs/seq outputs/par
```

## Troubleshooting

### Issue: Garbled Log Output
- **Cause**: Missing LOGGER_LOCK in custom code
- **Fix**: Wrap logger calls in `with LOGGER_LOCK:`

### Issue: CSV Rows in Wrong Order
- **Cause**: Using `as_completed()` without sorting results
- **Fix**: Collect all results, sort by `file_counter`, then write CSV rows
- **Status**: ✅ Fixed - Results are now sorted before CSV writing

### Issue: Incorrect CSV Results
- **Cause**: Missing CSV_WRITE_LOCK
- **Fix**: Wrap DataFrame.to_csv() in `with CSV_WRITE_LOCK:`

### Issue: Wrong File Counts
- **Cause**: Missing STATS_LOCK
- **Fix**: Wrap STATS updates in `with STATS_LOCK:`

### Issue: High Memory Usage
- **Solution**: Reduce `max_parallel_workers`

### Issue: No Speed Improvement
- **Check**: Are you on a single-core system?
- **Check**: Is I/O the bottleneck (slow HDD)?
- **Check**: Is `show_image_level > 0` (forcing sequential)?

## Future Enhancements

Potential improvements for future versions:

1. **Process Pool**: Use multiprocessing for true parallelism (avoid GIL)
2. **Async I/O**: Use asyncio for better I/O concurrency
3. **Dynamic Worker Adjustment**: Adjust workers based on system load
4. **Batch Processing**: Group small images for better efficiency
5. **Progress Bar**: Add visual progress indicator for parallel processing

## Migration Guide

### For Users
- **No changes required** - parallel processing works with existing configs
- **Optional**: Add `"max_parallel_workers": 4` to config for explicit control

### For Developers
- **Critical**: Always use locks when accessing shared resources:
  - CSV writes → `CSV_WRITE_LOCK`
  - Stats updates → `STATS_LOCK`
  - Logger calls → `LOGGER_LOCK`
- **Important**: Test thoroughly with both sequential and parallel modes

