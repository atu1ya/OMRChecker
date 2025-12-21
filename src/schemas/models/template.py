"""Typed dataclass models for template configuration."""

from dataclasses import dataclass, field

from src.utils.serialization import dataclass_to_dict


@dataclass
class AlignmentMarginsConfig:
    """Configuration for alignment margins."""

    top: int = 0
    bottom: int = 0
    left: int = 0
    right: int = 0


@dataclass
class AlignmentConfig:
    """Configuration for template alignment."""

    margins: AlignmentMarginsConfig = field(default_factory=AlignmentMarginsConfig)
    maxDisplacement: int = 10


@dataclass
class OutputColumnsConfig:
    """Configuration for output columns ordering and sorting."""

    customOrder: list[str] = field(default_factory=list)
    sortType: str = "ALPHANUMERIC"
    sortOrder: str = "ASC"


@dataclass
class SortFilesConfig:
    """Configuration for file sorting."""

    enabled: bool = False


@dataclass
class TemplateConfig:
    """Main template configuration object.

    This represents the structure of template.json files used for OMR sheet
    layout definition and field detection.
    """

    alignment: AlignmentConfig = field(default_factory=AlignmentConfig)
    conditionalSets: list = field(default_factory=list)
    customLabels: dict = field(default_factory=dict)
    customBubbleFieldTypes: dict = field(default_factory=dict)
    emptyValue: str = ""
    fieldBlocks: dict = field(default_factory=dict)
    fieldBlocksOffset: list[int] = field(default_factory=lambda: [0, 0])
    outputColumns: OutputColumnsConfig = field(default_factory=OutputColumnsConfig)
    preProcessors: list = field(default_factory=list)
    processingImageShape: list[int] = field(default_factory=lambda: [900, 650])
    sortFiles: SortFilesConfig = field(default_factory=SortFilesConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "TemplateConfig":
        """Create TemplateConfig from dictionary (typically from JSON).

        Args:
            data: Dictionary containing template configuration data

        Returns:
            TemplateConfig instance with nested dataclasses
        """
        # Parse alignment if present
        alignment_data = data.get("alignment", {})
        alignment = AlignmentConfig(
            margins=AlignmentMarginsConfig(**alignment_data.get("margins", {})),
            maxDisplacement=alignment_data.get("maxDisplacement", 10),
        )

        # Parse outputColumns if present
        output_columns_data = data.get("outputColumns", {})
        output_columns = OutputColumnsConfig(**output_columns_data)

        # Parse sortFiles if present
        sort_files_data = data.get("sortFiles", {})
        sort_files = SortFilesConfig(**sort_files_data)

        return cls(
            alignment=alignment,
            conditionalSets=data.get("conditionalSets", []),
            customLabels=data.get("customLabels", {}),
            customBubbleFieldTypes=data.get("customBubbleFieldTypes", {}),
            emptyValue=data.get("emptyValue", ""),
            fieldBlocks=data.get("fieldBlocks", {}),
            fieldBlocksOffset=data.get("fieldBlocksOffset", [0, 0]),
            outputColumns=output_columns,
            preProcessors=data.get("preProcessors", []),
            processingImageShape=data.get("processingImageShape", [900, 650]),
            sortFiles=sort_files,
        )

    def to_dict(self) -> dict:
        """Convert TemplateConfig to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the template config
        """
        return dataclass_to_dict(self)
