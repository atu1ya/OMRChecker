"""Image processing constants for OMRChecker.

This module contains all magic numbers and constants related to image processing,
thresholds, and computer vision operations. Extracting these values improves:
- Code readability and maintainability
- Easy parameter tuning
- Self-documenting code
"""

# ============================================================================
# Pixel and Color Values
# ============================================================================

# Standard pixel value ranges
PIXEL_VALUE_MIN = 0
PIXEL_VALUE_MAX = 255
PIXEL_VALUE_MID = 127

# Normalization defaults
NORMALIZE_ALPHA_DEFAULT = 0.0  # Min value for normalization
NORMALIZE_BETA_DEFAULT = 255.0  # Max value for normalization

# ============================================================================
# Thresholding Constants
# ============================================================================

# Page detection thresholds
THRESH_PAGE_TRUNCATE_HIGH = 210  # High truncate threshold for page detection
THRESH_PAGE_TRUNCATE_SECONDARY = 200  # Secondary truncate threshold
THRESH_DOT_DEFAULT = 200  # Default threshold for dot line detection

# Canny edge detection
CANNY_THRESHOLD_HIGH = 185  # High threshold for Canny edge detection
CANNY_THRESHOLD_LOW = 55  # Low threshold for Canny edge detection
AUTO_CANNY_SIGMA_DEFAULT = 0.33  # Default sigma for automatic Canny

# ============================================================================
# Contour and Shape Detection
# ============================================================================

# Minimum areas
MIN_PAGE_AREA = 80000  # Minimum area for valid page contour
MIN_MARKER_AREA = 100  # Minimum area for marker detection

# Approximation and simplification
APPROX_POLY_EPSILON_FACTOR = 0.025  # Epsilon factor for polygon approximation
CONTOUR_THICKNESS_STANDARD = 10  # Standard thickness for drawing contours

# Control points
MIN_ALLOWED_CONTROL_POINTS = 4  # Minimum control points for warping
MAX_CONTROL_POINTS_PER_EDGE = 50  # Maximum control points per edge

# ============================================================================
# Morphological Operations
# ============================================================================

# Kernel sizes (width, height)
MORPH_KERNEL_DEFAULT = (10, 10)  # Default morphological kernel size
MORPH_KERNEL_SMALL = (3, 3)  # Small kernel for fine operations
MORPH_KERNEL_LARGE = (20, 20)  # Large kernel for aggressive operations

# Iterations
MORPH_ITERATIONS_STANDARD = 1  # Standard morph iterations
MORPH_ITERATIONS_DOT_OPEN = 3  # Iterations for dot line opening
MORPH_ITERATIONS_AGGRESSIVE = 5  # Aggressive morph iterations

# Kernel multipliers for padding
PADDING_MULTIPLIER_KERNEL = 2.5  # Multiplier for kernel-based padding

# ============================================================================
# Paper/Document Constants
# ============================================================================

# HSV thresholds for paper detection (these would need actual values)
PAPER_VALUE_THRESHOLD = 200  # V channel threshold for paper
PAPER_SATURATION_THRESHOLD = 30  # S channel threshold for paper

# White padding value
WHITE_PADDING_VALUE = 255  # Pure white for padding

# ============================================================================
# Marker Detection Constants
# ============================================================================

# Marker matching and detection
MARKER_MATCH_MIN_THRESHOLD_DEFAULT = 0.7  # Minimum match score for marker
MARKER_RESCALE_RANGE_MIN_DEFAULT = 0.8  # Minimum rescale factor
MARKER_RESCALE_RANGE_MAX_DEFAULT = 1.2  # Maximum rescale factor
MARKER_RESCALE_STEPS_DEFAULT = 10  # Number of rescale steps

# ============================================================================
# Image Quality and Enhancement
# ============================================================================

# CLAHE (Contrast Limited Adaptive Histogram Equalization)
CLAHE_CLIP_LIMIT = 5.0  # Clip limit for CLAHE
CLAHE_TILE_GRID_SIZE = (8, 8)  # Tile grid size for CLAHE

# Gaussian blur
GAUSSIAN_BLUR_KERNEL_DEFAULT = (5, 5)  # Default Gaussian blur kernel
GAUSSIAN_BLUR_SIGMA = 0  # Sigma for Gaussian blur (0 = auto)

# ============================================================================
# Distance and Measurement
# ============================================================================

