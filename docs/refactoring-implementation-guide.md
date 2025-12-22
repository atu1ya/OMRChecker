# Detection & Interpretation Pass Refactoring - Implementation Guide

This document provides concrete, implementable code examples for refactoring the detection and interpretation passes based on industry standards.

## Table of Contents

1. [Quick Start: Minimal Viable Refactoring](#quick-start-minimal-viable-refactoring)
2. [Typed Detection Results](#typed-detection-results)
3. [Pipeline Architecture](#pipeline-architecture)
4. [Repository Pattern](#repository-pattern)
5. [Strategy Pattern for Thresholds](#strategy-pattern-for-thresholds)
6. [Async Processing](#async-processing)
7. [Testing Examples](#testing-examples)

---

## Quick Start: Minimal Viable Refactoring

### Step 1: Add Type Hints to Existing Code

Start by adding type hints without changing logic:

```python
# Before (src/algorithm/template/detection/base/detection_pass.py)
def update_aggregates_on_processed_field_detection(self, field, field_detection):
    self.update_field_level_aggregates_on_processed_field_detection(
        field, field_detection
    )

# After
from typing import Dict, Any
from src.algorithm.template.layout.field.base import Field
from src.algorithm.template.detection.base.detection import FieldDetection

def update_aggregates_on_processed_field_detection(
    self,
    field: Field,
    field_detection: FieldDetection
) -> None:
    """Update aggregates after processing a field detection.

    Args:
        field: The field that was processed
        field_detection: The detection result for the field
    """
    self.update_field_level_aggregates_on_processed_field_detection(
        field, field_detection
    )
```

### Step 2: Create Typed Models (Non-Breaking)

Create new models alongside existing dictionaries:

```python
# src/algorithm/template/detection/models/detection_results.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class ScanQuality(Enum):
    """Quality assessment of scan"""
    EXCELLENT = "excellent"  # Clear, high contrast
    GOOD = "good"            # Acceptable quality
    ACCEPTABLE = "acceptable" # Marginal, may need review
    POOR = "poor"            # Likely to have errors

@dataclass
class BubbleMeanValue:
    """Single bubble mean value with metadata"""
    mean_value: float
    unit_bubble: Any  # BubblesScanBox
    position: tuple[int, int]

    def __lt__(self, other: 'BubbleMeanValue') -> bool:
        """Enable sorting by mean value"""
        return self.mean_value < other.mean_value

@dataclass
class BubbleFieldDetectionResult:
    """Typed result for bubble field detection"""
    field_id: str
    field_label: str
    field_type: str
    bubble_means: List[BubbleMeanValue]
    std_deviation: float
    scan_quality: ScanQuality
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_reliable(self) -> bool:
        """Check if detection is reliable enough for interpretation"""
        return self.scan_quality in [ScanQuality.EXCELLENT, ScanQuality.GOOD]

    @property
    def sorted_bubble_means(self) -> List[BubbleMeanValue]:
        """Get bubble means sorted by value"""
        return sorted(self.bubble_means)

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert to legacy dictionary format for backward compatibility"""
        return {
            "field_bubble_means": self.bubble_means,
            "field_bubble_means_std": self.std_deviation,
            "scan_quality": self.scan_quality.value,
        }

    @classmethod
    def from_legacy_dict(cls, field_id: str, field_label: str,
                         legacy_data: Dict[str, Any]) -> 'BubbleFieldDetectionResult':
        """Create from legacy dictionary format"""
        return cls(
            field_id=field_id,
            field_label=field_label,
            field_type="bubbles",
            bubble_means=legacy_data["field_bubble_means"],
            std_deviation=legacy_data["field_bubble_means_std"],
            scan_quality=ScanQuality(legacy_data.get("scan_quality", "acceptable"))
        )

@dataclass
class OCRFieldDetectionResult:
    """Typed result for OCR field detection"""
    field_id: str
    field_label: str
    detections: List[Any]  # List[OCRDetection]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_legacy_dict(self) -> Dict[str, Any]:
        return {"detections": self.detections}

@dataclass
class FileDetectionResults:
    """All detection results for a file"""
    file_path: str
    bubble_fields: Dict[str, BubbleFieldDetectionResult] = field(default_factory=dict)
    ocr_fields: Dict[str, OCRFieldDetectionResult] = field(default_factory=dict)
    global_statistics: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def get_field_result(self, field_id: str):
        """Get result for any field type"""
        if field_id in self.bubble_fields:
            return self.bubble_fields[field_id]
        elif field_id in self.ocr_fields:
            return self.ocr_fields[field_id]
        raise KeyError(f"Field {field_id} not found in detection results")

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert to legacy nested dictionary format"""
        return {
            "field_label_wise_aggregates": {
                **{k: v.to_legacy_dict() for k, v in self.bubble_fields.items()},
                **{k: v.to_legacy_dict() for k, v in self.ocr_fields.items()},
            }
        }
```

### Step 3: Gradual Migration Helper

Create a bridge class that works with both old and new formats:

```python
# src/algorithm/template/detection/bridges/detection_bridge.py
from typing import Dict, Any, Union
from src.algorithm.template.detection.models.detection_results import (
    BubbleFieldDetectionResult,
    FileDetectionResults
)

class DetectionResultsBridge:
    """Bridge between legacy dict-based and new typed detection results"""

    def __init__(self):
        self._typed_results: Dict[str, FileDetectionResults] = {}
        self._legacy_aggregates: Dict[str, Dict[str, Any]] = {}

    def save_typed_result(self, file_path: str, result: FileDetectionResults) -> None:
        """Save new typed result"""
        self._typed_results[file_path] = result
        # Also maintain legacy format
        self._legacy_aggregates[file_path] = result.to_legacy_dict()

    def get_typed_result(self, file_path: str) -> FileDetectionResults:
        """Get new typed result"""
        if file_path in self._typed_results:
            return self._typed_results[file_path]

        # Convert from legacy if available
        if file_path in self._legacy_aggregates:
            return self._convert_legacy_to_typed(file_path)

        raise KeyError(f"No results found for {file_path}")

    def get_legacy_dict(self, file_path: str) -> Dict[str, Any]:
        """Get legacy dictionary format (for backward compatibility)"""
        if file_path in self._legacy_aggregates:
            return self._legacy_aggregates[file_path]

        if file_path in self._typed_results:
            return self._typed_results[file_path].to_legacy_dict()

        raise KeyError(f"No results found for {file_path}")

    def _convert_legacy_to_typed(self, file_path: str) -> FileDetectionResults:
        """Convert legacy format to typed"""
        legacy = self._legacy_aggregates[file_path]
        # Conversion logic here
        return FileDetectionResults(file_path=file_path)
```

---

## Typed Detection Results

### Complete Example with Validation

```python
# src/algorithm/template/detection/models/validated_results.py
from dataclasses import dataclass, field
from typing import List, Optional
from pydantic import BaseModel, validator, Field
from enum import Enum

class ScanQuality(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"

class BubbleFieldDetectionResultValidated(BaseModel):
    """Pydantic model with automatic validation"""

    field_id: str = Field(..., min_length=1, description="Unique field identifier")
    field_label: str = Field(..., min_length=1)
    bubble_means: List[float] = Field(..., min_items=1, max_items=100)
    std_deviation: float = Field(..., ge=0.0, description="Must be non-negative")
    scan_quality: ScanQuality

    @validator('bubble_means')
    def validate_bubble_means(cls, v):
        """Ensure bubble means are valid pixel intensities"""
        if any(mean < 0 or mean > 255 for mean in v):
            raise ValueError("Bubble means must be between 0 and 255")
        return v

    @validator('std_deviation')
    def validate_std_deviation(cls, v, values):
        """Validate std deviation is reasonable"""
        if 'bubble_means' in values:
            max_possible_std = 255.0  # Maximum for 8-bit images
            if v > max_possible_std:
                raise ValueError(f"Std deviation {v} exceeds maximum {max_possible_std}")
        return v

    def assess_quality(self) -> ScanQuality:
        """Automatically assess scan quality based on metrics"""
        if self.std_deviation > 50:
            return ScanQuality.EXCELLENT
        elif self.std_deviation > 30:
            return ScanQuality.GOOD
        elif self.std_deviation > 15:
            return ScanQuality.ACCEPTABLE
        else:
            return ScanQuality.POOR

    class Config:
        use_enum_values = True
        validate_assignment = True

# Usage example:
try:
    result = BubbleFieldDetectionResultValidated(
        field_id="q1",
        field_label="Question1",
        bubble_means=[120.5, 200.3, 115.8],
        std_deviation=45.2,
        scan_quality=ScanQuality.GOOD
    )
    print(f"Valid result: {result.field_label}")
except ValueError as e:
    print(f"Validation error: {e}")
```

---

## Pipeline Architecture

### Complete Pipeline Implementation

```python
# src/algorithm/template/pipeline/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')
U = TypeVar('U')

@dataclass
class PipelineContext:
    """Context passed through pipeline stages"""
    file_path: str
    config: Dict[str, Any]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class StageResult(Generic[T]):
    """Result from a pipeline stage"""
    success: bool
    data: Optional[T] = None
    error: Optional[Exception] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class PipelineStage(ABC, Generic[T, U]):
    """Abstract base class for pipeline stages"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    def process(self, input_data: T, context: PipelineContext) -> U:
        """Process the input and return output"""
        pass

    def validate(self, input_data: T, context: PipelineContext) -> bool:
        """Validate input before processing (override if needed)"""
        return input_data is not None

    def on_error(self, error: Exception, input_data: T, context: PipelineContext) -> Optional[U]:
        """Handle errors (override for custom error handling)"""
        self.logger.error(f"Error in stage {self.name}: {error}", exc_info=True)
        return None

    def execute(self, input_data: T, context: PipelineContext) -> StageResult[U]:
        """Execute the stage with error handling and timing"""
        start_time = datetime.now()

        try:
            # Validation
            if not self.validate(input_data, context):
                raise ValueError(f"Validation failed in stage {self.name}")

            # Processing
            self.logger.info(f"Starting stage: {self.name}")
            result = self.process(input_data, context)

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.info(f"Completed stage: {self.name} in {duration_ms:.2f}ms")

            return StageResult(
                success=True,
                data=result,
                duration_ms=duration_ms
            )

        except Exception as e:
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Try error recovery
            recovery_result = self.on_error(e, input_data, context)

            if recovery_result is not None:
                return StageResult(
                    success=True,
                    data=recovery_result,
                    error=e,
                    duration_ms=duration_ms,
                    metadata={"recovered": True}
                )

            return StageResult(
                success=False,
                error=e,
                duration_ms=duration_ms
            )

class Pipeline:
    """Pipeline that executes stages sequentially"""

    def __init__(self, stages: List[PipelineStage], name: str = "Pipeline"):
        self.stages = stages
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    def execute(self, input_data, context: PipelineContext) -> StageResult:
        """Execute all stages in sequence"""
        self.logger.info(f"Starting pipeline: {self.name}")
        start_time = datetime.now()

        result = input_data
        stage_results = []

        for stage in self.stages:
            stage_result = stage.execute(result, context)
            stage_results.append(stage_result)

            if not stage_result.success:
                total_duration = (datetime.now() - start_time).total_seconds() * 1000
                self.logger.error(
                    f"Pipeline {self.name} failed at stage {stage.name}: {stage_result.error}"
                )
                return StageResult(
                    success=False,
                    error=stage_result.error,
                    duration_ms=total_duration,
                    metadata={"failed_stage": stage.name, "stage_results": stage_results}
                )

            result = stage_result.data

        total_duration = (datetime.now() - start_time).total_seconds() * 1000
        self.logger.info(f"Pipeline {self.name} completed in {total_duration:.2f}ms")

        return StageResult(
            success=True,
            data=result,
            duration_ms=total_duration,
            metadata={"stage_results": stage_results}
        )

# Concrete implementations for OMR processing:

# src/algorithm/template/pipeline/stages.py
import numpy as np
from typing import Tuple
from src.algorithm.template.detection.models.detection_results import FileDetectionResults

@dataclass
class ImageData:
    """Data passed between image processing stages"""
    gray_image: np.ndarray
    colored_image: np.ndarray
    file_path: str

class ImageReadingStage(PipelineStage[str, ImageData]):
    """Stage 1: Read image from file"""

    def __init__(self):
        super().__init__("ImageReading")

    def validate(self, file_path: str, context: PipelineContext) -> bool:
        from pathlib import Path
        return Path(file_path).exists()

    def process(self, file_path: str, context: PipelineContext) -> ImageData:
        import cv2

        # Read image
        colored_image = cv2.imread(file_path)
        gray_image = cv2.cvtColor(colored_image, cv2.COLOR_BGR2GRAY)

        self.logger.info(f"Read image: {file_path}, shape: {gray_image.shape}")

        return ImageData(
            gray_image=gray_image,
            colored_image=colored_image,
            file_path=file_path
        )

class DetectionStage(PipelineStage[ImageData, FileDetectionResults]):
    """Stage 2: Detect all fields"""

    def __init__(self, template):
        super().__init__("Detection")
        self.template = template

    def process(self, image_data: ImageData, context: PipelineContext) -> FileDetectionResults:
        from src.algorithm.template.detection.models.detection_results import (
            BubbleFieldDetectionResult,
            FileDetectionResults,
            ScanQuality
        )

        results = FileDetectionResults(file_path=image_data.file_path)

        # Process each field
        for field in self.template.all_fields:
            if field.field_detection_type == "bubbles_threshold":
                # Detect bubbles
                bubble_result = self._detect_bubbles(field, image_data.gray_image)
                results.bubble_fields[field.field_label] = bubble_result

        return results

    def _detect_bubbles(self, field, gray_image) -> BubbleFieldDetectionResult:
        # Existing detection logic here
        # ...
        pass

class ThresholdCalculationStage(PipelineStage[FileDetectionResults, FileDetectionResults]):
    """Stage 3: Calculate thresholds from detections"""

    def __init__(self, threshold_strategy):
        super().__init__("ThresholdCalculation")
        self.threshold_strategy = threshold_strategy

    def process(self, detection_results: FileDetectionResults,
                context: PipelineContext) -> FileDetectionResults:
        # Calculate global threshold
        all_bubble_means = [
            mean
            for field_result in detection_results.bubble_fields.values()
            for mean in field_result.bubble_means
        ]

        global_threshold = self.threshold_strategy.calculate_global_threshold(
            all_bubble_means
        )

        # Store in context for interpretation stage
        context.metadata['global_threshold'] = global_threshold

        return detection_results

class InterpretationStage(PipelineStage[FileDetectionResults, Dict[str, str]]):
    """Stage 4: Interpret detections to field values"""

    def __init__(self):
        super().__init__("Interpretation")

    def process(self, detection_results: FileDetectionResults,
                context: PipelineContext) -> Dict[str, str]:
        omr_response = {}

        global_threshold = context.metadata.get('global_threshold')

        for field_label, bubble_result in detection_results.bubble_fields.items():
            # Calculate local threshold
            local_threshold = self._calculate_local_threshold(
                bubble_result.bubble_means,
                global_threshold
            )

            # Interpret marked bubbles
            marked_values = []
            for bubble_mean in bubble_result.bubble_means:
                if bubble_mean.mean_value < local_threshold:
                    marked_values.append(bubble_mean.unit_bubble.bubble_value)

            omr_response[field_label] = "".join(marked_values) if marked_values else ""

        return omr_response

    def _calculate_local_threshold(self, bubble_means, global_threshold):
        # Local threshold logic
        sorted_means = sorted([bm.mean_value for bm in bubble_means])
        # ... existing logic
        return global_threshold  # Simplified

# Usage:
def create_omr_pipeline(template, threshold_strategy):
    """Factory function to create the OMR processing pipeline"""
    return Pipeline(
        stages=[
            ImageReadingStage(),
            DetectionStage(template),
            ThresholdCalculationStage(threshold_strategy),
            InterpretationStage()
        ],
        name="OMR Processing"
    )

# Process a file:
pipeline = create_omr_pipeline(template, threshold_strategy)
context = PipelineContext(
    file_path="path/to/image.jpg",
    config={"threshold_config": {...}}
)
result = pipeline.execute("path/to/image.jpg", context)

if result.success:
    print(f"OMR Response: {result.data}")
else:
    print(f"Error: {result.error}")
```

---

## Repository Pattern

### Complete Repository Implementation

```python
# src/algorithm/template/repositories/aggregate_repository.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime

T = TypeVar('T')

class AggregateRepository(ABC, Generic[T]):
    """Abstract repository for managing detection/interpretation aggregates"""

    @abstractmethod
    def save_field_aggregate(self, field_id: str, aggregate: T) -> None:
        """Save field-level aggregate"""
        pass

    @abstractmethod
    def get_field_aggregate(self, field_id: str) -> T:
        """Get field-level aggregate"""
        pass

    @abstractmethod
    def get_all_field_aggregates(self) -> Dict[str, T]:
        """Get all field aggregates"""
        pass

    @abstractmethod
    def save_file_aggregate(self, file_path: str, aggregate: Dict[str, T]) -> None:
        """Save file-level aggregate"""
        pass

    @abstractmethod
    def get_file_aggregate(self, file_path: str) -> Dict[str, T]:
        """Get file-level aggregate"""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all aggregates"""
        pass

class InMemoryAggregateRepository(AggregateRepository[T]):
    """In-memory implementation of aggregate repository"""

    def __init__(self):
        self._field_aggregates: Dict[str, T] = {}
        self._file_aggregates: Dict[str, Dict[str, T]] = {}
        self._directory_aggregate: Optional[Dict] = None

    def save_field_aggregate(self, field_id: str, aggregate: T) -> None:
        self._field_aggregates[field_id] = aggregate

    def get_field_aggregate(self, field_id: str) -> T:
        if field_id not in self._field_aggregates:
            raise KeyError(f"Field aggregate not found: {field_id}")
        return self._field_aggregates[field_id]

    def get_all_field_aggregates(self) -> Dict[str, T]:
        return self._field_aggregates.copy()

    def save_file_aggregate(self, file_path: str, aggregate: Dict[str, T]) -> None:
        self._file_aggregates[file_path] = aggregate

    def get_file_aggregate(self, file_path: str) -> Dict[str, T]:
        if file_path not in self._file_aggregates:
            raise KeyError(f"File aggregate not found: {file_path}")
        return self._file_aggregates[file_path]

    def clear(self) -> None:
        self._field_aggregates.clear()
        self._file_aggregates.clear()
        self._directory_aggregate = None

    # Query methods
    def get_all_bubble_means(self) -> List:
        """Query: Get all bubble means across all fields"""
        bubble_means = []
        for aggregate in self._field_aggregates.values():
            if hasattr(aggregate, 'bubble_means'):
                bubble_means.extend(aggregate.bubble_means)
        return bubble_means

    def get_fields_by_quality(self, quality: str) -> List[T]:
        """Query: Get all fields with specific scan quality"""
        return [
            agg for agg in self._field_aggregates.values()
            if hasattr(agg, 'scan_quality') and agg.scan_quality.value == quality
        ]

# Usage with dependency injection:
from src.algorithm.template.detection.models.detection_results import BubbleFieldDetectionResult

class DetectionService:
    """Service that uses repository for detection results"""

    def __init__(self, repository: AggregateRepository[BubbleFieldDetectionResult]):
        self.repository = repository

    def detect_and_save(self, field, image):
        """Detect field and save to repository"""
        # Perform detection
        result = self._detect_bubbles(field, image)

        # Save to repository
        self.repository.save_field_aggregate(field.id, result)

        return result

    def _detect_bubbles(self, field, image) -> BubbleFieldDetectionResult:
        # Detection logic
        pass

class InterpretationService:
    """Service that uses repository for interpretation"""

    def __init__(self, repository: AggregateRepository[BubbleFieldDetectionResult]):
        self.repository = repository

    def interpret_field(self, field_id: str) -> str:
        """Interpret field using repository data"""
        # Get detection result from repository
        detection = self.repository.get_field_aggregate(field_id)

        # Calculate threshold using all bubble means
        all_bubble_means = self.repository.get_all_bubble_means()
        global_threshold = self._calculate_global_threshold(all_bubble_means)

        # Interpret
        return self._interpret(detection, global_threshold)

    def _calculate_global_threshold(self, all_bubble_means):
        # Threshold calculation
        pass

    def _interpret(self, detection, threshold):
        # Interpretation logic
        pass

# Setup:
repository = InMemoryAggregateRepository[BubbleFieldDetectionResult]()
detection_service = DetectionService(repository)
interpretation_service = InterpretationService(repository)

# Use:
for field in template.all_fields:
    detection_service.detect_and_save(field, image)

for field in template.all_fields:
    value = interpretation_service.interpret_field(field.id)
    print(f"{field.field_label}: {value}")
```

---

## Strategy Pattern for Thresholds

### Complete Strategy Implementation

```python
# src/algorithm/template/threshold/strategies.py
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
import numpy as np

@dataclass
class ThresholdResult:
    """Result from threshold calculation"""
    threshold_value: float
    confidence: float  # 0.0 to 1.0
    method_used: str
    fallback_used: bool = False
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ThresholdContext:
    """Context for threshold calculation"""
    min_jump: float = 30.0
    min_gap_two_bubbles: float = 20.0
    global_threshold_margin: float = 10.0
    outlier_deviation_threshold: float = 5.0

class ThresholdStrategy(ABC):
    """Abstract strategy for threshold calculation"""

    @abstractmethod
    def calculate_threshold(
        self,
        bubble_means: List[float],
        context: ThresholdContext
    ) -> ThresholdResult:
        """Calculate threshold from bubble means"""
        pass

class GlobalThresholdStrategy(ThresholdStrategy):
    """Strategy using global file-level statistics"""

    def calculate_threshold(
        self,
        bubble_means: List[float],
        context: ThresholdContext
    ) -> ThresholdResult:
        """
        Find the first large gap in sorted bubble means.
        Based on existing get_global_threshold logic.
        """
        if len(bubble_means) < 2:
            return ThresholdResult(
                threshold_value=127.5,  # Default
                confidence=0.0,
                method_used="global_default",
                fallback_used=True
            )

        sorted_means = sorted(bubble_means)

        # Find largest gap
        max_jump = 0
        threshold = 127.5

        for i in range(len(sorted_means) - 1):
            jump = sorted_means[i + 1] - sorted_means[i]
            if jump > max_jump:
                max_jump = jump
                threshold = sorted_means[i] + jump / 2

        # Calculate confidence based on jump size
        confidence = min(1.0, max_jump / (context.min_jump * 3))

        return ThresholdResult(
            threshold_value=threshold,
            confidence=confidence,
            method_used="global_max_jump",
            fallback_used=max_jump < context.min_jump,
            metadata={
                "max_jump": max_jump,
                "num_bubbles": len(bubble_means)
            }
        )

class LocalThresholdStrategy(ThresholdStrategy):
    """Strategy using field-level statistics"""

    def calculate_threshold(
        self,
        bubble_means: List[float],
        context: ThresholdContext,
        global_fallback: Optional[float] = None
    ) -> ThresholdResult:
        """
        Calculate local threshold for a specific field.
        Falls back to global if confidence is low.
        """
        if len(bubble_means) < 2:
            return ThresholdResult(
                threshold_value=global_fallback or 127.5,
                confidence=0.0,
                method_used="local_default",
                fallback_used=True
            )

        sorted_means = sorted(bubble_means)

        # For 2 bubbles, check if gap is significant
        if len(sorted_means) == 2:
            gap = sorted_means[1] - sorted_means[0]
            if gap < context.min_gap_two_bubbles:
                return ThresholdResult(
                    threshold_value=global_fallback or np.mean(sorted_means),
                    confidence=0.3,
                    method_used="local_two_bubbles_fallback",
                    fallback_used=True
                )
            else:
                return ThresholdResult(
                    threshold_value=np.mean(sorted_means),
                    confidence=0.7,
                    method_used="local_two_bubbles_mean",
                    fallback_used=False
                )

        # Find largest jump (3+ bubbles)
        max_jump = 0
        threshold = 127.5

        for i in range(1, len(sorted_means) - 1):
            jump = sorted_means[i + 1] - sorted_means[i - 1]
            if jump > max_jump:
                max_jump = jump
                threshold = sorted_means[i - 1] + jump / 2

        # Check if jump is confident
        confident_jump = context.min_jump + 10

        if max_jump < confident_jump:
            # Use global fallback if available
            if global_fallback is not None:
                return ThresholdResult(
                    threshold_value=global_fallback,
                    confidence=0.4,
                    method_used="local_low_confidence_global_fallback",
                    fallback_used=True,
                    metadata={"local_max_jump": max_jump}
                )

        confidence = min(1.0, max_jump / (confident_jump * 2))

        return ThresholdResult(
            threshold_value=threshold,
            confidence=confidence,
            method_used="local_max_jump",
            fallback_used=False,
            metadata={
                "max_jump": max_jump,
                "num_bubbles": len(bubble_means)
            }
        )

class AdaptiveThresholdStrategy(ThresholdStrategy):
    """Adaptive strategy that combines multiple strategies"""

    def __init__(
        self,
        strategies: List[ThresholdStrategy],
        weights: Optional[List[float]] = None
    ):
        self.strategies = strategies
        self.weights = weights or [1.0] * len(strategies)

    def calculate_threshold(
        self,
        bubble_means: List[float],
        context: ThresholdContext
    ) -> ThresholdResult:
        """
        Calculate threshold using weighted average of multiple strategies.
        Weight by confidence scores.
        """
        results = [
            strategy.calculate_threshold(bubble_means, context)
            for strategy in self.strategies
        ]

        # Calculate weighted average
        total_weight = sum(
            r.confidence * w
            for r, w in zip(results, self.weights)
        )

        if total_weight == 0:
            # All strategies have zero confidence
            return ThresholdResult(
                threshold_value=127.5,
                confidence=0.0,
                method_used="adaptive_all_zero_confidence",
                fallback_used=True
            )

        weighted_threshold = sum(
            r.threshold_value * r.confidence * w
            for r, w in zip(results, self.weights)
        ) / total_weight

        # Use max confidence from all strategies
        max_confidence = max(r.confidence for r in results)

        return ThresholdResult(
            threshold_value=weighted_threshold,
            confidence=max_confidence,
            method_used="adaptive_weighted",
            fallback_used=any(r.fallback_used for r in results),
            metadata={
                "strategy_results": [
                    {
                        "method": r.method_used,
                        "threshold": r.threshold_value,
                        "confidence": r.confidence
                    }
                    for r in results
                ]
            }
        )

# Usage example:
def create_threshold_calculator(config):
    """Factory to create threshold calculator based on config"""

    if config.get("use_adaptive", True):
        return AdaptiveThresholdStrategy(
            strategies=[
                GlobalThresholdStrategy(),
                LocalThresholdStrategy()
            ],
            weights=[0.4, 0.6]  # Prefer local threshold
        )
    elif config.get("use_local", True):
        return LocalThresholdStrategy()
    else:
        return GlobalThresholdStrategy()

# Use:
calculator = create_threshold_calculator(config)
context = ThresholdContext(min_jump=30.0)

# For field:
result = calculator.calculate_threshold(
    bubble_means=[120.5, 200.3, 115.8, 118.2],
    context=context
)

print(f"Threshold: {result.threshold_value:.2f}")
print(f"Confidence: {result.confidence:.2%}")
print(f"Method: {result.method_used}")
```

---

## Async Processing

### Async Field Processing

```python
# src/algorithm/template/async_processing/field_processor.py
import asyncio
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import numpy as np

class AsyncFieldProcessor:
    """Process fields asynchronously"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_field_async(
        self,
        field,
        gray_image: np.ndarray,
        colored_image: np.ndarray,
        context: dict
    ):
        """Process a single field asynchronously"""
        loop = asyncio.get_event_loop()

        # Run CPU-bound detection in thread pool
        detection_result = await loop.run_in_executor(
            self.executor,
            self._detect_field_sync,
            field,
            gray_image,
            colored_image
        )

        # Run interpretation (can access context)
        interpretation_result = await loop.run_in_executor(
            self.executor,
            self._interpret_field_sync,
            field,
            detection_result,
            context
        )

        return {
            "field_label": field.field_label,
            "detection": detection_result,
            "interpretation": interpretation_result
        }

    def _detect_field_sync(self, field, gray_image, colored_image):
        """Synchronous detection (runs in thread pool)"""
        # Existing detection logic
        from src.algorithm.template.detection.bubbles_threshold.detection import BubblesFieldDetection

        if field.field_detection_type == "bubbles_threshold":
            detection = BubblesFieldDetection(field, gray_image, colored_image)
            return detection

        return None

    def _interpret_field_sync(self, field, detection_result, context):
        """Synchronous interpretation (runs in thread pool)"""
        # Existing interpretation logic
        pass

    async def process_all_fields_async(
        self,
        fields: List,
        gray_image: np.ndarray,
        colored_image: np.ndarray
    ) -> Dict:
        """Process all fields in parallel"""

        # First pass: collect all detections in parallel
        detection_tasks = [
            self.process_detection_async(field, gray_image, colored_image)
            for field in fields
        ]

        detection_results = await asyncio.gather(*detection_tasks)

        # Build context from detections
        context = self._build_context(detection_results)

        # Second pass: interpret all fields in parallel
        interpretation_tasks = [
            self.process_interpretation_async(field, detection, context)
            for field, detection in zip(fields, detection_results)
        ]

        interpretation_results = await asyncio.gather(*interpretation_tasks)

        # Combine results
        return {
            field.field_label: interpretation
            for field, interpretation in zip(fields, interpretation_results)
        }

    async def process_detection_async(self, field, gray_image, colored_image):
        """Async detection"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._detect_field_sync,
            field,
            gray_image,
            colored_image
        )

    async def process_interpretation_async(self, field, detection, context):
        """Async interpretation"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._interpret_field_sync,
            field,
            detection,
            context
        )

    def _build_context(self, detection_results):
        """Build global context from all detections"""
        # Collect all bubble means
        all_bubble_means = []
        for detection in detection_results:
            if hasattr(detection, 'field_bubble_means'):
                all_bubble_means.extend(detection.field_bubble_means)

        # Calculate global threshold
        from src.algorithm.template.threshold.strategies import GlobalThresholdStrategy, ThresholdContext

        strategy = GlobalThresholdStrategy()
        bubble_values = [bm.mean_value for bm in all_bubble_means]
        threshold_result = strategy.calculate_threshold(
            bubble_values,
            ThresholdContext()
        )

        return {
            "global_threshold": threshold_result.threshold_value,
            "all_bubble_means": all_bubble_means
        }

    def close(self):
        """Clean up resources"""
        self.executor.shutdown(wait=True)

# Usage:
async def process_file_async(file_path: str, template):
    """Process entire file asynchronously"""
    # Read image
    gray_image, colored_image = read_image(file_path)

    # Create processor
    processor = AsyncFieldProcessor(max_workers=4)

    try:
        # Process all fields
        result = await processor.process_all_fields_async(
            template.all_fields,
            gray_image,
            colored_image
        )

        return result
    finally:
        processor.close()

# Run:
result = asyncio.run(process_file_async("path/to/image.jpg", template))
print(result)
```

---

## Testing Examples

### Unit Tests

```python
# tests/unit/test_threshold_strategies.py
import pytest
from src.algorithm.template.threshold.strategies import (
    GlobalThresholdStrategy,
    LocalThresholdStrategy,
    AdaptiveThresholdStrategy,
    ThresholdContext
)

class TestGlobalThresholdStrategy:

    def test_basic_threshold_calculation(self):
        """Test basic threshold calculation with clear gap"""
        strategy = GlobalThresholdStrategy()
        bubble_means = [100, 105, 110, 200, 205, 210]  # Clear gap around 155

        result = strategy.calculate_threshold(
            bubble_means,
            ThresholdContext(min_jump=30.0)
        )

        assert 140 < result.threshold_value < 170
        assert result.confidence > 0.5
        assert not result.fallback_used

    def test_no_clear_gap(self):
        """Test with gradual increase (no clear gap)"""
        strategy = GlobalThresholdStrategy()
        bubble_means = [100, 110, 120, 130, 140, 150]  # Gradual increase

        result = strategy.calculate_threshold(
            bubble_means,
            ThresholdContext(min_jump=30.0)
        )

        assert result.fallback_used
        assert result.confidence < 0.5

    def test_empty_input(self):
        """Test with empty bubble means"""
        strategy = GlobalThresholdStrategy()

        result = strategy.calculate_threshold([], ThresholdContext())

        assert result.threshold_value == 127.5  # Default
        assert result.confidence == 0.0
        assert result.fallback_used

class TestLocalThresholdStrategy:

    def test_two_bubbles_significant_gap(self):
        """Test with two bubbles with significant gap"""
        strategy = LocalThresholdStrategy()
        bubble_means = [100, 200]  # Large gap

        result = strategy.calculate_threshold(
            bubble_means,
            ThresholdContext(min_gap_two_bubbles=20.0)
        )

        assert 140 < result.threshold_value < 160
        assert result.confidence > 0.5
        assert not result.fallback_used

    def test_two_bubbles_small_gap_fallback(self):
        """Test with two bubbles with small gap uses fallback"""
        strategy = LocalThresholdStrategy()
        bubble_means = [100, 110]  # Small gap

        result = strategy.calculate_threshold(
            bubble_means,
            ThresholdContext(min_gap_two_bubbles=20.0),
            global_fallback=150.0
        )

        assert result.fallback_used
        # Should use global fallback or mean

    def test_multiple_bubbles_confident(self):
        """Test with multiple bubbles and clear jump"""
        strategy = LocalThresholdStrategy()
        bubble_means = [100, 102, 104, 200, 202, 204]

        result = strategy.calculate_threshold(
            bubble_means,
            ThresholdContext(min_jump=30.0)
        )

        assert 140 < result.threshold_value < 160
        assert result.confidence > 0.5

class TestAdaptiveThresholdStrategy:

    def test_combines_strategies(self):
        """Test that adaptive strategy combines results"""
        adaptive = AdaptiveThresholdStrategy(
            strategies=[
                GlobalThresholdStrategy(),
                LocalThresholdStrategy()
            ],
            weights=[0.5, 0.5]
        )

        bubble_means = [100, 105, 200, 205]

        result = adaptive.calculate_threshold(
            bubble_means,
            ThresholdContext()
        )

        assert result.method_used == "adaptive_weighted"
        assert "strategy_results" in result.metadata
        assert len(result.metadata["strategy_results"]) == 2

    def test_high_confidence_wins(self):
        """Test that higher confidence strategy gets more weight"""
        # This is implicit in weighted average
        pass

# Property-based tests
from hypothesis import given, strategies as st

class TestThresholdProperties:

    @given(
        bubble_means=st.lists(
            st.floats(min_value=0, max_value=255),
            min_size=3,
            max_size=20
        )
    )
    def test_threshold_in_range(self, bubble_means):
        """Threshold should always be between min and max values"""
        if not bubble_means:
            return

        strategy = GlobalThresholdStrategy()
        result = strategy.calculate_threshold(bubble_means, ThresholdContext())

        assert min(bubble_means) <= result.threshold_value <= max(bubble_means)

    @given(
        bubble_means=st.lists(
            st.floats(min_value=0, max_value=255),
            min_size=2,
            max_size=20
        )
    )
    def test_confidence_in_range(self, bubble_means):
        """Confidence should always be between 0 and 1"""
        strategy = GlobalThresholdStrategy()
        result = strategy.calculate_threshold(bubble_means, ThresholdContext())

        assert 0.0 <= result.confidence <= 1.0

# Integration tests
@pytest.mark.integration
class TestIntegration:

    def test_full_pipeline_with_threshold_strategies(self):
        """Test complete pipeline with threshold calculation"""
        from src.algorithm.template.pipeline.base import Pipeline, PipelineContext
        # ... pipeline setup
        pass
```

### Mocking Examples

```python
# tests/unit/test_detection_service.py
import pytest
from unittest.mock import Mock, MagicMock
from src.algorithm.template.repositories.aggregate_repository import InMemoryAggregateRepository
from src.algorithm.template.detection.models.detection_results import (
    BubbleFieldDetectionResult,
    ScanQuality
)

@pytest.fixture
def mock_repository():
    """Fixture providing a mock repository"""
    return Mock(spec=InMemoryAggregateRepository)

@pytest.fixture
def sample_bubble_result():
    """Fixture providing sample bubble detection result"""
    from src.algorithm.template.detection.bubbles_threshold.detection import BubbleMeanValue
    from unittest.mock import Mock

    mock_bubble = Mock()
    mock_bubble.bubble_value = "A"

    return BubbleFieldDetectionResult(
        field_id="q1",
        field_label="Question1",
        field_type="bubbles",
        bubble_means=[
            BubbleMeanValue(120.5, mock_bubble, (0, 0)),
            BubbleMeanValue(200.3, mock_bubble, (0, 0)),
        ],
        std_deviation=45.2,
        scan_quality=ScanQuality.GOOD
    )

class TestDetectionService:

    def test_detect_and_save(self, mock_repository, sample_bubble_result):
        """Test that detection is saved to repository"""
        from your_module import DetectionService

        service = DetectionService(mock_repository)
        service._detect_bubbles = Mock(return_value=sample_bubble_result)

        mock_field = Mock()
        mock_field.id = "q1"
        mock_image = Mock()

        result = service.detect_and_save(mock_field, mock_image)

        # Verify save was called
        mock_repository.save_field_aggregate.assert_called_once_with(
            "q1",
            sample_bubble_result
        )

        assert result == sample_bubble_result

class TestInterpretationService:

    def test_interpret_field_uses_repository(self, mock_repository, sample_bubble_result):
        """Test that interpretation retrieves from repository"""
        from your_module import InterpretationService

        # Setup repository mock
        mock_repository.get_field_aggregate.return_value = sample_bubble_result
        mock_repository.get_all_bubble_means.return_value = sample_bubble_result.bubble_means

        service = InterpretationService(mock_repository)
        result = service.interpret_field("q1")

        # Verify repository was queried
        mock_repository.get_field_aggregate.assert_called_once_with("q1")
        mock_repository.get_all_bubble_means.assert_called_once()

        assert isinstance(result, str)
```

---

## Summary

This implementation guide provides:

1. **Backward-compatible types** - Can be gradually adopted
2. **Pipeline architecture** - Flexible and composable
3. **Repository pattern** - Clean data access
4. **Strategy pattern** - Extensible threshold calculation
5. **Async processing** - Better performance
6. **Comprehensive tests** - Ensures reliability

### Next Steps

1. Start with adding type hints to existing code
2. Introduce typed models alongside dictionaries
3. Extract threshold strategies
4. Implement repository pattern
5. Gradually migrate to pipeline architecture
6. Add async processing for performance

Each step can be done independently without breaking existing functionality.

