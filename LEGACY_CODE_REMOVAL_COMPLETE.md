# Legacy Code Removal Complete

## Overview

Successfully removed all legacy/backward compatibility code from the unified processor architecture, resulting in a cleaner, more maintainable codebase.

## What Was Removed

### 1. Deleted Files

#### `/src/processors/_legacy_processor.py` ❌ DELETED
This file contained a legacy `Processor` wrapper class that was used for backward compatibility. It provided:
- `options` and `tuning_options` attributes
- `relative_dir` path handling
- `get_name()` fallback to `get_class_name()`

**Why removed:** No longer needed as `ImageTemplatePreprocessor` now directly implements the unified `Processor` interface.

### 2. Removed Methods

#### `ImageTemplatePreprocessor.resize_and_apply_filter()` ❌ REMOVED
Located in: `src/processors/image/base.py`

**Old implementation:**
```python
def resize_and_apply_filter(self, in_image, colored_image, _template, _file_path):
    """Legacy method for backward compatibility."""
    config = self.tuning_config

    in_image = ImageUtils.resize_to_shape(self.processing_image_shape, in_image)

    if config.outputs.colored_outputs_enabled:
        colored_image = ImageUtils.resize_to_shape(
            self.processing_image_shape,
            colored_image,
        )

    out_image, colored_image, _template = self.apply_filter(
        in_image, colored_image, _template, _file_path
    )

    return out_image, colored_image, _template
```

**Why removed:**
- Duplicated logic that's now in the unified `process()` method
- Old interface that returned tuples instead of using `ProcessingContext`
- No longer called by any code

### 3. Simplified Class Hierarchy

#### Before (with legacy code):
```python
# _legacy_processor.py
class Processor(UnifiedProcessor):  # Wrapper class
    def __init__(self, options, relative_dir):
        self.options = options
        self.tuning_options = options.get("tuningOptions", {})
        self.relative_dir = Path(relative_dir)
        # ...

    def get_name(self):
        return self.get_class_name() if hasattr(...) else ...

# ImageTemplatePreprocessor.py
class ImageTemplatePreprocessor(Processor):  # Inherits from wrapper
    def __init__(self, ...):
        super().__init__(options, relative_dir)  # Call wrapper
        # ...

    def resize_and_apply_filter(...):  # Legacy method
        # ...

    def process(self, context):  # New method
        # Calls resize_and_apply_filter internally
        # ...
```

#### After (no legacy code):
```python
# image/base.py
class ImageTemplatePreprocessor(Processor):  # Directly inherits from unified Processor
    def __init__(self, options, relative_dir, save_image_ops, default_processing_image_shape):
        # Direct initialization - no wrapper
        self.options = options
        self.tuning_options = options.get("tuningOptions", {})
        self.relative_dir = Path(relative_dir)
        # Image preprocessing specific attributes
        self.append_save_image = save_image_ops.append_save_image
        self.tuning_config = save_image_ops.tuning_config
        self.processing_image_shape = options.get(
            "processingImageShape", default_processing_image_shape
        )
        self.output = options.get("output")

    def get_name(self) -> str:
        """Get the name of this processor (required by unified Processor interface)."""
        return self.get_class_name()

    def process(self, context: ProcessingContext) -> ProcessingContext:
        """Process images using the unified processor interface."""
        # Single unified implementation - no legacy fallback
        # ...
```

### 4. Updated Code

#### `template_layout.py` - Updated to use unified interface

**Before:**
```python
# Applied preprocessors using old tuple-based interface
(
    gray_image,
    colored_image,
    next_template_layout,
) = pre_processor.resize_and_apply_filter(
    gray_image, colored_image, next_template_layout, file_path
)
```

**After:**
```python
# Apply filter using unified processor interface
context = ProcessingContext(
    gray_image=gray_image,
    colored_image=colored_image,
    template=next_template_layout,
    file_path=file_path,
)
context = pre_processor.process(context)

# Extract results from context
gray_image = context.gray_image
colored_image = context.colored_image
next_template_layout = context.template
```

## Benefits of Removal

### 1. **Simpler Class Hierarchy** ✅
- Removed unnecessary wrapper class (`_legacy_processor.Processor`)
- `ImageTemplatePreprocessor` directly inherits from unified `Processor`
- Fewer indirection layers = easier to understand

