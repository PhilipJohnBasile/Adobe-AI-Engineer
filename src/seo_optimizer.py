#!/usr/bin/env python3
"""
SEO Optimizer Module

Real-time SEO content optimization including keyword analysis,
readability scoring, meta tag generation, and content structure analysis.

Features:
- Keyword density analysis
- Readability scoring (Flesch-Kincaid, etc.)
- Meta tag generation
- Content structure analysis
- SEO scoring and recommendations
"""

import re
import math
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class KeywordAnalysis:
    """Keyword analysis results"""
    keyword: str
    count: int
    density: float  # percentage
    in_title: bool
    in_first_paragraph: bool
    in_headings: int
    prominence_score: float


@dataclass
class ReadabilityScores:
    """Readability analysis results"""
    flesch_reading_ease: float  # 0-100, higher is easier
    flesch_kincaid_grade: float  # US grade level
    gunning_fog: float  # years of education
    smog_index: float  # years of education
    avg_sentence_length: float
    avg_word_length: float
    avg_syllables_per_word: float
    reading_level: str  # easy, moderate, difficult


@dataclass
class SEOIssue:
    """An SEO issue or recommendation"""
    category: str
    severity: str  # error, warning, info
    message: str
    suggestion: str
    impact: str  # high, medium, low


@dataclass
class SEOReport:
    """Complete SEO analysis report"""
    overall_score: float  # 0-100
    keyword_score: float
    readability_score: float
    structure_score: float
    meta_score: float
    content_length_score: float
    keyword_analysis: List[KeywordAnalysis]
    readability: ReadabilityScores
    issues: List[SEOIssue]
    recommendations: List[str]
    word_count: int
    heading_count: Dict[str, int]


