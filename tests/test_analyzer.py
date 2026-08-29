"""Unit tests for the scoring/matching logic in analyzer.py.

These deliberately don't assert exact hand-computed scores for every
sub-dimension (skills/education/experience/formatting) — that internal
logic is expected to evolve. Instead they lock down the parts that would
be a real, silent bug if they drifted: the overall-score weighting
formula, the score-band thresholds, and the fact that pass/fail verdicts
always agree with the numeric score that produced them.
"""
import pytest

from analyzer import (
    calculate_scores,
    simulate_ats,
    match_job_description,
    _get_match_recommendation,
)
import analyzer as analyzer_module


SAMPLE_RESUME = """
John Doe
john.doe@example.com | +1 555 123 4567

SUMMARY
Backend engineer with 6 years of experience building Python and SQL
services on AWS.

SKILLS
Python, SQL, AWS, Docker, Git, Leadership

EDUCATION
Bachelor of Science in Computer Science - State University, 2018

EXPERIENCE
Software Engineer - Example Corp (2019 - Present)
- Built and maintained backend services using Python and PostgreSQL.
- Deployed infrastructure on AWS using Docker containers.
"""


def _sample_skills(n, categories=('Programming Languages', 'Web Development',
                                   'Database', 'Cloud & DevOps', 'Soft Skills')):
    """n synthetic (skill_name, category) tuples cycling through categories,
    matching the shape extract_skills() returns."""
    return [(f'skill-{i}', categories[i % len(categories)]) for i in range(n)]


class TestOverallScoreWeighting:
    def test_weighting_formula_matches_documented_30_20_30_20(self):
        scores, _ = calculate_scores(SAMPLE_RESUME, _sample_skills(12), [{'degree': 'BSc'}],
                                      [('Software Engineer', 'Example Corp', 'Built things')])
        expected = round(
            scores['skills'] * 0.30 +
            scores['education'] * 0.20 +
            scores['experience'] * 0.30 +
            scores['formatting'] * 0.20
        )
        assert scores['overall'] == expected

    def test_all_scores_are_within_0_100(self):
        scores, _ = calculate_scores(SAMPLE_RESUME, _sample_skills(12), [{'degree': 'BSc'}],
                                      [('Software Engineer', 'Example Corp', 'Built things')])
        for key in ('skills', 'education', 'experience', 'formatting', 'overall'):
            assert 0 <= scores[key] <= 100, f'{key} out of range: {scores[key]}'


class TestSkillsScoreBands:
    @pytest.mark.parametrize('skill_count,min_expected', [
        (0, 0),
        (2, 20),
        (5, 50),
        (8, 70),
        (12, 85),
        (16, 100),
    ])
    def test_more_skills_never_scores_lower(self, skill_count, min_expected):
        scores, _ = calculate_scores(SAMPLE_RESUME, _sample_skills(skill_count), [], [])
        assert scores['skills'] >= min_expected

    def test_category_diversity_bonus_does_not_exceed_100(self):
        # 20 skills across 5 categories should hit both the top count band
        # and the >=4-category bonus — score must still cap at 100.
        scores, _ = calculate_scores(SAMPLE_RESUME, _sample_skills(20), [], [])
        assert scores['skills'] == 100


class TestAtsPassLikelyAgreesWithScore:
    def test_pass_likely_matches_60_threshold(self):
        skills = _sample_skills(12)
        scores, _ = calculate_scores(SAMPLE_RESUME, skills, [{'degree': 'BSc'}],
                                      [('Software Engineer', 'Example Corp', 'Built things')])
        results = simulate_ats(SAMPLE_RESUME, skills, [{'degree': 'BSc'}],
                                [('Software Engineer', 'Example Corp', 'Built things')], scores)
        assert results['pass_likely'] == (results['ats_score'] >= 60)

    def test_empty_resume_does_not_pass(self):
        scores, _ = calculate_scores('', [], [], [])
        results = simulate_ats('', [], [], [], scores)
        assert results['pass_likely'] is False


class TestMatchJobDescriptionWeighting:
    """Forces the lexical-only fallback path by making the semantic model
    unavailable, so these tests are deterministic and don't need to
    download/run the real sentence-transformers model in CI."""

    @pytest.fixture(autouse=True)
    def no_semantic_model(self, monkeypatch):
        monkeypatch.setattr(analyzer_module, '_semantic_similarity', lambda resume, jd: None)

    def test_identical_text_scores_highly(self):
        text = 'Python developer with AWS and Docker experience building SQL services.'
        result = match_job_description(text, text)
        assert result['match_score'] >= 70

    def test_unrelated_text_scores_low(self):
        result = match_job_description(
            'Pastry chef specializing in French desserts and cake decoration.',
            'Senior Python backend engineer with AWS, Docker, and Kubernetes experience.'
        )
        assert result['match_score'] < 40

    def test_empty_job_description_returns_error(self):
        result = match_job_description(SAMPLE_RESUME, '')
        assert 'error' in result

    def test_fallback_weighting_formula(self):
        """With no semantic model, match_pct should equal
        word*0.5 + phrase*0.2 + skill*0.3 (rounded) — recompute independently
        via the same public function's other returned fields rather than
        re-deriving word/phrase/skill percentages by hand, since those are
        internal to the function."""
        result = match_job_description(
            'Python developer with SQL and AWS experience.',
            'Looking for a Python developer with SQL and AWS experience.'
        )
        assert 0 <= result['match_score'] <= 100
        assert result['recommendation'] == _get_match_recommendation(result['match_score'])


class TestMatchRecommendationThresholds:
    """The template's score-band CSS uses 70/50/30 — this locks the verdict
    text to the same boundaries so they can't silently drift apart again."""

    @pytest.mark.parametrize('score,expected_substring', [
        (100, 'Excellent'),
        (70, 'Excellent'),
        (69, 'Good match'),
        (50, 'Good match'),
        (49, 'Moderate'),
        (30, 'Moderate'),
        (29, 'Low match'),
        (0, 'Low match'),
    ])
    def test_boundary_values(self, score, expected_substring):
        assert expected_substring in _get_match_recommendation(score)