# Error tolerances
ALLOWED_DISTANCE_ERROR_PERCENTAGE = 5.0  # Allowed error % for distance checks
ROTATION_ANGLE_TOLERANCE_DEGREES = 2.0  # Tolerance for rotation angle

# ============================================================================
# Contour Retrieval Modes
# ============================================================================

# OpenCV version compatibility
CV2_CONTOURS_LENGTH_V2 = 2  # Number of values returned by findContours in CV2
CV2_CONTOURS_LENGTH_V3 = 3  # Number of values returned by findContours in CV3+

# ============================================================================
# Display and Visualization
# ============================================================================

# Transparency and overlay
TRANSPARENCY_OVERLAY_DEFAULT = 0.5  # Default alpha for overlay operations

# Drawing colors (RGB)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (0, 0, 255)  # BGR format
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (255, 0, 0)
COLOR_YELLOW = (0, 255, 255)

# Display image levels
DISPLAY_LEVEL_NONE = 0  # No display
DISPLAY_LEVEL_ERROR_ONLY = 1  # Show only on errors
DISPLAY_LEVEL_LOW = 2  # Low detail display
DISPLAY_LEVEL_MEDIUM = 3  # Medium detail display
DISPLAY_LEVEL_HIGH = 4  # High detail display
DISPLAY_LEVEL_DEBUG = 5  # Full debug display
DISPLAY_LEVEL_VERBOSE = 6  # Verbose debug display

# Images per row for display
DEFAULT_IMAGES_PER_ROW = 4  # Default images per row in stack
DEFAULT_IMAGES_PER_ROW_HIGH_DETAIL = 6  # Images per row for high detail

# ============================================================================
# Statistics and Formatting
# ============================================================================

# Label widths for aligned output
STATS_LABEL_WIDTH = 30  # Width for statistics labels
FILE_PATH_DISPLAY_MAX_LENGTH = 50  # Max length for file path display

# Decimal places for formatting
DECIMAL_PLACES_TIME = 2  # Decimal places for time display
DECIMAL_PLACES_RATE = 1  # Decimal places for rate display
DECIMAL_PLACES_PERCENTAGE = 1  # Decimal places for percentage

# Time conversions
SECONDS_PER_MINUTE = 60  # Seconds in a minute
MILLISECONDS_PER_SECOND = 1000  # Milliseconds in a second

# ============================================================================
# Array and Collection Defaults
# ============================================================================

# Top N contours to consider
TOP_CONTOURS_COUNT = 5  # Number of top contours to analyze

# Rectangle corners count
RECTANGLE_CORNERS_COUNT = 4  # Number of corners in a rectangle

# ============================================================================
# File and Processing
# ============================================================================

# Batch processing
DEFAULT_PARALLEL_WORKERS = 4  # Default number of parallel workers
MAX_FILES_PER_BATCH = 100  # Maximum files to process in one batch

# File size limits (in bytes)
MAX_IMAGE_FILE_SIZE = 50 * 1024 * 1024  # 50MB max for images
MAX_JSON_FILE_SIZE = 10 * 1024 * 1024  # 10MB max for JSON
MAX_CSV_FILE_SIZE = 100 * 1024 * 1024  # 100MB max for CSV

# Image dimension limits
MAX_IMAGE_WIDTH = 10000  # Maximum image width in pixels
MAX_IMAGE_HEIGHT = 10000  # Maximum image height in pixels
MIN_IMAGE_WIDTH = 100  # Minimum useful image width
MIN_IMAGE_HEIGHT = 100  # Minimum useful image height

# ============================================================================
# Processing Dimensions
# ============================================================================

# Default template dimensions
DEFAULT_TEMPLATE_WIDTH = 1200  # Default template width
DEFAULT_TEMPLATE_HEIGHT = 1600  # Default template height

# Bubble dimensions
DEFAULT_BUBBLE_WIDTH = 32  # Default bubble width
DEFAULT_BUBBLE_HEIGHT = 32  # Default bubble height
MIN_BUBBLE_DIMENSION = 10  # Minimum bubble dimension

# ============================================================================
# Mathematical Constants
# ============================================================================

# Ratios and multipliers
GOLDEN_RATIO = 1.618  # Golden ratio for aesthetics
SQRT_TWO = 1.414  # Square root of 2

# Geometric constants
FULL_CIRCLE_DEGREES = 360  # Degrees in a full circle
RIGHT_ANGLE_DEGREES = 90  # Degrees in a right angle