class SEOOptimizer:
    """
    SEO content optimization engine.

    Features:
    - Keyword analysis and density
    - Readability scoring
    - Meta tag generation
    - Content structure analysis
    - Comprehensive SEO reporting
    """

    # Ideal ranges for SEO
    IDEAL_KEYWORD_DENSITY = (1.0, 2.5)  # percentage
    IDEAL_WORD_COUNT = (1000, 2500)
    IDEAL_SENTENCE_LENGTH = (15, 20)  # words
    IDEAL_PARAGRAPH_LENGTH = (100, 200)  # words
    IDEAL_FLESCH_SCORE = (60, 70)  # reading ease

    def __init__(self):
        self.stop_words = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall", "can", "need",
            "that", "this", "these", "those", "it", "its", "they", "them",
            "we", "us", "our", "you", "your", "he", "him", "his", "she", "her"
        }

    def analyze_content(
        self,
        content: str,
        target_keyword: str = None,
        secondary_keywords: List[str] = None,
        title: str = None,
        meta_description: str = None
    ) -> SEOReport:
        """
        Analyze content for SEO optimization.

        Args:
            content: Content to analyze
            target_keyword: Primary target keyword
            secondary_keywords: Secondary keywords
            title: Page/article title
            meta_description: Meta description

        Returns:
            SEOReport with comprehensive analysis
        """
        # Basic text analysis
        words = self._get_words(content)
        sentences = self._get_sentences(content)
        paragraphs = self._get_paragraphs(content)
        headings = self._extract_headings(content)

        word_count = len(words)

        # Keyword analysis
        keyword_analyses = []
        if target_keyword:
            keyword_analyses.append(
                self._analyze_keyword(content, target_keyword, title, headings)
            )

        if secondary_keywords:
            for kw in secondary_keywords:
                keyword_analyses.append(
                    self._analyze_keyword(content, kw, title, headings)
                )

        # Readability analysis
        readability = self._analyze_readability(content, words, sentences)

        # Structure analysis
        heading_count = {
            "h1": len([h for h in headings if h[0] == 1]),
            "h2": len([h for h in headings if h[0] == 2]),
            "h3": len([h for h in headings if h[0] == 3]),
            "h4": len([h for h in headings if h[0] == 4]),
        }

        # Generate issues and recommendations
        issues = []
        recommendations = []

        # Check content length
        content_length_score = self._score_content_length(word_count)
        if word_count < self.IDEAL_WORD_COUNT[0]:
            issues.append(SEOIssue(
                category="content_length",
                severity="warning",
                message=f"Content is short ({word_count} words)",
                suggestion=f"Aim for at least {self.IDEAL_WORD_COUNT[0]} words for better SEO",
                impact="medium"
            ))
            recommendations.append(f"Add more content to reach at least {self.IDEAL_WORD_COUNT[0]} words")

        # Check keyword density
        keyword_score = 100
        if target_keyword and keyword_analyses:
            ka = keyword_analyses[0]
            keyword_score = self._score_keyword_density(ka.density)

            if ka.density < self.IDEAL_KEYWORD_DENSITY[0]:
                issues.append(SEOIssue(
                    category="keyword_density",
                    severity="warning",
                    message=f"Keyword density too low ({ka.density:.1f}%)",
                    suggestion=f"Increase keyword usage to {self.IDEAL_KEYWORD_DENSITY[0]}-{self.IDEAL_KEYWORD_DENSITY[1]}%",
                    impact="high"
                ))
            elif ka.density > self.IDEAL_KEYWORD_DENSITY[1]:
                issues.append(SEOIssue(
                    category="keyword_density",
                    severity="warning",
                    message=f"Keyword density too high ({ka.density:.1f}%)",
                    suggestion=f"Reduce keyword stuffing to avoid penalties",
                    impact="high"
                ))

            if not ka.in_first_paragraph:
                issues.append(SEOIssue(
                    category="keyword_placement",
                    severity="info",
                    message="Target keyword not in first paragraph",
                    suggestion="Include the target keyword in your opening paragraph",
                    impact="medium"
                ))
                recommendations.append("Add target keyword to the first paragraph")

            if ka.in_headings == 0:
                recommendations.append("Include target keyword in at least one heading")

        # Check readability
        readability_score = self._score_readability(readability.flesch_reading_ease)
        if readability.flesch_reading_ease < 50:
            issues.append(SEOIssue(
                category="readability",
                severity="warning",
                message=f"Content is difficult to read (Flesch score: {readability.flesch_reading_ease:.0f})",
                suggestion="Simplify sentences and use shorter words",
                impact="medium"
            ))
            recommendations.append("Break up long sentences for better readability")

        # Check headings structure
        structure_score = self._score_structure(heading_count, word_count)
        if heading_count["h2"] == 0 and word_count > 300:
            issues.append(SEOIssue(
                category="structure",
                severity="warning",
                message="No H2 headings found",
                suggestion="Add H2 headings to break up content",
                impact="medium"
            ))
            recommendations.append("Add H2 headings every 200-300 words")

        # Check meta information
        meta_score = 100
        if title:
            if len(title) < 30:
                issues.append(SEOIssue(
                    category="meta",
                    severity="info",
                    message="Title is short",
                    suggestion="Aim for 50-60 characters in title",
                    impact="low"
                ))
                meta_score -= 15
            elif len(title) > 60:
                issues.append(SEOIssue(
                    category="meta",
                    severity="warning",
                    message="Title may be truncated in search results",
                    suggestion="Keep title under 60 characters",
                    impact="medium"
                ))
                meta_score -= 20

            if target_keyword and target_keyword.lower() not in title.lower():
                issues.append(SEOIssue(
                    category="meta",
                    severity="warning",
                    message="Target keyword not in title",
                    suggestion="Include your target keyword in the title",
                    impact="high"
                ))
                meta_score -= 25
                recommendations.append("Add target keyword to the title")

        if meta_description:
            if len(meta_description) < 120:
                issues.append(SEOIssue(
                    category="meta",
                    severity="info",
                    message="Meta description is short",
                    suggestion="Aim for 150-160 characters",
                    impact="low"
                ))
            elif len(meta_description) > 160:
                issues.append(SEOIssue(
                    category="meta",
                    severity="info",
                    message="Meta description may be truncated",
                    suggestion="Keep under 160 characters",
                    impact="low"
                ))
        else:
            meta_score -= 30
            recommendations.append("Add a meta description")

        # Calculate overall score
        overall_score = (
            keyword_score * 0.3 +
            readability_score * 0.2 +
            structure_score * 0.2 +
            meta_score * 0.15 +
            content_length_score * 0.15
        )

        return SEOReport(
            overall_score=round(overall_score, 1),
            keyword_score=round(keyword_score, 1),
            readability_score=round(readability_score, 1),
            structure_score=round(structure_score, 1),
            meta_score=round(meta_score, 1),
            content_length_score=round(content_length_score, 1),
            keyword_analysis=keyword_analyses,
            readability=readability,
            issues=issues,
            recommendations=recommendations,
            word_count=word_count,
            heading_count=heading_count
        )

    def _get_words(self, text: str) -> List[str]:
        """Extract words from text"""
        return re.findall(r'\b[a-zA-Z]+\b', text.lower())

    def _get_sentences(self, text: str) -> List[str]:
        """Extract sentences from text"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_paragraphs(self, text: str) -> List[str]:
        """Extract paragraphs from text"""
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]

    def _extract_headings(self, text: str) -> List[Tuple[int, str]]:
        """Extract headings from markdown text"""
        headings = []
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE):
            level = len(match.group(1))
            content = match.group(2).strip()
            headings.append((level, content))
        return headings

    def _analyze_keyword(
        self,
        content: str,
        keyword: str,
        title: str = None,
        headings: List[Tuple[int, str]] = None
    ) -> KeywordAnalysis:
        """Analyze keyword usage in content"""
        content_lower = content.lower()
        keyword_lower = keyword.lower()

        # Count occurrences
        count = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', content_lower))

        # Calculate density
        words = self._get_words(content)
        density = (count / max(1, len(words))) * 100

        # Check title
        in_title = keyword_lower in (title or "").lower()

        # Check first paragraph
        paragraphs = self._get_paragraphs(content)
        in_first_paragraph = keyword_lower in paragraphs[0].lower() if paragraphs else False

        # Check headings
        in_headings = 0
        if headings:
            for _, heading_text in headings:
                if keyword_lower in heading_text.lower():
                    in_headings += 1

        # Calculate prominence score
        prominence = 0
        if in_title:
            prominence += 30
        if in_first_paragraph:
            prominence += 25
        prominence += min(25, in_headings * 10)
        prominence += min(20, density * 10)

        return KeywordAnalysis(
            keyword=keyword,
            count=count,
            density=round(density, 2),
            in_title=in_title,
            in_first_paragraph=in_first_paragraph,
            in_headings=in_headings,
            prominence_score=min(100, prominence)
        )

    def _analyze_readability(
        self,
        content: str,
        words: List[str],
        sentences: List[str]
    ) -> ReadabilityScores:
        """Analyze readability of content"""
        if not words or not sentences:
            return ReadabilityScores(
                flesch_reading_ease=0,
                flesch_kincaid_grade=0,
                gunning_fog=0,
                smog_index=0,
                avg_sentence_length=0,
                avg_word_length=0,
                avg_syllables_per_word=0,
                reading_level="unknown"
            )

        # Calculate basic metrics
        word_count = len(words)
        sentence_count = len(sentences)
        syllable_count = sum(self._count_syllables(w) for w in words)

        avg_sentence_length = word_count / sentence_count
        avg_word_length = sum(len(w) for w in words) / word_count
        avg_syllables = syllable_count / word_count

        # Flesch Reading Ease
        flesch_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)
        flesch_ease = max(0, min(100, flesch_ease))

        # Flesch-Kincaid Grade Level
        fk_grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables) - 15.59
        fk_grade = max(0, fk_grade)

        # Gunning Fog Index
        complex_words = sum(1 for w in words if self._count_syllables(w) >= 3)
        complex_ratio = complex_words / word_count
        fog = 0.4 * (avg_sentence_length + 100 * complex_ratio)

        # SMOG Index
        smog = 1.0430 * math.sqrt(complex_words * (30 / sentence_count)) + 3.1291 if sentence_count > 0 else 0

        # Determine reading level
        if flesch_ease >= 70:
            reading_level = "easy"
        elif flesch_ease >= 50:
            reading_level = "moderate"
        else:
            reading_level = "difficult"

        return ReadabilityScores(
            flesch_reading_ease=round(flesch_ease, 1),
            flesch_kincaid_grade=round(fk_grade, 1),
            gunning_fog=round(fog, 1),
            smog_index=round(smog, 1),
            avg_sentence_length=round(avg_sentence_length, 1),
            avg_word_length=round(avg_word_length, 1),
            avg_syllables_per_word=round(avg_syllables, 2),
            reading_level=reading_level
        )

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        if len(word) <= 3:
            return 1

        # Remove trailing e
        word = re.sub(r'e$', '', word)

        # Count vowel groups
        vowels = re.findall(r'[aeiouy]+', word)
        return max(1, len(vowels))

    def _score_content_length(self, word_count: int) -> float:
        """Score content length"""
        if word_count >= self.IDEAL_WORD_COUNT[0] and word_count <= self.IDEAL_WORD_COUNT[1]:
            return 100
        elif word_count < self.IDEAL_WORD_COUNT[0]:
            return (word_count / self.IDEAL_WORD_COUNT[0]) * 100
        else:
            # Longer is still okay
            return 100

    def _score_keyword_density(self, density: float) -> float:
        """Score keyword density"""
        if self.IDEAL_KEYWORD_DENSITY[0] <= density <= self.IDEAL_KEYWORD_DENSITY[1]:
            return 100
        elif density < self.IDEAL_KEYWORD_DENSITY[0]:
            return (density / self.IDEAL_KEYWORD_DENSITY[0]) * 100
        else:
            # Too high - penalize
            overage = density - self.IDEAL_KEYWORD_DENSITY[1]
            return max(0, 100 - overage * 20)

    def _score_readability(self, flesch_score: float) -> float:
        """Score readability"""
        if self.IDEAL_FLESCH_SCORE[0] <= flesch_score <= self.IDEAL_FLESCH_SCORE[1]:
            return 100
        elif flesch_score > self.IDEAL_FLESCH_SCORE[1]:
            # Easier is fine
            return 100
        else:
            # Harder - penalize
            return (flesch_score / self.IDEAL_FLESCH_SCORE[0]) * 100

    def _score_structure(self, heading_count: Dict[str, int], word_count: int) -> float:
        """Score content structure"""
        score = 100

        # Check H1 (should have exactly 1)
        if heading_count.get("h1", 0) != 1:
            score -= 20

        # Check H2 (should have some for longer content)
        expected_h2 = max(1, word_count // 300)
        actual_h2 = heading_count.get("h2", 0)
        if actual_h2 < expected_h2:
            score -= min(30, (expected_h2 - actual_h2) * 10)

        return max(0, score)

    def suggest_keywords(
        self,
        content: str,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Suggest keywords based on content.

        Args:
            content: Content to analyze
            count: Number of keywords to suggest

        Returns:
            List of keyword suggestions
        """
        words = self._get_words(content)

        # Filter stop words and short words
        significant_words = [
            w for w in words
            if w not in self.stop_words and len(w) > 3
        ]

        # Count frequencies
        word_freq = Counter(significant_words)

        # Get top keywords
        top_keywords = word_freq.most_common(count)

        suggestions = []
        for word, freq in top_keywords:
            density = (freq / len(words)) * 100
            suggestions.append({
                "keyword": word,
                "frequency": freq,
                "density": round(density, 2),
                "recommendation": "Good" if self.IDEAL_KEYWORD_DENSITY[0] <= density <= self.IDEAL_KEYWORD_DENSITY[1] else "Adjust"
            })

        return suggestions

    def generate_meta_tags(
        self,
        content: str,
        title: str = None,
        target_keyword: str = None
    ) -> Dict[str, str]:
        """
        Generate optimized meta tags.

        Args:
            content: Content to generate tags for
            title: Existing title (optional)
            target_keyword: Target keyword to include

        Returns:
            Dict with meta title and description
        """
        sentences = self._get_sentences(content)

        # Generate meta title
        if title:
            meta_title = title
            if len(meta_title) > 60:
                meta_title = meta_title[:57] + "..."
        else:
            # Use first heading or first sentence
            meta_title = sentences[0][:60] if sentences else "Untitled"

        # Ensure keyword in title
        if target_keyword and target_keyword.lower() not in meta_title.lower():
            if len(meta_title) + len(target_keyword) + 3 <= 60:
                meta_title = f"{target_keyword}: {meta_title}"
            else:
                meta_title = meta_title[:30] + f" - {target_keyword}"

        # Generate meta description
        # Use first paragraph or combine first sentences
        paragraphs = self._get_paragraphs(content)
        if paragraphs:
            first_para = paragraphs[0]
            if len(first_para) > 160:
                meta_description = first_para[:157] + "..."
            elif len(first_para) < 120 and len(paragraphs) > 1:
                meta_description = (first_para + " " + paragraphs[1])[:157] + "..."
            else:
                meta_description = first_para
        else:
            meta_description = " ".join(sentences[:2])[:157] + "..." if sentences else ""

        return {
            "meta_title": meta_title,
            "meta_description": meta_description,
            "title_length": len(meta_title),
            "description_length": len(meta_description)
        }


