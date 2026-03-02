"""
Tests for Code Similarity Analyzer.

Tests cover:
- Code normalization (Python, Java, generic)
- Similarity calculation between code pairs
- Full prova analysis with multiple students
- Edge cases (empty code, identical code, single submission)
"""
import pytest
from analyzer import CodeSimilarityAnalyzer


class TestNormalizePython:
    """Tests for Python code normalization."""

    def test_strips_comments(self):
        code = "x = 1  # this is a comment\ny = 2  # another"
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.normalize_code(code)
        assert "#" not in result

    def test_strips_empty_lines(self):
        code = "x = 1\n\n\ny = 2\n\n"
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.normalize_code(code)
        lines = result.strip().split('\n')
        assert all(line.strip() for line in lines)

    def test_normalizes_whitespace(self):
        code = "x   =   1\ny    =    2"
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.normalize_code(code)
        assert "   " not in result

    def test_normalizes_strings(self):
        code = 'print("hello world")\nprint("goodbye")'
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.normalize_code(code)
        assert "hello world" not in result
        assert '"STR"' in result

    def test_normalizes_numbers(self):
        code = "x = 42\ny = 3.14"
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.normalize_code(code)
        assert "42" not in result
        assert "NUM" in result

    def test_skips_docstrings(self):
        code = '"""This is a docstring"""\nx = 1'
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.normalize_code(code)
        assert "docstring" not in result

    def test_empty_code(self):
        analyzer = CodeSimilarityAnalyzer("python")
        assert analyzer.normalize_code("") == ""
        assert analyzer.normalize_code("   ") == ""


class TestNormalizeJava:
    """Tests for Java code normalization."""

    def test_strips_single_line_comments(self):
        code = "int x = 1; // comment\nint y = 2;"
        analyzer = CodeSimilarityAnalyzer("java")
        result = analyzer.normalize_code(code)
        assert "//" not in result

    def test_strips_multiline_comments(self):
        code = "/* block comment\nstill comment */\nint x = 1;"
        analyzer = CodeSimilarityAnalyzer("java")
        result = analyzer.normalize_code(code)
        assert "block comment" not in result
        assert "x" in result

    def test_normalizes_strings(self):
        code = 'System.out.println("hello");'
        analyzer = CodeSimilarityAnalyzer("java")
        result = analyzer.normalize_code(code)
        assert "hello" not in result
        assert '"STR"' in result


class TestNormalizeGeneric:
    """Tests for generic code normalization."""

    def test_handles_unknown_language(self):
        code = "let x = 1; // comment\nlet y = 2;"
        analyzer = CodeSimilarityAnalyzer("javascript")
        result = analyzer.normalize_code(code)
        assert "//" not in result

    def test_strips_hash_comments(self):
        code = "x = 1 # comment\ny = 2"
        analyzer = CodeSimilarityAnalyzer("ruby")
        result = analyzer.normalize_code(code)
        assert "comment" not in result


