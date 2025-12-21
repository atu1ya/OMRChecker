# Exception Handling Guide

## Overview

OMRChecker uses a comprehensive custom exception hierarchy to provide clear, structured error handling throughout the application. This guide explains how to use and extend the exception system.

## Benefits

The custom exception hierarchy provides:

1. **Better Error Context**: All exceptions carry structured context information
2. **Granular Error Handling**: Catch specific errors or entire categories
3. **Improved Debugging**: Rich error messages with relevant details
4. **Type Safety**: IDE support for exception handling
5. **Security**: Structured error information prevents information leakage

## Exception Hierarchy

```
OMRCheckerError (base)
├── InputError
│   ├── InputDirectoryNotFoundError
│   ├── InputFileNotFoundError
│   └── ImageReadError
├── OutputError
│   ├── OutputDirectoryError
│   └── FileWriteError
├── ValidationError
│   ├── TemplateValidationError
│   ├── ConfigValidationError
│   ├── EvaluationValidationError
│   └── SchemaValidationError
├── ProcessingError
│   ├── MarkerDetectionError
│   ├── ImageProcessingError
│   ├── AlignmentError
│   ├── BubbleDetectionError
│   ├── OCRError
│   └── BarcodeDetectionError
├── TemplateError
│   ├── TemplateNotFoundError
│   ├── TemplateLoadError
│   ├── PreprocessorError
│   └── FieldDefinitionError
├── EvaluationError
│   ├── EvaluationConfigNotFoundError
│   ├── EvaluationConfigLoadError
│   ├── AnswerKeyError
│   └── ScoringError
├── SecurityError
│   ├── PathTraversalError
│   └── FileSizeLimitError
└── ConfigError
    ├── ConfigNotFoundError
    ├── ConfigLoadError
    └── InvalidConfigValueError
```

## Usage Examples

### Basic Exception Handling

```python
from pathlib import Path
from src.exceptions import InputDirectoryNotFoundError, OMRCheckerError

# Raising an exception
def validate_directory(path: Path) -> None:
    if not path.exists():
        raise InputDirectoryNotFoundError(path)
```

### Catching Specific Exceptions

```python
from src.exceptions import (
    MarkerDetectionError,
    ImageReadError,
    TemplateNotFoundError
)

try:
    process_omr_file(file_path)
except MarkerDetectionError as e:
    # Handle marker detection failure
    logger.warning(f"Could not detect markers: {e}")
    save_to_errors_directory(file_path)
except ImageReadError as e:
    # Handle corrupted/unreadable image
    logger.error(f"Image read failed: {e}")
    skip_file(file_path)
except TemplateNotFoundError as e:
    # Critical error - cannot proceed
    logger.critical(f"Missing template: {e}")
    raise
```

### Catching Exception Categories

```python
from src.exceptions import ProcessingError, ValidationError

try:
    result = process_directory(input_dir)
except ValidationError as e:
    # Handle all validation-related errors
    print(f"Validation failed: {e}")
    print(f"Error context: {e.context}")
except ProcessingError as e:
    # Handle all processing-related errors
    print(f"Processing failed: {e}")
    retry_with_different_settings()
```

### Catching All OMRChecker Errors

```python
from src.exceptions import OMRCheckerError

try:
    run_omr_processing()
except OMRCheckerError as e:
    # Catch any application-specific error
    logger.error(f"OMRChecker error: {e}")
    # Access structured context
    if e.context:
        logger.debug(f"Error context: {e.context}")
except Exception as e:
    # Catch unexpected system errors
    logger.critical(f"Unexpected error: {e}")
```

## Creating New Exceptions

### Adding to Existing Categories

If you need a new exception that fits an existing category:

```python
# In src/exceptions.py

class CustomDetectionError(ProcessingError):
    """Raised when custom detection algorithm fails."""

    def __init__(self,
                 file_path: Path,
                 algorithm: str,
                 reason: str | None = None) -> None:
        """
        Initialize the exception.

        Args:
            file_path: Path to the file being processed
            algorithm: Name of the detection algorithm
            reason: Optional reason for failure
        """
        self.file_path = file_path
        self.algorithm = algorithm
        self.reason = reason

        msg = f"Custom detection failed using '{algorithm}' for '{file_path}'"
        if reason:
            msg += f": {reason}"

        super().__init__(
            msg,
            context={
                "file_path": str(file_path),
                "algorithm": algorithm,
                "reason": reason
            }
        )
```

### Creating a New Exception Category

For entirely new error categories:

```python
class DatabaseError(OMRCheckerError):
    """Base class for database-related errors."""

class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""

    def __init__(self,
                 host: str,
                 port: int,
                 reason: str | None = None) -> None:
        self.host = host
        self.port = port
        self.reason = reason

        msg = f"Database connection failed: {host}:{port}"
        if reason:
            msg += f" - {reason}"

        super().__init__(
            msg,
            context={
                "host": host,
                "port": port,
                "reason": reason
            }
        )
```

## Best Practices

### 1. Always Include Context

```python
# Good - includes relevant context
raise ImageProcessingError(
    operation="rotation",
    file_path=file_path,
    reason="Invalid rotation angle: 370"
)

# Bad - missing context
raise Exception("Rotation failed")
```

