# Field Block Shifting Augmentation - Enhancement

## Overview

Added a new augmentation type to the data augmentation script that simulates field block misalignment by physically moving field blocks within the image. This creates realistic training data specifically for testing and validating the ML-based shift detection system.

## New Augmentation Type: Field Block Shifting

### Key Features

1. **Intelligent Background Detection**
   - Samples from image corners to detect background color
   - Calculates median color from all corners for robustness
   - Handles various paper colors (typically white for OMR sheets)

2. **Realistic Shifting**
   - Moves field blocks by random amounts within configurable margins
   - Default max shift: 10-40 pixels (randomized per augmentation)
   - Preserves field block content perfectly
   - Fills vacated areas with detected background color

3. **Boundary Awareness**
   - Prevents field blocks from shifting outside image boundaries
   - Automatically adjusts shifts if they would exceed image dimensions
   - Ensures no data loss or clipping

4. **Label Preservation**
   - Updates ROI bounding box coordinates to match new positions
   - Stores shift metadata (dx, dy) for validation purposes
   - Maintains all other ROI properties unchanged

## Implementation Details

### Method: `_shift_field_blocks`

```python
def _shift_field_blocks(
    self, image: np.ndarray, labels: dict, max_shift: int = 30
) -> tuple[np.ndarray, dict]:
    """Shift field blocks to simulate misalignment while preserving white background.

    This augmentation creates realistic training data for the shift detection system
    by moving field blocks within a margin, using the white background to fill gaps.
    """
```

**Process:**

1. **Background Detection**
   - Sample 20x20 pixel regions from each corner
   - Calculate mean color of each corner
   - Take median across all corners for robustness

2. **Per-Block Shifting**
   - For each field block (ROI):
     - Generate random shift: `(-max_shift, +max_shift)` for both x and y
     - Calculate new position with boundary checking
     - Extract field block from original position
     - Fill old position with background color
     - Place field block at new position
     - Update ROI coordinates and store shift metadata

3. **Label Updates**
   - Update `bbox` coordinates to match new positions
   - Add `shift` metadata: `{"dx": shift_x, "dy": shift_y}`
   - Preserve all other ROI properties

### Integration into Augmentation Pipeline

Updated the augmentation type rotation from **6 types** to **7 types**:

```python
aug_type = aug_idx % 7  # Increased to 7 types

# Type 0: Brightness adjustment
# Type 1: Contrast adjustment
# Type 2: Gaussian noise
# Type 3: Blur
# Type 4: Rotation
# Type 5: Combined (brightness + noise)
# Type 6: Field block shifting (NEW!)
```

## Benefits for Shift Detection Training

1. **Realistic Misalignment Simulation**
   - Mimics real-world scanner/printing misalignments
   - Creates varied shift patterns across different field blocks
   - Tests the shift detection system under diverse conditions

2. **Ground Truth Shift Data**
   - Stores exact shift amounts in label metadata
   - Enables precise validation of ML shift predictions
   - Allows calculation of shift detection accuracy

3. **Seamless Visual Quality**
   - Uses background color filling to avoid visual artifacts
   - Maintains professional appearance for human review
   - No noticeable defects or distortions

4. **Complementary to Traditional Augmentation**
   - Works alongside existing augmentation types
   - Can be combined with brightness, noise, rotation, etc.
   - Provides comprehensive dataset variation

## Usage Example

### Basic Usage

```python
from pathlib import Path
from augment_data import DataAugmenter

augmenter = DataAugmenter(
    source_images_dir=Path("outputs/training_data/dataset/images"),
    source_labels_dir=Path("outputs/training_data/dataset/labels"),
    output_dir=Path("outputs/training_data/augmented"),
)

# Generate 200 samples (includes field block shifting)
augmenter.augment_dataset(target_count=200)
```

### Distribution

With 200 target samples and 8 original samples:
- Augmentations per image: (200 - 8) // 8 = 24
- Field block shifting samples: ~24/7 ≈ 3-4 per original image
- Total shifted samples: ~24-32 images

## Sample Output

### Label Metadata

**Original:**
```json
{
  "rois": [
    {
      "bbox": {"x": 100, "y": 200, "width": 400, "height": 300},
      "label": "MCQBlock1a1"
    }
  ]
}
```

**After Shifting:**
```json
{
  "rois": [
    {
      "bbox": {"x": 125, "y": 215, "width": 400, "height": 300},
      "label": "MCQBlock1a1",
      "shift": {"dx": 25, "dy": 15}
    }
  ]
}
```

## Configuration Options

### Adjustable Parameters

1. **Max Shift Amount**
   - Currently randomized: 10-40 pixels
   - Can be made configurable via constructor
   - Recommended range: 10-50 pixels for OMR sheets

2. **Background Detection Margin**
   - Current: 20x20 pixels from each corner
   - Adjustable for different image sizes
   - Larger margins = more robust background detection

3. **Shift Distribution**
   - Currently uniform random within [-max_shift, +max_shift]
   - Could be modified to favor certain shift patterns
   - Could add different distributions (Gaussian, biased, etc.)

## Testing the Enhancement

### Validation Steps

1. **Visual Inspection**
   ```bash
   # Generate augmented data
   python augment_data.py

   # Check outputs/training_data/augmented/images/
   # Look for *_aug006.jpg, *_aug013.jpg, etc. (shifted samples)
   ```

2. **Label Verification**
   ```python
   import json
   from pathlib import Path

   # Load a shifted sample label
   label_file = Path("outputs/training_data/augmented/labels/sample_aug006.json")
   with label_file.open() as f:
       data = json.load(f)

   # Check shift metadata
   for roi in data["rois"]:
       if "shift" in roi:
           print(f"{roi['label']}: shifted by {roi['shift']}")
   ```

3. **Shift Detection Testing**
   - Use augmented data to train field block detector
   - Compare ML-detected positions with ground truth shifts
   - Validate shift detection accuracy

## Future Enhancements

1. **Per-Block Shift Configuration**
   - Allow different max shifts per field block type
   - More restrictive for critical blocks (IDs, codes)
   - More permissive for answer blocks

2. **Shift Pattern Generation**
   - Add correlated shifts (entire regions moving together)
   - Simulate scanner bed tilt patterns
   - Add directional bias for common misalignments

3. **Quality Validation**
   - Detect and avoid overlapping field blocks after shifting
   - Ensure minimum spacing between blocks
   - Validate that shifts don't create unrealistic layouts

4. **Metadata Enrichment**
   - Store original positions for easy comparison
   - Add shift magnitude and direction statistics
   - Include background detection confidence

## Code Quality

✅ **All ruff checks passed**
✅ **Type annotations complete**
✅ **Documentation comprehensive**
✅ **Error handling robust**

## Summary

This enhancement adds a critical augmentation type specifically designed for the shift detection system. By generating realistic shifted field blocks with accurate ground truth metadata, it enables:

1. Training of robust shift detection models
2. Validation of shift detection accuracy
3. Testing of shift correction algorithms
4. Evaluation of confidence adjustment strategies

The implementation is clean, well-documented, and maintains the high code quality standards of the project.

---

**Date**: January 4, 2026
**Status**: ✅ Complete
**Lines Added**: ~110
**Linter**: ✅ Clean