class TestCalculateSimilarity:
    """Tests for similarity calculation between code pairs."""

    def test_identical_code(self):
        code = "def hello():\n    print('hello')"
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.calculate_similarity(code, code)
        assert result["text_similarity"] == 100.0
        assert result["normalized_similarity"] == 100.0
        assert result["max_similarity"] == 100.0

    def test_completely_different_code(self):
        code_a = "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)"
        code_b = "class Car:\n    def __init__(self):\n        self.speed = 0\n    def accelerate(self):\n        self.speed += 10"
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.calculate_similarity(code_a, code_b)
        assert result["max_similarity"] < 50.0

    def test_similar_with_renamed_variables(self):
        code_a = "def soma(a, b):\n    resultado = a + b\n    return resultado"
        code_b = "def soma(x, y):\n    total = x + y\n    return total"
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.calculate_similarity(code_a, code_b)
        assert result["max_similarity"] > 60.0
        assert result["normalized_similarity"] > 50.0

    def test_similar_with_different_comments(self):
        code_a = "# Minha solucao\ndef soma(a, b):\n    return a + b"
        code_b = "# Solucao do exercicio\ndef soma(a, b):\n    return a + b"
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.calculate_similarity(code_a, code_b)
        assert result["normalized_similarity"] == 100.0

    def test_empty_code_a(self):
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.calculate_similarity("", "def hello(): pass")
        assert result["text_similarity"] == 0.0
        assert result["max_similarity"] == 0.0

    def test_empty_code_b(self):
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.calculate_similarity("def hello(): pass", "")
        assert result["text_similarity"] == 0.0

    def test_both_empty(self):
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.calculate_similarity("", "")
        assert result["max_similarity"] == 0.0

    def test_similar_with_different_strings(self):
        code_a = 'print("hello world")\nprint("foo")'
        code_b = 'print("goodbye world")\nprint("bar")'
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.calculate_similarity(code_a, code_b)
        assert result["normalized_similarity"] == 100.0

    def test_similarity_is_between_0_and_100(self):
        code_a = "def f(x): return x * 2"
        code_b = "def g(y): return y + 1"
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.calculate_similarity(code_a, code_b)
        assert 0.0 <= result["text_similarity"] <= 100.0
        assert 0.0 <= result["normalized_similarity"] <= 100.0
        assert 0.0 <= result["max_similarity"] <= 100.0


