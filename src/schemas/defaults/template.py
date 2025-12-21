from src.schemas.models.template import (
    AlignmentConfig,
    AlignmentMarginsConfig,
    OutputColumnsConfig,
    SortFilesConfig,
    TemplateConfig,
)

# Create default template config instance
TEMPLATE_DEFAULTS = TemplateConfig(
    alignment=AlignmentConfig(
        margins=AlignmentMarginsConfig(top=0, bottom=0, left=0, right=0),
        maxDisplacement=10,
    ),
    conditionalSets=[],
    customLabels={},
    customBubbleFieldTypes={},
    emptyValue="",
    fieldBlocks={},
    fieldBlocksOffset=[0, 0],
    outputColumns=OutputColumnsConfig(
        customOrder=[],
        sortType="ALPHANUMERIC",
        sortOrder="ASC",
    ),
    preProcessors=[],
    processingImageShape=[900, 650],
    sortFiles=SortFilesConfig(enabled=False),
)