### 2. **Single Responsibility** ✅
- Each processor has one interface: `process(context) -> context`
- No dual interfaces (old tuple-based + new context-based)
- Consistent pattern across all processors

### 3. **Less Code to Maintain** ✅
```
Files removed: 1 (_legacy_processor.py)
Methods removed: 1 (resize_and_apply_filter)
Wrapper classes removed: 1
Lines of code removed: ~60 lines
```

### 4. **No Confusion** ✅
- Developers don't need to wonder which method to call
- No "should I use resize_and_apply_filter or process?" questions
- Clear, single interface for all processors

### 5. **Cleaner Architecture** ✅
```
Before:
UnifiedProcessor (base) → LegacyProcessor (wrapper) → ImageTemplatePreprocessor

After:
Processor (base) → ImageTemplatePreprocessor
```

## What Remains

### Core Unified Processor Interface

All processors now implement this single, clean interface:

```python
from abc import ABC, abstractmethod
from src.processors.base import ProcessingContext, Processor

class Processor(ABC):
    """Base processor interface."""

    @abstractmethod
    def process(self, context: ProcessingContext) -> ProcessingContext:
        """Process the context and return updated context."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get a human-readable name for this processor."""
        pass
```

### Existing Processors (All Using Unified Interface)

- ✅ **ImageTemplatePreprocessor** - Base for all image preprocessing
  - AutoRotate, CropPage, CropOnMarkers, Contrast, GaussianBlur, etc.
- ✅ **PreprocessingProcessor** - Coordinates image preprocessing
- ✅ **AlignmentProcessor** - Template alignment
- ✅ **ReadOMRProcessor** - OMR detection and interpretation
- ✅ **ProcessingPipeline** - Orchestrates all processors

## Migration Impact

### For End Users
**No impact** - All existing configurations and templates work unchanged

### For Developers
**Positive impact:**
- Simpler API to understand and use
- No legacy methods to avoid or deprecate
- Single, consistent pattern across all processors
- Easier to create new custom processors

### For Custom Processor Authors

**Before (with legacy code):**
```python
class MyCustomProcessor(ImageTemplatePreprocessor):
    def apply_filter(self, image, colored_image, template, file_path):
        # Could call either:
        # - resize_and_apply_filter() [legacy]
        # - process() [new]
        return modified_image, colored_image, template
```

**After (no legacy code):**
```python
class MyCustomProcessor(ImageTemplatePreprocessor):
    def apply_filter(self, image, colored_image, template, file_path):
        # One clear way - implement apply_filter()
        # The base class handles process() consistently
        return modified_image, colored_image, template
```

## Test Results

```bash
Total Tests: 130
Status: ✅ ALL PASSING (100%)
Time: ~19 seconds
```

**Breakdown:**
- ✅ Processor tests: 7/7
- ✅ Integration tests: 19/19
- ✅ All other tests: 104/104

## Code Quality

```bash
uv run ruff check src/processors/
# Output: All checks passed! ✅
```

## Summary of Changes

### Files Modified
1. `src/processors/image/base.py`
   - Removed `resize_and_apply_filter()` method
   - Updated `__init__()` to not call `super().__init__()`
   - Directly initialize all attributes
   - Added `get_name()` method implementation

2. `src/algorithm/template/layout/template_layout.py`
   - Updated `apply_preprocessors()` to use `process()` instead of `resize_and_apply_filter()`
   - Now uses `ProcessingContext` for data passing

### Files Deleted
1. `src/processors/_legacy_processor.py` ❌

### Lines of Code Changed
- **Removed:** ~60 lines
- **Modified:** ~30 lines
- **Net reduction:** ~30 lines

## Conclusion

The legacy code removal successfully:

✅ **Simplified the architecture** - Removed wrapper classes and dual interfaces

✅ **Improved maintainability** - Less code to maintain, single clear pattern

✅ **Enhanced clarity** - One way to do things, no confusion

✅ **Maintained stability** - All 130 tests passing, no breaking changes for end users

✅ **Cleaner codebase** - ~30 fewer lines, better organized

The unified processor architecture is now fully realized with no legacy baggage. All processors use a single, consistent interface making the codebase easier to understand, maintain, and extend.

---

**Status:** ✅ **COMPLETE**

**Tests:** 130/130 passing (100%)

**Linting:** All checks passed

**Lines Removed:** ~30 lines

**Breaking Changes:** None for end users (internal refactoring only)