class TestAnalyzeProva:
    """Tests for full prova analysis."""

    def test_basic_prova_analysis(self):
        analyzer = CodeSimilarityAnalyzer("python")

        submissions = {
            1: [
                {"aluno_id": 1, "aluno_nome": "Joao", "aluno_email": "joao@gmail.com",
                 "codigo_submetido": "print('hello')"},
                {"aluno_id": 2, "aluno_nome": "Maria", "aluno_email": "maria@gmail.com",
                 "codigo_submetido": "print('hello')"},
            ]
        }
        titles = {1: "Questao 1"}

        result = analyzer.analyze_prova(submissions, titles, threshold=70.0)

        assert result["total_students"] == 2
        assert len(result["questions"]) == 1
        assert result["questions"][0]["total_pairs"] == 1
        assert result["total_flagged_pairs"] >= 1

    def test_multiple_questions(self):
        analyzer = CodeSimilarityAnalyzer("python")

        submissions = {
            1: [
                {"aluno_id": 1, "aluno_nome": "Joao", "aluno_email": "j@g.com",
                 "codigo_submetido": "print(1)"},
                {"aluno_id": 2, "aluno_nome": "Maria", "aluno_email": "m@g.com",
                 "codigo_submetido": "print(2)"},
            ],
            2: [
                {"aluno_id": 1, "aluno_nome": "Joao", "aluno_email": "j@g.com",
                 "codigo_submetido": "def soma(a,b): return a+b"},
                {"aluno_id": 2, "aluno_nome": "Maria", "aluno_email": "m@g.com",
                 "codigo_submetido": "class Foo: pass"},
            ]
        }
        titles = {1: "Q1", 2: "Q2"}

        result = analyzer.analyze_prova(submissions, titles)

        assert len(result["questions"]) == 2
        assert result["total_students"] == 2

    def test_three_students_creates_three_pairs(self):
        analyzer = CodeSimilarityAnalyzer("python")

        submissions = {
            1: [
                {"aluno_id": 1, "aluno_nome": "A", "aluno_email": "a@g.com",
                 "codigo_submetido": "print(1)"},
                {"aluno_id": 2, "aluno_nome": "B", "aluno_email": "b@g.com",
                 "codigo_submetido": "print(2)"},
                {"aluno_id": 3, "aluno_nome": "C", "aluno_email": "c@g.com",
                 "codigo_submetido": "print(3)"},
            ]
        }
        titles = {1: "Q1"}

        result = analyzer.analyze_prova(submissions, titles)
        assert result["questions"][0]["total_pairs"] == 3
        assert result["total_students"] == 3

    def test_single_submission_no_pairs(self):
        analyzer = CodeSimilarityAnalyzer("python")

        submissions = {
            1: [
                {"aluno_id": 1, "aluno_nome": "A", "aluno_email": "a@g.com",
                 "codigo_submetido": "print(1)"},
            ]
        }
        titles = {1: "Q1"}

        result = analyzer.analyze_prova(submissions, titles)
        assert result["questions"][0]["total_pairs"] == 0
        assert result["total_flagged_pairs"] == 0

    def test_flagged_pairs_above_threshold(self):
        analyzer = CodeSimilarityAnalyzer("python")

        submissions = {
            1: [
                {"aluno_id": 1, "aluno_nome": "A", "aluno_email": "a@g.com",
                 "codigo_submetido": "def soma(a, b):\n    return a + b"},
                {"aluno_id": 2, "aluno_nome": "B", "aluno_email": "b@g.com",
                 "codigo_submetido": "def soma(a, b):\n    return a + b"},
                {"aluno_id": 3, "aluno_nome": "C", "aluno_email": "c@g.com",
                 "codigo_submetido": "class Calculator:\n    def multiply(self, x, y):\n        return x * y"},
            ]
        }
        titles = {1: "Q1"}

        result = analyzer.analyze_prova(submissions, titles, threshold=70.0)

        flagged = [p for p in result["questions"][0]["pairs"] if p["flagged"]]
        assert len(flagged) >= 1
        assert flagged[0]["aluno_a"]["id"] in [1, 2]
        assert flagged[0]["aluno_b"]["id"] in [1, 2]

    def test_pairs_sorted_by_similarity_descending(self):
        analyzer = CodeSimilarityAnalyzer("python")

        submissions = {
            1: [
                {"aluno_id": 1, "aluno_nome": "A", "aluno_email": "a@g.com",
                 "codigo_submetido": "def f(x): return x + 1"},
                {"aluno_id": 2, "aluno_nome": "B", "aluno_email": "b@g.com",
                 "codigo_submetido": "def f(x): return x + 1"},  # Identical to A
                {"aluno_id": 3, "aluno_nome": "C", "aluno_email": "c@g.com",
                 "codigo_submetido": "import os\nos.listdir('.')"},  # Very different
            ]
        }
        titles = {1: "Q1"}

        result = analyzer.analyze_prova(submissions, titles)
        pairs = result["questions"][0]["pairs"]

        for i in range(len(pairs) - 1):
            assert pairs[i]["max_similarity"] >= pairs[i + 1]["max_similarity"]

    def test_empty_submissions_dict(self):
        analyzer = CodeSimilarityAnalyzer("python")
        result = analyzer.analyze_prova({}, {})
        assert result["total_students"] == 0
        assert result["total_flagged_pairs"] == 0
        assert result["questions"] == []

    def test_threshold_customization(self):
        analyzer = CodeSimilarityAnalyzer("python")

        submissions = {
            1: [
                {"aluno_id": 1, "aluno_nome": "A", "aluno_email": "a@g.com",
                 "codigo_submetido": "print('hello')"},
                {"aluno_id": 2, "aluno_nome": "B", "aluno_email": "b@g.com",
                 "codigo_submetido": "print('hello')"},
            ]
        }
        titles = {1: "Q1"}

        result_high = analyzer.analyze_prova(submissions, titles, threshold=100.0)
        result_low = analyzer.analyze_prova(submissions, titles, threshold=0.0)

        assert result_low["total_flagged_pairs"] >= result_high["total_flagged_pairs"]
        assert result_low["threshold_used"] == 0.0
        assert result_high["threshold_used"] == 100.0


class TestJavaSimilarity:
    """Tests for Java code similarity."""

    def test_java_identical_code(self):
        code = "public class Main {\n    public static void main(String[] args) {\n        System.out.println(1);\n    }\n}"
        analyzer = CodeSimilarityAnalyzer("java")
        result = analyzer.calculate_similarity(code, code)
        assert result["text_similarity"] == 100.0

    def test_java_different_comments_same_code(self):
        code_a = "// Minha solucao\npublic int soma(int a, int b) { return a + b; }"
        code_b = "// Solucao copiada\npublic int soma(int a, int b) { return a + b; }"
        analyzer = CodeSimilarityAnalyzer("java")
        result = analyzer.calculate_similarity(code_a, code_b)
        assert result["normalized_similarity"] == 100.0
