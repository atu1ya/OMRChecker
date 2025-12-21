# CSV Row Ordering Fix

## Problem

When using parallel processing (`max_workers > 1`), CSV rows were being written in completion order rather than input file order. This happened because:

1. `ThreadPoolExecutor` processes files concurrently
2. Files complete at different times (based on complexity, I/O, etc.)
3. `as_completed()` yields futures as they finish, not in submission order
4. CSV writes happened immediately upon completion

**Example of shuffled output:**
```
Input files: [file1.jpg, file2.jpg, file3.jpg]
CSV rows:    [file3.jpg, file1.jpg, file2.jpg]  ❌ Wrong order!
```

### Visual: Before Fix

```
Thread 1: file1.jpg ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▶ Complete (3s) ━▶ Write to CSV (3rd)
Thread 2: file2.jpg ━━━━━━━━━━━━━━━━▶ Complete (1.5s) ━▶ Write to CSV (2nd)
Thread 3: file3.jpg ━━━━━━━▶ Complete (0.8s) ━▶ Write to CSV (1st)
                                                         ⬇
                                              CSV: [file3, file2, file1] ❌
```

### Visual: After Fix

```
Thread 1: file1.jpg ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▶ Complete (3s) ━▶ Store result
Thread 2: file2.jpg ━━━━━━━━━━━━━━━━▶ Complete (1.5s) ━▶ Store result
Thread 3: file3.jpg ━━━━━━━▶ Complete (0.8s) ━▶ Store result
                                                         ⬇
                                              Wait for all threads
                                                         ⬇
                                              Sort by file_counter
                                                         ⬇
                                              CSV: [file1, file2, file3] ✅
```

## Solution

Implemented a **deferred write pattern** that collects results, sorts them, then writes in correct order:

### Changes Made

#### 1. **Modified `process_single_file()` to defer CSV writes**

```python
result = {
    "file_counter": idx,
    "csv_writes": []  # Store CSV data instead of writing immediately
}

# Instead of: thread_safe_csv_append(file, data)
# Now: result["csv_writes"].append({"file": file, "data": data})
```

#### 2. **Updated `process_directory_files()` to sort before writing**

**Parallel Mode (max_workers > 1):**
```python
# Collect all results as they complete
results = []
for future in as_completed(futures):
    results.append(future.result())

# Sort by file_counter to maintain input order
results.sort(key=lambda r: r["file_counter"])

# Write CSV in sorted order
for result in results:
    for csv_write in result["csv_writes"]:
        thread_safe_csv_append(csv_write["file"], csv_write["data"])
```

**Sequential Mode (max_workers = 1):**
```python
# Write immediately (no sorting needed)
for file_info in file_tasks:
    result = process_single_file(file_info)
    for csv_write in result["csv_writes"]:
        thread_safe_csv_append(csv_write["file"], csv_write["data"])
```

### Result

**After fix:**
```
Input files: [file1.jpg, file2.jpg, file3.jpg]
CSV rows:    [file1.jpg, file2.jpg, file3.jpg]  ✅ Correct order!
```

## Files Modified

1. **`src/entry.py`**
   - `process_single_file()`: Store CSV data in result dict instead of writing immediately
   - `process_directory_files()`: Collect results, sort by `file_counter`, then write CSVs

2. **`docs/v2/Parallel-Processing.md`**
   - Updated documentation to explain result ordering
   - Added troubleshooting section for CSV ordering

## Testing

Verified with sample containing 3 files:

```bash
cd /Users/udayraj.deshmukh/Personals/OMRChecker
uv run python main.py \
  --inputDir samples/3-answer-key/using-image \
  --outputDir outputs/test-ordering

# Check CSV order
cat outputs/test-ordering/UPSC-mock/Results/*.csv
```

**Output:**
```csv
"file_id","input_path","output_path","score",...
"angle-1.jpg","...","...","70.67",...
"angle-2.jpg","...","...","70.67",...
"angle-3.jpg","...","...","70.67",...
```

✅ Rows match input file order!

## Performance Impact

**Memory:** Slightly higher - results stored in memory before writing instead of streaming
**Speed:** Minimal impact - sorting 100s of results is negligible compared to image processing
**Benefit:** Predictable, ordered CSV output that matches input file order

## Thread Safety

The deferred write pattern maintains thread safety:
- Individual files process in parallel ✅
- Results collected independently ✅
- CSV writes happen sequentially in main thread ✅
- `CSV_WRITE_LOCK` still used for safety ✅

## Migration

**No breaking changes** - existing configs and code continue to work:
- Sequential mode (max_workers=1): CSV writes immediately as before
- Parallel mode (max_workers>1): CSV now written in correct order
- All existing functionality preserved

## Future Enhancements

Potential optimizations (not currently needed):
1. Stream writes for very large batches (1000+ files) to reduce memory
2. Chunked sorting for extremely large datasets
3. Optional flag to disable sorting if user doesn't care about order

