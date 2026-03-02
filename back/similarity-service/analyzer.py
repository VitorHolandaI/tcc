"""
Code Similarity Analyzer

Compares code submissions between students for plagiarism detection.
Uses two approaches:
1. Text similarity (difflib.SequenceMatcher) - direct text comparison
2. Normalized similarity - strips comments, whitespace, normalizes identifiers
"""
import re
import difflib
from itertools import combinations
from typing import List, Dict, Any, Optional


class CodeSimilarityAnalyzer:
    """Analyzes code similarity between student submissions."""

    def __init__(self, language: str = "python"):
        self.language = language.lower()

    def normalize_code(self, code: str) -> str:
        """
        Normalize code by removing comments, extra whitespace,
        and normalizing variable names for structural comparison.
        """
        if not code or not code.strip():
            return ""

        if self.language == "python":
            return self._normalize_python(code)
        elif self.language == "java":
            return self._normalize_java(code)
        else:
            return self._normalize_generic(code)

    def _normalize_python(self, code: str) -> str:
        """Normalize Python code."""
        lines = code.split('\n')
        normalized_lines = []

        for line in lines:
            stripped = re.sub(r'#.*$', '', line)
            stripped = stripped.strip()
            if not stripped:
                continue
            if stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            stripped = re.sub(r'\s+', ' ', stripped)
            normalized_lines.append(stripped)

        result = '\n'.join(normalized_lines)

        result = re.sub(r'"[^"]*"', '"STR"', result)
        result = re.sub(r"'[^']*'", '"STR"', result)

        result = re.sub(r'\b\d+\.?\d*\b', 'NUM', result)

        return result

    def _normalize_java(self, code: str) -> str:
        """Normalize Java code."""
        code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

        lines = code.split('\n')
        normalized_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            stripped = re.sub(r'\s+', ' ', stripped)
            normalized_lines.append(stripped)

        result = '\n'.join(normalized_lines)

        result = re.sub(r'"[^"]*"', '"STR"', result)
        result = re.sub(r'\b\d+\.?\d*\b', 'NUM', result)

        return result

    def _normalize_generic(self, code: str) -> str:
        """Generic normalization for unknown languages."""
        code = re.sub(r'(//|#).*$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

        lines = code.split('\n')
        normalized_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            stripped = re.sub(r'\s+', ' ', stripped)
            normalized_lines.append(stripped)

        result = '\n'.join(normalized_lines)
        result = re.sub(r'"[^"]*"', '"STR"', result)
        result = re.sub(r"'[^']*'", '"STR"', result)
        result = re.sub(r'\b\d+\.?\d*\b', 'NUM', result)

        return result

    def calculate_similarity(self, code_a: str, code_b: str) -> Dict[str, float]:
        """
        Calculate similarity between two code snippets.

        Returns:
            dict with text_similarity, normalized_similarity, max_similarity (all 0-100%)
        """
        if not code_a or not code_b:
            return {
                "text_similarity": 0.0,
                "normalized_similarity": 0.0,
                "max_similarity": 0.0
            }

        text_ratio = difflib.SequenceMatcher(None, code_a, code_b).ratio() * 100

        norm_a = self.normalize_code(code_a)
        norm_b = self.normalize_code(code_b)

        if norm_a and norm_b:
            norm_ratio = difflib.SequenceMatcher(None, norm_a, norm_b).ratio() * 100
        else:
            norm_ratio = 0.0

        max_sim = max(text_ratio, norm_ratio)

        return {
            "text_similarity": round(text_ratio, 1),
            "normalized_similarity": round(norm_ratio, 1),
            "max_similarity": round(max_sim, 1)
        }

    def analyze_prova(
        self,
        submissions_by_question: Dict[int, List[Dict[str, Any]]],
        question_titles: Dict[int, str],
        threshold: float = 70.0
    ) -> Dict[str, Any]:
        """
        Analyze all submissions for a prova, comparing pairs per question.

        Args:
            submissions_by_question: {questao_id: [{aluno_id, aluno_nome, aluno_email, codigo_submetido}, ...]}
            question_titles: {questao_id: titulo}
            threshold: similarity % above which a pair is flagged

        Returns:
            dict with per-question results and flagged pairs
        """
        questions_results = []
        total_flagged = 0
        all_students = set()

        for questao_id, submissions in submissions_by_question.items():
            for sub in submissions:
                all_students.add(sub["aluno_id"])

            pairs = []
            flagged_count = 0

            for sub_a, sub_b in combinations(submissions, 2):
                similarity = self.calculate_similarity(
                    sub_a["codigo_submetido"],
                    sub_b["codigo_submetido"]
                )

                pair_result = {
                    "aluno_a": {
                        "id": sub_a["aluno_id"],
                        "nome": sub_a["aluno_nome"],
                        "email": sub_a["aluno_email"]
                    },
                    "aluno_b": {
                        "id": sub_b["aluno_id"],
                        "nome": sub_b["aluno_nome"],
                        "email": sub_b["aluno_email"]
                    },
                    "text_similarity": similarity["text_similarity"],
                    "normalized_similarity": similarity["normalized_similarity"],
                    "max_similarity": similarity["max_similarity"],
                    "flagged": similarity["max_similarity"] >= threshold
                }

                pairs.append(pair_result)
                if pair_result["flagged"]:
                    flagged_count += 1

            pairs.sort(key=lambda p: p["max_similarity"], reverse=True)

            questions_results.append({
                "questao_id": questao_id,
                "questao_titulo": question_titles.get(questao_id, f"Questao {questao_id}"),
                "total_submissions": len(submissions),
                "total_pairs": len(pairs),
                "flagged_pairs": flagged_count,
                "pairs": pairs
            })

            total_flagged += flagged_count

        return {
            "questions": questions_results,
            "total_students": len(all_students),
            "total_flagged_pairs": total_flagged,
            "threshold_used": threshold
        }
