"""Tests for FileOrganizerProcessor."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.processors.base import ProcessingContext
from src.processors.organization.processor import FileOrganizerProcessor
from src.schemas.models.config import FileGroupingConfig, GroupingRule


class TestFileOrganizerProcessor:
    """Test suite for FileOrganizerProcessor."""

    def test_processor_name(self):
        """Test that processor returns correct name."""
        config = FileGroupingConfig(enabled=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = FileOrganizerProcessor(config, Path(tmpdir))
            assert processor.get_name() == "FileOrganizer"

    def test_disabled_processor_does_nothing(self):
        """Test that disabled processor doesn't collect results."""
        config = FileGroupingConfig(enabled=False)
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = FileOrganizerProcessor(config, Path(tmpdir))

            context = ProcessingContext(
                file_path=Path("test.jpg"),
                gray_image=None,
                colored_image=None,
                template=MagicMock(),
            )

            result = processor.process(context)

            assert result is context  # Returns unchanged context
            assert len(processor.results) == 0  # No results collected

    def test_enabled_processor_collects_results(self):
        """Test that enabled processor collects results from processing."""
        config = FileGroupingConfig(enabled=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = FileOrganizerProcessor(config, Path(tmpdir))

            context = ProcessingContext(
                file_path=Path("test.jpg"),
                gray_image=None,
                colored_image=None,
                template=MagicMock(),
            )
            context.omr_response = {"roll": "12345"}
            context.score = 95
            context.is_multi_marked = False
            context.metadata = {"output_path": "/path/to/output.jpg"}

            processor.process(context)

            assert len(processor.results) == 1
            assert processor.results[0]["score"] == 95
            assert processor.results[0]["omr_response"] == {"roll": "12345"}

    def test_rule_priority_ordering(self):
        """Test that rules are sorted by priority."""
        rules = [
            GroupingRule(
                name="Low Priority",
                priority=3,
                destination_pattern="low/{roll}",
                matcher={"formatString": "{roll}", "matchRegex": ".*"},
            ),
            GroupingRule(
                name="High Priority",
                priority=1,
                destination_pattern="high/{roll}",
                matcher={"formatString": "{roll}", "matchRegex": ".*"},
            ),
            GroupingRule(
                name="Medium Priority",
                priority=2,
                destination_pattern="med/{roll}",
                matcher={"formatString": "{roll}", "matchRegex": ".*"},
            ),
        ]
        config = FileGroupingConfig(enabled=True, rules=rules)

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = FileOrganizerProcessor(config, Path(tmpdir))

            # Check rules are sorted by priority
            assert processor.config.rules[0].name == "High Priority"
            assert processor.config.rules[1].name == "Medium Priority"
            assert processor.config.rules[2].name == "Low Priority"

    def test_rule_matching_uses_first_match(self):
        """Test that first matching rule by priority is used."""
        rules = [
            GroupingRule(
                name="Specific Match",
                priority=1,
                destination_pattern="specific/{roll}",
                matcher={"formatString": "{roll}", "matchRegex": "^123.*"},
            ),
            GroupingRule(
                name="General Match",
                priority=2,
                destination_pattern="general/{roll}",
                matcher={"formatString": "{roll}", "matchRegex": ".*"},
            ),
        ]
        config = FileGroupingConfig(enabled=True, rules=rules)

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = FileOrganizerProcessor(config, Path(tmpdir))

            fields = {"roll": "12345"}
            matched = processor._find_matching_rule(fields)  # noqa: SLF001

            assert matched is not None
            assert matched.name == "Specific Match"

    def test_rule_matching_falls_to_second_if_first_doesnt_match(self):
        """Test that second rule is used if first doesn't match."""
        rules = [
            GroupingRule(
                name="No Match",
                priority=1,
                destination_pattern="nomatch/{roll}",
                matcher={"formatString": "{roll}", "matchRegex": "^999.*"},
            ),
            GroupingRule(
                name="Should Match",
                priority=2,
                destination_pattern="match/{roll}",
                matcher={"formatString": "{roll}", "matchRegex": "^123.*"},
            ),
        ]
        config = FileGroupingConfig(enabled=True, rules=rules)

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = FileOrganizerProcessor(config, Path(tmpdir))

            fields = {"roll": "12345"}
            matched = processor._find_matching_rule(fields)  # noqa: SLF001

            assert matched is not None
            assert matched.name == "Should Match"

    def test_no_matching_rule_returns_none(self):
        """Test that no match returns None."""
        rules = [
            GroupingRule(
                name="No Match",
                priority=1,
                destination_pattern="nomatch/{roll}",
                matcher={"formatString": "{roll}", "matchRegex": "^999.*"},
            ),
        ]
        config = FileGroupingConfig(enabled=True, rules=rules)

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = FileOrganizerProcessor(config, Path(tmpdir))

            fields = {"roll": "12345"}
            matched = processor._find_matching_rule(fields)  # noqa: SLF001

            assert matched is None

    def test_finish_processing_with_no_results(self):
        """Test that finish_processing does nothing when no results collected."""
        config = FileGroupingConfig(enabled=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            processor = FileOrganizerProcessor(config, Path(tmpdir))

            # Should not raise any errors
            processor.finish_processing_directory()

            assert len(processor.file_operations) == 0

    def test_finish_processing_creates_organized_dir(self):
        """Test that finish_processing creates organized directory."""
        config = FileGroupingConfig(enabled=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            processor = FileOrganizerProcessor(config, output_dir)

            # Add a mock result
            mock_context = MagicMock()
            mock_context.file_path = Path("test.jpg")
            mock_context.omr_response = {"roll": "12345"}
            mock_context.score = 95
            mock_context.is_multi_marked = False
            mock_context.metadata = {}

            processor.results.append(
                {
                    "context": mock_context,
                    "output_path": None,  # Will be skipped
                    "score": 95,
                    "omr_response": {"roll": "12345"},
                    "is_multi_marked": False,
                }
            )

            processor.finish_processing_directory()

            organized_dir = output_dir / "organized"
            assert organized_dir.exists()
            assert organized_dir.is_dir()

    def test_file_organization_with_default_pattern(self):
        """Test file organization using default pattern."""
        config = FileGroupingConfig(
            enabled=True, default_pattern="ungrouped/{original_name}"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            # Create a mock output file
            test_file = output_dir / "test_output.jpg"
            test_file.write_text("test")

            processor = FileOrganizerProcessor(config, output_dir)

            # Add a result
            mock_context = MagicMock()
            mock_context.file_path = Path("test.jpg")
            mock_context.omr_response = {"roll": "12345"}
            mock_context.score = 95
            mock_context.is_multi_marked = False
            mock_context.metadata = {"output_path": str(test_file)}

            processor.results.append(
                {
                    "context": mock_context,
                    "output_path": str(test_file),
                    "score": 95,
                    "omr_response": {"roll": "12345"},
                    "is_multi_marked": False,
                }
            )

            processor.finish_processing_directory()

            # Check that file was organized (symlink or copy created)
            organized_file = output_dir / "organized" / "ungrouped" / "test_output.jpg"
            assert (
                organized_file.exists() or organized_file.is_symlink()
            )  # Depends on OS

    def test_collision_skip_strategy(self):
        """Test that skip collision strategy skips existing files."""
        rules = [
            GroupingRule(
                name="Test Rule",
                priority=1,
                destination_pattern="output/{roll}",
                matcher={"formatString": "{roll}", "matchRegex": ".*"},
                collision_strategy="skip",
            ),
        ]
        config = FileGroupingConfig(enabled=True, rules=rules)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            test_file = output_dir / "test.jpg"
            test_file.write_text("test")

            # Pre-create the destination file to cause collision
            # The pattern will resolve to "output/12345.jpg" based on roll field
            organized_dir = output_dir / "organized" / "output"
            organized_dir.mkdir(parents=True)
            collision_file = (
                organized_dir / "12345.jpg"
            )  # Updated to match actual pattern output
            collision_file.write_text("existing")

            processor = FileOrganizerProcessor(config, output_dir)

            mock_context = MagicMock()
            mock_context.file_path = Path("test.jpg")
            mock_context.omr_response = {"roll": "12345"}
            mock_context.score = 95
            mock_context.is_multi_marked = False
            mock_context.metadata = {"output_path": str(test_file)}

            processor.results.append(
                {
                    "context": mock_context,
                    "output_path": str(test_file),
                    "score": 95,
                    "omr_response": {"roll": "12345"},
                    "is_multi_marked": False,
                }
            )

            processor.finish_processing_directory()

            # Check that operation was skipped
            skipped = [
                op for op in processor.file_operations if op["action"] == "skipped"
            ]
            assert len(skipped) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