# Demo function
def demo_seo_optimizer():
    """Demonstrate SEO optimizer"""
    print("SEO Optimizer Demo")
    print("=" * 50)

    optimizer = SEOOptimizer()

    # Sample content
    content = """
    # How to Improve Your Content Marketing Strategy

    Content marketing is essential for modern businesses. A good content marketing
    strategy can help you attract more customers and build brand awareness.

    ## Why Content Marketing Matters

    Content marketing helps businesses connect with their audience. By creating
    valuable content, you can establish trust and demonstrate expertise.

    Studies show that content marketing generates three times more leads than
    traditional advertising. It's also more cost-effective in the long run.

    ## Key Elements of Success

    A successful content marketing strategy includes:
    - Clear goals and objectives
    - Understanding your target audience
    - Consistent publishing schedule
    - Quality over quantity
    - Measurement and optimization

    ## Getting Started

    Start by defining your goals. What do you want to achieve with content
    marketing? Common goals include increasing website traffic, generating
    leads, and building brand awareness.

    Next, research your audience. Understanding their needs and preferences
    will help you create content that resonates with them.
    """

    print("\n1. Analyzing content...")
    report = optimizer.analyze_content(
        content=content,
        target_keyword="content marketing",
        title="How to Improve Your Content Marketing Strategy"
    )

    print(f"\n2. SEO Scores:")
    print(f"   Overall: {report.overall_score}/100")
    print(f"   Keyword: {report.keyword_score}/100")
    print(f"   Readability: {report.readability_score}/100")
    print(f"   Structure: {report.structure_score}/100")

    print(f"\n3. Content Stats:")
    print(f"   Word count: {report.word_count}")
    print(f"   Headings: {report.heading_count}")

    print(f"\n4. Readability:")
    print(f"   Flesch Reading Ease: {report.readability.flesch_reading_ease}")
    print(f"   Grade Level: {report.readability.flesch_kincaid_grade}")
    print(f"   Reading Level: {report.readability.reading_level}")

    if report.keyword_analysis:
        print(f"\n5. Keyword Analysis:")
        ka = report.keyword_analysis[0]
        print(f"   '{ka.keyword}': {ka.count} occurrences ({ka.density}% density)")
        print(f"   In title: {ka.in_title}, In first para: {ka.in_first_paragraph}")

    print(f"\n6. Issues Found: {len(report.issues)}")
    for issue in report.issues[:3]:
        print(f"   [{issue.severity}] {issue.message}")

    print(f"\n7. Recommendations:")
    for rec in report.recommendations[:3]:
        print(f"   - {rec}")

    print("\n Demo complete!")


if __name__ == "__main__":
    demo_seo_optimizer()
