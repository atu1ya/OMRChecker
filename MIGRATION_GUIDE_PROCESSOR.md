# Migration Guide: Unified Processor Architecture

## ⚠️ Breaking Change Notice

This update introduces a **breaking change** by replacing the old stage-based pipeline with a new unified processor architecture. The old `TemplateProcessingPipeline` and related stage classes have been completely removed.

## What Changed

### Removed Components

The following components have been **completely removed**:

1. **Old Pipeline Classes:**
   - `src/algorithm/pipeline/pipeline.py` → `TemplateProcessingPipeline`
   - `src/algorithm/pipeline/base.py` → `PipelineStage` base class

2. **Old Stage Classes:**
   - `src/algorithm/pipeline/stages/preprocessing_stage.py` → `PreprocessingStage`
   - `src/algorithm/pipeline/stages/alignment_stage.py` → `AlignmentStage`
   - `src/algorithm/pipeline/stages/detection_interpretation_stage.py` → `DetectionInterpretationStage`

3. **Old Tests:**
   - `src/tests/test_pipeline.py` → Old pipeline tests

### New Components

The following components have been **added**:

1. **Unified Processor Base:**
   - `src/algorithm/processor/base.py` → `Processor` base class & `ProcessingContext`

2. **New Processor Implementations:**
   - `src/algorithm/processor/pipeline.py` → `ProcessingPipeline` (orchestrator)
   - `src/algorithm/processor/image.py` → `PreprocessingProcessor`
   - `src/algorithm/processor/alignment.py` → `AlignmentProcessor`
   - `src/algorithm/processor/read_omr.py` → `ReadOMRProcessor`

3. **New Tests:**
   - `src/tests/test_processors.py` → Comprehensive processor tests

## Migration Steps

### For End Users

**No changes required!** The `entry.py` entry point automatically uses the new pipeline. Your existing:
- Template JSON files
- Configuration files
- Input images
- Evaluation files

All continue to work exactly as before.

### For Developers/Contributors

If you have custom code that directly uses the pipeline classes, follow these migration steps:

#### 1. Update Imports

**Before:**
```python
from src.algorithm.pipeline.pipeline import TemplateProcessingPipeline
from src.algorithm.pipeline.base import PipelineStage
```

**After:**
```python
from src.algorithm.processor.pipeline import ProcessingPipeline
from src.algorithm.processor.base import Processor, ProcessingContext
```

#### 2. Update Template Usage

The `Template` class now uses only the new pipeline:

**Before:**
```python
template = Template(template_path, tuning_config)
# Old code might have used:
# - template.legacy_pipeline
# - Direct calls to stages
```

**After:**
```python
template = Template(template_path, tuning_config)
# Use the unified pipeline:
context = template.process_file(file_path, gray_image, colored_image)

# Access results from context:
omr_response = context.omr_response
is_multi_marked = context.is_multi_marked
field_interpretations = context.field_id_to_interpretation
```

#### 3. Creating Custom Processors

If you need to extend the pipeline with custom processing:

**Before (Old Stage-based):**
```python
from src.algorithm.pipeline.base import PipelineStage

class CustomStage(PipelineStage):
    def execute(self, context):
        # Custom logic
        return context

    def get_stage_name(self):
        return "CustomStage"
```

**After (New Processor-based):**
```python
from src.algorithm.processor.base import Processor, ProcessingContext

class CustomProcessor(Processor):
    def process(self, context: ProcessingContext) -> ProcessingContext:
        # Custom logic
        context.gray_image = custom_transform(context.gray_image)
        return context

    def get_name(self) -> str:
        return "CustomProcessor"

# Add to pipeline:
template.pipeline.add_processor(CustomProcessor())
```

#### 4. Accessing Pipeline Results

**Before:**
```python
# Results might have been in various places
omr_response = template.get_omr_metrics_for_file(file_path)
```

**After:**
```python
# All results in one context object
context = template.process_file(file_path, gray_image, colored_image)
omr_response = context.omr_response
is_multi_marked = context.is_multi_marked
interpretations = context.field_id_to_interpretation
metadata = context.metadata
```

## Benefits of the New Architecture

### 1. Simplicity
- **One base class** (`Processor`) instead of multiple (`PipelineStage`, `ImageTemplatePreprocessor`)
- **One interface** (`process(context) -> context`) for all operations
- **Consistent patterns** across all processing steps

### 2. Maintainability
- Easier to understand the flow
- Less code duplication
- Clear separation of concerns

### 3. Extensibility
- Add custom processors easily
- Reorder processors dynamically
- Remove/disable processors conditionally

### 4. Testability
- Test any processor in isolation
- Mock context easily
- Consistent test patterns

## Testing

### Test Results
- **Total tests:** 130 (11 old pipeline tests removed)
- **Status:** All passing ✅
- **Coverage:** All functionality preserved

### Running Tests
```bash
# Run all tests
uv run pytest src/tests/

# Run only processor tests
uv run pytest src/tests/test_processors.py

# Run with coverage
uv run pytest src/tests/ --cov=src/algorithm/processor
```

## Troubleshooting

### Error: `ImportError: cannot import name 'TemplateProcessingPipeline'`

**Cause:** Your code is trying to import the old pipeline class.

**Solution:** Update imports to use the new `ProcessingPipeline`:
```python
from src.algorithm.processor.pipeline import ProcessingPipeline
```

### Error: `AttributeError: 'Template' object has no attribute 'legacy_pipeline'`

**Cause:** Your code is trying to access the old pipeline.

**Solution:** Use the new `pipeline` attribute:
```python
# Old: template.legacy_pipeline.process_file(...)
# New:
context = template.pipeline.process_file(file_path, gray_image, colored_image)
```

### Error: `ImportError: cannot import name 'PipelineStage'`

**Cause:** Your custom code extends the old `PipelineStage` class.

**Solution:** Extend the new `Processor` class instead:
```python
from src.algorithm.processor.base import Processor, ProcessingContext
```

## Support

If you encounter issues during migration:

1. **Check the examples** in `src/tests/test_processors.py`
2. **Review the architecture docs** in `UNIFIED_PROCESSOR_ARCHITECTURE.md`
3. **File an issue** on GitHub with:
   - Error message
   - Code snippet showing the issue
   - Expected vs actual behavior

## Timeline

- **Breaking Change Date:** [Current Date]
- **Deprecation Period:** None (immediate breaking change)
- **Old Code Removed:** Yes, completely removed

## Summary

This is a **clean break** from the old architecture. The new unified processor architecture is:
- ✅ Simpler and more maintainable
- ✅ More consistent and testable
- ✅ Easier to extend with custom processors
- ✅ Fully tested and production-ready

While this is a breaking change, the migration is straightforward for most users, and the benefits far outweigh the migration cost.

