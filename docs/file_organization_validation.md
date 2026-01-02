# File Grouping Configuration Validation

## Overview

The File Organization feature now includes comprehensive validation to catch common user mistakes **before** processing begins. This saves time and helps users fix configuration errors quickly.

## What Gets Validated

### 1. **Field Availability**
Checks if all fields used in patterns are actually available:
- Built-in fields: `{file_path}`, `{file_name}`, `{file_stem}`, `{original_name}`, `{is_multi_marked}`
- Evaluation fields: `{score}` (requires `evaluation.json`)
- Template fields: Any field defined in `template.json` (e.g., `{roll_number}`, `{booklet_code}`)

### 2. **Evaluation Dependency**
Ensures `{score}` is only used when `evaluation.json` exists.

### 3. **Pattern Syntax**
Validates format string syntax (proper use of `{}` braces).

### 4. **Regex Validity**
Checks that regex patterns in matchers compile correctly.

### 5. **Valid Options**
- `action`: Must be `"symlink"` or `"copy"`
- `collision_strategy`: Must be `"skip"`, `"increment"`, or `"overwrite"`

### 6. **Rule Priorities**
Ensures no duplicate priority values across rules.

## Example Error Messages

### Missing Evaluation File
```json
{
  "destination_pattern": "scores/{score}/roll_{roll}",
  "matcher": {
    "formatString": "{score}",
    "matchRegex": "^[8-9]"
  }
}
```

**Error:**
```
Rule #1 ('High Scorers') destination_pattern: Field '{score}' requires evaluation.json
to be present. Either add evaluation.json or remove this field from the pattern.
```

### Invalid Template Field
```json
{
  "destination_pattern": "output/{invalid_field}",
  "matcher": {
    "formatString": "{roll_number}",
    "matchRegex": ".*"
  }
}
```

**Error:**
```
Rule #1 ('Test Rule') destination_pattern: Field '{invalid_field}' not found in template.
Available fields: {booklet_code}, {file_name}, {file_path}, {file_stem},
{is_multi_marked}, {name}, {original_name}, {roll_number}, {score}
```

### Invalid Regex Pattern
```json
{
  "matcher": {
    "formatString": "{roll_number}",
    "matchRegex": "[unclosed(bracket"
  }
}
```

**Error:**
```
Rule #1 ('Bad Regex'): Invalid regex pattern in matcher.matchRegex:
unterminated character set at position 0
```

### Invalid Action
```json
{
  "action": "move"
}
```

**Error:**
```
Rule #1 ('Test Rule'): Invalid action 'move'. Must be 'symlink' or 'copy'.
```

### Duplicate Priorities
```json
{
  "rules": [
    {"name": "Rule A", "priority": 1, ...},
    {"name": "Rule B", "priority": 1, ...}
  ]
}
```

**Error:**
```
Duplicate rule priorities found: {1}. Each rule should have a unique priority.
```

### Invalid Pattern Syntax
```json
{
  "destination_pattern": "output/{unclosed_brace"
}
```

**Error:**
```
Rule #1 ('Bad Pattern') destination_pattern: Invalid pattern syntax:
Single '}' encountered in format string
```

## When Validation Runs

Validation runs **once per directory** when:
1. File grouping is enabled in `config.json`
2. A template is loaded
3. Before any files are processed

If validation fails:
- Clear error messages are logged
- File organization is **automatically disabled** for that directory
- Processing continues normally (without organization)
- User can fix errors and re-run

## Integration Example

In `entry.py`, validation is called automatically:

```python
file_grouping_config = tuning_config.outputs.file_grouping
if file_grouping_config.enabled:
    # Validate configuration
    has_evaluation = evaluation_config is not None
    validation_errors = file_grouping_config.validate(
        template=template,
        has_evaluation=has_evaluation
    )

    if validation_errors:
        logger.error("File grouping configuration has errors:")
        for error in validation_errors:
            logger.error(f"  - {error}")
        logger.error("File organization will be DISABLED for this directory.")
    else:
        # All good - add processor
        organizer = FileOrganizerProcessor(...)
        template.pipeline.add_processor(organizer)
```

## Benefits

1. **Early Detection**: Catches errors before processing starts
2. **Clear Messages**: Tells users exactly what's wrong and how to fix it
3. **Helpful Suggestions**: Lists available fields when field not found
4. **Non-Blocking**: Processing continues even if organization is disabled
5. **Comprehensive**: Checks multiple error types in one pass

## Testing

15 comprehensive tests ensure validation works correctly:
- ✅ Disabled config skips validation
- ✅ Built-in fields always valid
- ✅ Score field requires evaluation
- ✅ Template field validation
- ✅ Invalid regex detection
- ✅ Invalid action/collision strategy
- ✅ Duplicate priority detection
- ✅ Pattern syntax validation
- ✅ Multiple errors reported together
- ✅ Helpful error messages with suggestions

