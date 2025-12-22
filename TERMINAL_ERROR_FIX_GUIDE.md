# Terminal Error Fix - Step by Step Guide

## Context
After running `uv run python main.py -i samples/1-mobile-camera`, we encountered the error:
```
Error processing samples/1-mobile-camera/MobileCamera/sheet1.jpg:
type object 'BubblesFieldInterpretation' has no attribute 'get_global_threshold'
```

This document shows exactly what was done to fix this and subsequent errors.

---

## Error 1: `get_global_threshold` Not Found

### The Problem
```python
# In interpretation_pass.py (line 101):
) = BubblesFieldInterpretation.get_global_threshold(
    all_outlier_deviations,
    GLOBAL_PAGE_THRESHOLD_STD,
    MIN_JUMP=MIN_JUMP_STD,
    JUMP_DELTA=JUMP_DELTA_STD,
    ...
)
```

The new refactored `BubblesFieldInterpretation` no longer has this static method.

### The Fix
Replace the static method call with the new `GlobalThresholdStrategy`:

```python
# Added imports at top of file:
from src.algorithm.template.threshold.strategies import (
    GlobalThresholdStrategy,
    ThresholdConfig,
)

# Replaced the method call:
def get_outlier_deviation_threshold(self, file_path, all_outlier_deviations):
    config = self.tuning_config
    MIN_JUMP_STD = config.thresholding.MIN_JUMP_STD
    GLOBAL_PAGE_THRESHOLD_STD = config.thresholding.GLOBAL_PAGE_THRESHOLD_STD

    strategy = GlobalThresholdStrategy()
    threshold_config = ThresholdConfig(
        min_jump=MIN_JUMP_STD,
        default_threshold=GLOBAL_PAGE_THRESHOLD_STD,
    )

    result = strategy.calculate_threshold(all_outlier_deviations, threshold_config)
    return result.threshold_value
```

**Same fix applied to `get_fallback_threshold()` method.**

---

## Error 2: `'float' object has no attribute 'mean_value'`

### The Problem
The code was trying to do:
```python
outlier_values = [item.mean_value for item in all_outlier_deviations]
```

But `all_outlier_deviations` is a list of **floats** (std deviations), not objects!

### The Fix
**For outlier deviations** (already floats):
```python
# Just use them directly:
result = strategy.calculate_threshold(all_outlier_deviations, threshold_config)
```

**For field-wise means** (BubbleMeanValue objects):
```python
# Extract mean_value from objects:
bubble_values = [item.mean_value for item in field_wise_means_and_refs]
result = strategy.calculate_threshold(bubble_values, threshold_config)
```

---

## Error 3: Missing Config Attributes

### The Problem
```
'ThresholdingConfig' object has no attribute 'OUTLIER_STD_THRESHOLD'
'ThresholdingConfig' object has no attribute 'GLOBAL_PAGE_THRESHOLD_WHITE'
```

These attributes don't exist in the config schema!

### The Fix
```python
def _create_threshold_config(
    self, file_level_interpretation_aggregates  # Added parameter
) -> ThresholdConfig:
    config = self.tuning_config
    return ThresholdConfig(
        min_jump=config.thresholding.MIN_JUMP,
        jump_delta=config.thresholding.JUMP_DELTA,
        min_gap_two_bubbles=config.thresholding.MIN_GAP_TWO_BUBBLES,
        min_jump_surplus_for_global_fallback=config.thresholding.MIN_JUMP_SURPLUS_FOR_GLOBAL_FALLBACK,
        confident_jump_surplus_for_disparity=config.thresholding.CONFIDENT_JUMP_SURPLUS_FOR_DISPARITY,
        global_threshold_margin=config.thresholding.GLOBAL_THRESHOLD_MARGIN,

        # FIXED: Get from file-level aggregates (calculated per file)
        outlier_deviation_threshold=file_level_interpretation_aggregates.get(
            "outlier_deviation_threshold_for_file", 5.0
        ),

        # FIXED: Use GLOBAL_PAGE_THRESHOLD (not _WHITE)
        default_threshold=config.thresholding.GLOBAL_PAGE_THRESHOLD,
    )
```

Also updated the call site:
```python
# In run_interpretation():
threshold_config = self._create_threshold_config(
    file_level_interpretation_aggregates  # Pass aggregates
)
```

---

## Error 4: `'BubbleInterpretation' object has no attribute 'item_reference'`

### The Problem
The drawing code (`interpretation_drawing.py`) expects:
```python
bubble = bubble_interpretation.item_reference
```

But our `BubbleInterpretation` class didn't have this attribute!

### The Fix
Added missing attributes to `BubbleInterpretation`:

```python
class BubbleInterpretation:
    """Single bubble interpretation result."""

    def __init__(self, bubble_mean, threshold: float) -> None:
        self.bubble_mean = bubble_mean
        self.threshold = threshold
        self.mean_value = bubble_mean.mean_value  # ADDED
        self.is_attempted = bubble_mean.mean_value < threshold
        self.bubble_value = (
            bubble_mean.unit_bubble.bubble_value
            if hasattr(bubble_mean.unit_bubble, "bubble_value")
            else ""
        )
        self.item_reference = bubble_mean.unit_bubble  # ADDED for drawing
```

---

## Final Verification

### Test 1: Run with Sample
```bash
uv run python main.py -i samples/1-mobile-camera
```

**Result:** ✅ SUCCESS
```
Read Response: {'Roll': 'E503110026', 'q5': '6', 'q6': '11', ...}
Total file(s) processed: 1 (Sum Tallied!)
```

### Test 2: Linting
```bash
uv run ruff check src/
```

**Result:** ✅ All checks passed!

---

## Summary of Files Changed

1. **`src/algorithm/template/detection/bubbles_threshold/interpretation_pass.py`**
   - Added imports for `GlobalThresholdStrategy` and `ThresholdConfig`
   - Updated `get_outlier_deviation_threshold()` to use strategy
   - Updated `get_fallback_threshold()` to use strategy
   - Fixed data type handling (floats vs objects)

2. **`src/algorithm/template/detection/bubbles_threshold/interpretation.py`**
   - Updated `_create_threshold_config()` signature to accept aggregates
   - Fixed config attribute names
   - Added `mean_value` to `BubbleInterpretation`
   - Added `item_reference` to `BubbleInterpretation`

---

## Key Lessons Learned

1. **Static Methods → Strategy Pattern**: The refactoring successfully replaced static utility methods with proper strategy classes.

2. **Type Awareness**: Need to know whether data is primitive (float) or object (BubbleMeanValue) to handle correctly.

3. **Config Schema**: Always check the actual config schema rather than assuming attribute names.

4. **Interface Preservation**: When refactoring, preserve the interfaces that other subsystems (like drawing) depend on.

5. **File-Level vs Config**: Some values (like `outlier_deviation_threshold`) are calculated per file, not stored in config.

---

**All errors resolved. System working perfectly!** ✅