### 2. Use Specific Exceptions

```python
# Good - specific exception
if not template_path.exists():
    raise TemplateNotFoundError(search_path)

# Bad - generic exception
if not template_path.exists():
    raise Exception("Template not found")
```

### 3. Catch at the Right Level

```python
# Good - catch specific errors where you can handle them
try:
    detect_markers(image)
except MarkerDetectionError:
    # Can handle this specific case
    use_alternative_detection(image)

# Bad - catching too broadly
try:
    detect_markers(image)
except Exception:
    # What went wrong? Can't tell...
    pass
```

### 4. Preserve Error Chains

```python
# Good - preserve the original exception
try:
    data = json.load(f)
except json.JSONDecodeError as e:
    raise ConfigLoadError(config_path, str(e)) from e

# Bad - lose the original error
try:
    data = json.load(f)
except json.JSONDecodeError:
    raise ConfigLoadError(config_path, "Invalid JSON")
```

### 5. Don't Swallow Errors Silently

```python
# Good - log or re-raise
try:
    process_file(path)
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
    save_to_errors(path)

# Bad - silent failure
try:
    process_file(path)
except ProcessingError:
    pass
```

## Error Context

All custom exceptions support a `context` dictionary for structured error information:

```python
exc = ImageProcessingError(
    operation="cropping",
    file_path=Path("/images/test.jpg"),
    reason="Invalid coordinates"
)

# Access context
print(exc.context)
# Output: {
#     'operation': 'cropping',
#     'file_path': '/images/test.jpg',
#     'reason': 'Invalid coordinates'
# }

# Context is included in string representation
print(exc)
# Output: Image processing failed during 'cropping' for '/images/test.jpg':
#         Invalid coordinates (operation=cropping, file_path=/images/test.jpg,
#         reason=Invalid coordinates)
```

## Testing Exceptions

Always test that your code raises the correct exceptions:

```python
import pytest
from src.exceptions import InputDirectoryNotFoundError

def test_raises_correct_exception():
    """Test that missing directory raises InputDirectoryNotFoundError."""
    with pytest.raises(InputDirectoryNotFoundError) as exc_info:
        validate_input_directory(Path("/nonexistent"))

    # Check exception details
    exc = exc_info.value
    assert exc.path == Path("/nonexistent")
    assert "nonexistent" in str(exc)
```

## Migration from Generic Exceptions

When migrating old code:

### Before
```python
if not path.exists():
    raise Exception(f"Path not found: {path}")
```

### After
```python
if not path.exists():
    raise InputDirectoryNotFoundError(path)
```

### Before
```python
try:
    process_image()
except Exception as e:
    logger.error(f"Error: {e}")
```

### After
```python
try:
    process_image()
except MarkerDetectionError as e:
    logger.error(f"Marker detection failed: {e}")
except ImageProcessingError as e:
    logger.error(f"Image processing failed: {e}")
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
```

## Security Considerations

### Don't Expose Sensitive Information

```python
# Good - generic message for users
try:
    load_config(path)
except ConfigLoadError as e:
    # Log detailed error for debugging
    logger.error(f"Config load failed: {e}")
    # Show generic message to user
    print("Configuration file is invalid. Please check the format.")

# Bad - expose internal paths/details to users
try:
    load_config(path)
except ConfigLoadError as e:
    print(f"Error: {e}")  # May expose internal file paths
```

### Validate Input in Exception Constructors

```python
class FileSizeLimitError(SecurityError):
    def __init__(self, path: Path, size: int, limit: int) -> None:
        # Validate inputs
        if size < 0 or limit < 0:
            raise ValueError("Size and limit must be positive")

        self.path = path
        self.size = size
        self.limit = limit
        # ...
```

## Common Patterns

### Retry Logic with Specific Exceptions

```python
from src.exceptions import AlignmentError, ProcessingError

MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    try:
        result = align_image(image)
        break
    except AlignmentError as e:
        if attempt == MAX_RETRIES - 1:
            logger.error(f"Alignment failed after {MAX_RETRIES} attempts: {e}")
            raise
        logger.warning(f"Alignment attempt {attempt + 1} failed, retrying...")
```

### Fallback Strategies

```python
from src.exceptions import OCRError, BarcodeDetectionError

def extract_identifier(image: np.ndarray) -> str:
    """Extract identifier using multiple strategies."""
    try:
        return extract_barcode(image)
    except BarcodeDetectionError:
        logger.info("Barcode detection failed, trying OCR")
        try:
            return extract_text_ocr(image)
        except OCRError:
            logger.warning("All extraction methods failed")
            return "UNKNOWN"
```

### Batch Processing with Error Collection

```python
from src.exceptions import ProcessingError

errors = []
successes = []

for file_path in files:
    try:
        result = process_file(file_path)
        successes.append((file_path, result))
    except ProcessingError as e:
        errors.append((file_path, e))
        logger.warning(f"Failed to process {file_path}: {e}")

# Report summary
print(f"Processed {len(successes)} files successfully")
print(f"Failed to process {len(errors)} files")
```

## See Also

- [Contributing Guide](../CONTRIBUTING.md) - Guidelines for contributing
- [Testing Guide](./testing.md) - How to test your code
- [Architecture Overview](./architecture.md) - System architecture

