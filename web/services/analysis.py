from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from web.services.marker import SubjectResult


THRESHOLD = 0.51


@dataclass
class LearningAreaResult:
    name: str
    correct: int
    total: int
    percentage: float
    status: str


@dataclass
class SubjectAnalysis:
    subject: str
    areas: List[LearningAreaResult]


@dataclass
class FullAnalysis:
    subjects: List[SubjectAnalysis]


class AnalysisError(Exception):
    pass


def _normalize_mapping(raw_mapping: Dict) -> Dict[str, Dict[str, List[str]]]:
    if "subjects" in raw_mapping:
        normalized: Dict[str, Dict[str, List[str]]] = {}
        for subject in raw_mapping["subjects"]:
            subject_name = subject.get("name")
            areas = subject.get("learning_areas")
            if not subject_name or not isinstance(areas, dict):
                raise AnalysisError("Invalid subject mapping in concept JSON.")
            normalized[subject_name] = {
                area: list(map(str, questions))
                for area, questions in areas.items()
            }
        return normalized

    if isinstance(raw_mapping, dict):
        return {
            subject: {area: list(map(str, questions)) for area, questions in areas.items()}
            for subject, areas in raw_mapping.items()
            if isinstance(areas, dict)
        }

    raise AnalysisError("Concept mapping JSON must be an object.")


def _subject_result_map(subjects: Iterable["SubjectResult"]) -> Dict[str, "SubjectResult"]:
    return {subject.subject: subject for subject in subjects}


def analyze_results(
    subject_results: Iterable["SubjectResult"],
    concept_mapping: Dict,
) -> FullAnalysis:
    mapping = _normalize_mapping(concept_mapping)
    subject_map = _subject_result_map(subject_results)
    analyses: List[SubjectAnalysis] = []

    for subject_name, areas in mapping.items():
        if subject_name not in subject_map:
            continue
        subject_result = subject_map[subject_name]
        question_map = {q.question_id: q for q in subject_result.questions}
        area_results: List[LearningAreaResult] = []
        for area_name, question_ids in areas.items():
            correct = 0
            total = 0
            for question_id in question_ids:
                if question_id not in question_map:
                    continue
                total += 1
                if question_map[question_id].is_correct:
                    correct += 1
            percentage = (correct / total) if total else 0.0
            status = "Done well" if percentage >= THRESHOLD else "Needs improvement"
            area_results.append(
                LearningAreaResult(
                    name=area_name,
                    correct=correct,
                    total=total,
                    percentage=percentage,
                    status=status,
                )
            )
        analyses.append(SubjectAnalysis(subject=subject_name, areas=area_results))

    return FullAnalysis(subjects=analyses)


def summarize_strengths(analysis: FullAnalysis) -> Tuple[List[str], List[str]]:
    done_well: List[str] = []
    needs_improvement: List[str] = []
    for subject in analysis.subjects:
        for area in subject.areas:
            label = f"{subject.subject} — {area.name}"
            if area.status == "Done well":
                done_well.append(label)
            else:
                needs_improvement.append(label)
    return done_well, needs_improvement
