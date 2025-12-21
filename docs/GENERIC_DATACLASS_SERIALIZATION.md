# Generic Dataclass Serialization Implementation

## Summary

Replaced the manual `to_dict()` implementation in the `Config` class with a generic, reusable serializer that automatically handles nested dataclasses, Path objects, Enums, and collections.

The serializer is available in `src/utils/serialization.py` and re-exported from `src/utils/parsing.py` for backward compatibility.

## Problem Statement

The original `to_dict()` method in the `Config` class manually listed every field:

```python
def to_dict(self) -> dict:
    return {
        "path": str(self.path),
        "thresholding": {
            "GAMMA_LOW": self.thresholding.GAMMA_LOW,
            "MIN_GAP_TWO_BUBBLES": self.thresholding.MIN_GAP_TWO_BUBBLES,
            "MIN_JUMP": self.thresholding.MIN_JUMP,
            # ... 30+ more lines of repetitive field mappings
        },
        "outputs": {
            "output_mode": self.outputs.output_mode,
            # ... more fields
        },
        "processing": {
            "max_parallel_workers": self.processing.max_parallel_workers,
        },
    }
```

**Issues with this approach:**
1. **Error-prone**: Easy to miss fields when adding new ones
2. **Verbose**: ~40 lines of boilerplate for field mapping
3. **Hard to maintain**: Every dataclass change requires manual updates
4. **Not DRY**: Field names repeated twice (definition + serialization)
5. **No reusability**: Can't be used for other dataclasses

## Solution

Created a generic `dataclass_to_dict()` function that:
- Automatically serializes any dataclass structure
- Handles nested dataclasses recursively
- Converts Path objects to strings
- Converts Enums to their values
- Processes lists, tuples, and dictionaries
- Preserves primitive types (str, int, float, bool, None)

## Implementation

### New Files

1. **`src/utils/serialization.py`**
   - Generic serialization utility with comprehensive documentation
   - Handles all common Python types used in dataclasses
   - No circular dependencies - uses only stdlib imports
   - Re-exported from `src/utils/parsing.py` for convenience

2. **`src/tests/test_dataclass_serialization.py`**
   - Comprehensive test suite (8 tests, all passing)
   - Tests nested dataclasses, Path objects, Enums, collections
   - Validates edge cases and type handling

### Updated Files

1. **`src/schemas/models/config.py`**
   - Simplified `to_dict()` from ~40 lines to 1 line
   - Added import for `dataclass_to_dict`
   - No changes to external API or behavior

## Code Changes

### Before
```python
def to_dict(self) -> dict:
    return {
        "path": str(self.path),
        "thresholding": {
            "GAMMA_LOW": self.thresholding.GAMMA_LOW,
            # ... 30+ more lines
        },
        # ... more nested structures
    }
```

### After
```python
from src.utils.serialization import dataclass_to_dict
# Or: from src.utils.parsing import dataclass_to_dict

def to_dict(self) -> dict:
    return dataclass_to_dict(self)
```

## Benefits

1. **Automatic**: Works with any dataclass, no manual field listing
2. **Maintainable**: Adapts automatically when fields are added/removed
3. **Tested**: Single implementation with comprehensive test coverage
4. **Reusable**: Can be used for any dataclass in the codebase
5. **Type-safe**: Leverages Python's built-in `dataclasses.asdict()`
6. **Extensible**: Easy to add support for new types if needed

## Usage Examples

### Simple Dataclass
```python
@dataclass
class Person:
    name: str
    age: int

person = Person(name="Alice", age=30)
result = dataclass_to_dict(person)
# {'name': 'Alice', 'age': 30}
```

### Nested with Path and Enum
```python
from pathlib import Path
from enum import Enum

class Status(Enum):
    ACTIVE = "active"

@dataclass
class Config:
    path: Path
    status: Status

config = Config(path=Path("/tmp/config.json"), status=Status.ACTIVE)
result = dataclass_to_dict(config)
# {'path': '/tmp/config.json', 'status': 'active'}
```

## Testing

All tests pass (93/93):
- ✅ 8 new tests for generic serializer
- ✅ 10 existing config-related tests
- ✅ 75 other existing tests

The generic serializer produces identical output to the manual implementation, ensuring full backward compatibility.

## Future Applications

This generic serializer can be used for:
- Other dataclasses that need JSON serialization
- API response formatting
- Configuration export/import
- Data persistence layers

Consider converting `QuestionMeta` and `EvaluationMeta` classes to dataclasses to leverage this utility in future refactoring.

## Related Documentation

- Implementation details: `src/utils/serialization.py` (includes extensive docstring with examples)
- Re-export for convenience: `src/utils/parsing.py` (backward compatibility)
- Test coverage: `src/tests/test_dataclass_serialization.py`
- Original dataclass migration: `docs/IMPLEMENTATION_SUMMARY_DATACLASSES.md`

