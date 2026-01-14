#!/usr/bin/env python3
"""
Voice Learning System

Analyzes existing content to learn and create reusable brand voice profiles.
Can scan websites, blog posts, or uploaded text to extract tone, style, and
personality characteristics.

Features:
- Website content scanning
- Document analysis (PDF, DOCX, TXT)
- Voice characteristic extraction
- Reusable voice profiles
- Consistency scoring
"""

import asyncio
import json
import logging
import os
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import Counter
import statistics

logger = logging.getLogger(__name__)

# Optional imports
try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


@dataclass
class VoiceCharacteristics:
    """Extracted voice characteristics"""
    tone: str
    formality_level: float  # 0-1 (informal to formal)
    vocabulary_level: str  # simple, moderate, sophisticated, technical
    sentence_complexity: float  # 0-1
    avg_sentence_length: float
    avg_word_length: float
    personality_traits: List[str]
    common_phrases: List[str]
    power_words: List[str]
    dos: List[str]
    donts: List[str]
    sentiment_tendency: str  # positive, neutral, negative
    emotion_range: List[str]
    rhetorical_devices: List[str]


@dataclass
class VoiceProfile:
    """Complete voice profile for content generation"""
    id: str
    name: str
    description: str
    characteristics: VoiceCharacteristics
    sample_texts: List[str]
    source_urls: List[str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    owner_id: str = "default"
    usage_count: int = 0

    def to_prompt_context(self) -> str:
        """Convert to prompt context for AI generation"""
        c = self.characteristics
        return f"""
Voice Profile: {self.name}

TONE & STYLE:
- Primary Tone: {c.tone}
- Formality: {"Formal" if c.formality_level > 0.6 else "Casual" if c.formality_level < 0.4 else "Balanced"}
- Vocabulary: {c.vocabulary_level}
- Sentence Style: {"Complex" if c.sentence_complexity > 0.6 else "Simple" if c.sentence_complexity < 0.4 else "Varied"}
- Average Sentence Length: {c.avg_sentence_length:.0f} words

PERSONALITY:
- Traits: {', '.join(c.personality_traits[:5])}
- Sentiment: {c.sentiment_tendency}
- Emotions: {', '.join(c.emotion_range[:3])}

WRITING GUIDELINES:
Do:
{chr(10).join('- ' + d for d in c.dos[:5])}

Don't:
{chr(10).join('- ' + d for d in c.donts[:5])}

SIGNATURE PHRASES:
{chr(10).join('- "' + p + '"' for p in c.common_phrases[:3])}

POWER WORDS TO USE:
{', '.join(c.power_words[:10])}
"""


class VoiceAnalyzer:
    """Analyzes text to extract voice characteristics"""

    # Formality indicators
    FORMAL_WORDS = {
        "therefore", "consequently", "furthermore", "moreover", "nevertheless",
        "accordingly", "subsequently", "notwithstanding", "hence", "thus",
        "regarding", "concerning", "pursuant", "whereas", "hereby"
    }

    INFORMAL_WORDS = {
        "gonna", "wanna", "kinda", "yeah", "yep", "nope", "cool", "awesome",
        "stuff", "thing", "guy", "guys", "totally", "basically", "actually",
        "literally", "super", "really", "pretty", "kind of", "sort of"
    }

    # Personality indicators
    PERSONALITY_MARKERS = {
        "authoritative": ["research shows", "studies indicate", "data suggests", "experts agree", "evidence"],
        "friendly": ["we're here", "let's", "together", "you'll love", "excited", "glad"],
        "professional": ["our team", "we provide", "solutions", "services", "expertise"],
        "casual": ["hey", "check out", "cool", "awesome", "love it", "fun"],
        "inspirational": ["dream", "achieve", "believe", "transform", "empower", "inspire"],
        "urgent": ["now", "today", "limited", "hurry", "don't miss", "act fast"],
        "empathetic": ["understand", "feel", "struggle", "challenge", "support", "help"],
        "humorous": ["joke", "funny", "laugh", "humor", "wit", "pun"]
    }

    # Power words by category
    POWER_WORDS = {
        "urgency": ["now", "today", "instant", "fast", "quick", "hurry", "limited", "deadline"],
        "exclusivity": ["exclusive", "members", "insider", "private", "secret", "vip"],
        "trust": ["proven", "guaranteed", "certified", "authentic", "official", "trusted"],
        "value": ["free", "bonus", "save", "discount", "deal", "value", "bargain"],
        "emotion": ["love", "hate", "fear", "hope", "dream", "believe", "amazing"]
    }

    def __init__(self):
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found, using basic analysis")

    def analyze_text(self, text: str) -> VoiceCharacteristics:
        """
        Analyze text and extract voice characteristics.

        Args:
            text: Text to analyze

        Returns:
            VoiceCharacteristics with extracted features
        """
        # Basic text statistics
        sentences = self._split_sentences(text)
        words = text.lower().split()
        word_set = set(words)

        # Calculate metrics
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        avg_word_length = sum(len(w) for w in words) / max(1, len(words))

        # Formality analysis
        formality = self._calculate_formality(word_set, text)

        # Vocabulary level
        vocab_level = self._assess_vocabulary_level(words, avg_word_length)

        # Sentence complexity
        complexity = self._assess_sentence_complexity(sentences)

        # Tone detection
        tone = self._detect_tone(text, word_set)

        # Personality traits
        traits = self._detect_personality_traits(text.lower())

        # Common phrases
        common_phrases = self._extract_common_phrases(text)

        # Power words used
        power_words = self._find_power_words(word_set)

        # Sentiment
        sentiment = self._analyze_sentiment(text)

        # Rhetorical devices
        rhetorical = self._detect_rhetorical_devices(text)

        # Generate dos and donts
        dos, donts = self._generate_guidelines(formality, vocab_level, tone, traits)

        return VoiceCharacteristics(
            tone=tone,
            formality_level=formality,
            vocabulary_level=vocab_level,
            sentence_complexity=complexity,
            avg_sentence_length=avg_sentence_length,
            avg_word_length=avg_word_length,
            personality_traits=traits,
            common_phrases=common_phrases,
            power_words=power_words,
            dos=dos,
            donts=donts,
            sentiment_tendency=sentiment,
            emotion_range=self._detect_emotions(text),
            rhetorical_devices=rhetorical
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Basic sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _calculate_formality(self, word_set: set, text: str) -> float:
        """Calculate formality level (0-1)"""
        formal_count = len(word_set & self.FORMAL_WORDS)
        informal_count = len(word_set & self.INFORMAL_WORDS)

        # Check for contractions (informal)
        contractions = len(re.findall(r"\b\w+'\w+\b", text))
        informal_count += contractions * 0.5

        # Check for exclamation marks (informal)
        exclamations = text.count('!')
        informal_count += exclamations * 0.3

        total = formal_count + informal_count
        if total == 0:
            return 0.5  # Neutral

        return formal_count / total

    def _assess_vocabulary_level(self, words: List[str], avg_word_length: float) -> str:
        """Assess vocabulary sophistication level"""
        # Count syllables approximation
        long_words = sum(1 for w in words if len(w) > 8)
        long_word_ratio = long_words / max(1, len(words))

        if avg_word_length > 6 and long_word_ratio > 0.15:
            return "technical"
        elif avg_word_length > 5.5 or long_word_ratio > 0.1:
            return "sophisticated"
        elif avg_word_length > 4.5:
            return "moderate"
        else:
            return "simple"

    def _assess_sentence_complexity(self, sentences: List[str]) -> float:
        """Assess sentence complexity (0-1)"""
        if not sentences:
            return 0.5

        complexities = []
        for sentence in sentences:
            words = sentence.split()
            word_count = len(words)

            # Check for subordinating conjunctions
            subordinators = ["because", "although", "while", "when", "if", "unless", "since", "after", "before"]
            has_subordination = any(s in sentence.lower() for s in subordinators)

            # Check for comma usage (often indicates complex structure)
            comma_count = sentence.count(',')

            complexity = min(1.0, (word_count / 30) + (comma_count * 0.1) + (0.2 if has_subordination else 0))
            complexities.append(complexity)

        return statistics.mean(complexities)

    def _detect_tone(self, text: str, word_set: set) -> str:
        """Detect primary tone"""
        text_lower = text.lower()

        tone_scores = {
            "professional": 0,
            "casual": 0,
            "enthusiastic": 0,
            "serious": 0,
            "friendly": 0,
            "authoritative": 0
        }

        # Professional indicators
        if any(w in text_lower for w in ["professional", "expertise", "solution", "services"]):
            tone_scores["professional"] += 2
        if len(word_set & self.FORMAL_WORDS) > 2:
            tone_scores["professional"] += 1
            tone_scores["authoritative"] += 1

        # Casual indicators
        if len(word_set & self.INFORMAL_WORDS) > 2:
            tone_scores["casual"] += 2
        if text.count('!') > 3:
            tone_scores["enthusiastic"] += 2
            tone_scores["casual"] += 1

        # Friendly indicators
        if any(w in text_lower for w in ["we", "us", "our", "together", "you'll"]):
            tone_scores["friendly"] += 1

        # Authoritative indicators
        if any(w in text_lower for w in ["research", "study", "data", "evidence", "expert"]):
            tone_scores["authoritative"] += 2

        return max(tone_scores.items(), key=lambda x: x[1])[0]

    def _detect_personality_traits(self, text: str) -> List[str]:
        """Detect personality traits in writing"""
        traits = []

        for trait, markers in self.PERSONALITY_MARKERS.items():
            if any(marker in text for marker in markers):
                traits.append(trait)

        return traits if traits else ["balanced"]

    def _extract_common_phrases(self, text: str) -> List[str]:
        """Extract commonly used phrases"""
        # Find 2-4 word phrases
        words = text.lower().split()
        phrases = []

        for n in [2, 3, 4]:
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                # Clean phrase
                phrase = re.sub(r'[^\w\s]', '', phrase).strip()
                if phrase and len(phrase) > 5:
                    phrases.append(phrase)

        # Count occurrences
        phrase_counts = Counter(phrases)
        common = [p for p, c in phrase_counts.most_common(20) if c >= 2]

        return common[:10]

    def _find_power_words(self, word_set: set) -> List[str]:
        """Find power words used in text"""
        found = []
        for category, words in self.POWER_WORDS.items():
            for word in words:
                if word in word_set:
                    found.append(word)
        return list(set(found))

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze overall sentiment"""
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity

                if polarity > 0.2:
                    return "positive"
                elif polarity < -0.2:
                    return "negative"
                else:
                    return "neutral"
            except Exception:
                pass

        # Fallback: simple word counting
        positive_words = {"good", "great", "excellent", "amazing", "love", "best", "happy", "wonderful"}
        negative_words = {"bad", "poor", "terrible", "worst", "hate", "awful", "disappointing"}

        words = set(text.lower().split())
        pos_count = len(words & positive_words)
        neg_count = len(words & negative_words)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        return "neutral"

    def _detect_emotions(self, text: str) -> List[str]:
        """Detect emotional range"""
        text_lower = text.lower()
        emotions = []

        emotion_words = {
            "excitement": ["excited", "thrilled", "amazing", "incredible"],
            "trust": ["trust", "reliable", "proven", "guaranteed"],
            "curiosity": ["discover", "learn", "explore", "find out"],
            "urgency": ["now", "hurry", "limited", "don't miss"],
            "comfort": ["easy", "simple", "comfortable", "relaxed"],
            "aspiration": ["dream", "achieve", "success", "goal"]
        }

        for emotion, words in emotion_words.items():
            if any(w in text_lower for w in words):
                emotions.append(emotion)

        return emotions if emotions else ["neutral"]

    def _detect_rhetorical_devices(self, text: str) -> List[str]:
        """Detect rhetorical devices used"""
        devices = []

        # Questions (rhetorical)
        if '?' in text:
            devices.append("rhetorical_questions")

        # Repetition
        words = text.lower().split()
        word_counts = Counter(words)
        if any(c > 3 for w, c in word_counts.items() if len(w) > 4):
            devices.append("repetition")

        # Alliteration
        sentences = self._split_sentences(text)
        for sentence in sentences:
            words = sentence.lower().split()
            if len(words) >= 3:
                first_letters = [w[0] for w in words if w]
                if any(first_letters.count(l) >= 3 for l in set(first_letters)):
                    devices.append("alliteration")
                    break

        # Lists/triads
        if text.count(',') > 3:
            devices.append("lists")

        # Direct address
        if any(w in text.lower() for w in ["you", "your", "you'll", "you're"]):
            devices.append("direct_address")

        return list(set(devices))

    def _generate_guidelines(
        self,
        formality: float,
        vocab_level: str,
        tone: str,
        traits: List[str]
    ) -> Tuple[List[str], List[str]]:
        """Generate dos and donts based on analysis"""
        dos = []
        donts = []

        # Formality guidelines
        if formality > 0.6:
            dos.extend(["Use complete sentences", "Maintain professional language", "Avoid contractions"])
            donts.extend(["Use slang or colloquialisms", "Start sentences with 'And' or 'But'"])
        elif formality < 0.4:
            dos.extend(["Use contractions naturally", "Write conversationally", "Use everyday language"])
            donts.extend(["Be overly formal", "Use jargon unnecessarily"])
        else:
            dos.extend(["Balance formal and casual language", "Adapt tone to context"])

        # Vocabulary guidelines
        if vocab_level == "simple":
            dos.extend(["Use short, common words", "Keep sentences brief"])
            donts.extend(["Use complex vocabulary", "Write long paragraphs"])
        elif vocab_level in ["sophisticated", "technical"]:
            dos.extend(["Use precise terminology", "Provide depth and detail"])

        # Tone guidelines
        if tone == "friendly":
            dos.extend(["Use inclusive language (we, us)", "Show empathy"])
        elif tone == "authoritative":
            dos.extend(["Cite evidence and research", "Use confident language"])
        elif tone == "enthusiastic":
            dos.extend(["Show excitement appropriately", "Use dynamic language"])

        # Personality guidelines
        if "empathetic" in traits:
            dos.append("Acknowledge reader challenges")
        if "humorous" in traits:
            dos.append("Include appropriate humor")
            donts.append("Be overly serious")

        return dos, donts


class VoiceLearningSystem:
    """
    Complete voice learning system for brand voice analysis and profile creation.

    Features:
    - Website scanning
    - Document analysis
    - Voice profile creation and management
    - Consistency scoring
    """

    def __init__(self, storage_path: str = "data/voice_profiles"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.analyzer = VoiceAnalyzer()
        self.profiles: Dict[str, VoiceProfile] = {}
        self._load_profiles()

    def _load_profiles(self):
        """Load profiles from disk"""
        for profile_file in self.storage_path.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                # Reconstruct characteristics
                chars = VoiceCharacteristics(**data.get("characteristics", {}))
                data["characteristics"] = chars
                profile = VoiceProfile(**data)
                self.profiles[profile.id] = profile
            except Exception as e:
                logger.error(f"Error loading profile {profile_file}: {e}")

    def _save_profile(self, profile: VoiceProfile):
        """Save profile to disk"""
        profile_file = self.storage_path / f"{profile.id}.json"
        data = asdict(profile)
        with open(profile_file, 'w') as f:
            json.dump(data, f, indent=2)
        self.profiles[profile.id] = profile

    async def analyze_website(
        self,
        url: str,
        max_pages: int = 10
    ) -> VoiceCharacteristics:
        """
        Analyze website content for voice characteristics.

        Args:
            url: Website URL to analyze
            max_pages: Maximum pages to scan

        Returns:
            VoiceCharacteristics extracted from website
        """
        if not WEB_SCRAPING_AVAILABLE:
            raise ImportError("Web scraping not available. Install requests and beautifulsoup4.")

        # Fetch main page
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            raise Exception(f"Failed to fetch website: {e}")

        # Extract text content
        texts = []

        # Get main content areas
        for tag in ['article', 'main', 'div.content', 'div.post', 'p']:
            elements = soup.find_all(tag)
            for el in elements:
                text = el.get_text(strip=True)
                if len(text) > 100:  # Meaningful content
                    texts.append(text)

        if not texts:
            raise Exception("No content found on website")

        # Combine and analyze
        combined_text = "\n\n".join(texts[:50])  # Limit for analysis
        return self.analyzer.analyze_text(combined_text)

    async def analyze_documents(
        self,
        file_paths: List[Path]
    ) -> VoiceCharacteristics:
        """
        Analyze uploaded documents for voice characteristics.

        Args:
            file_paths: List of document paths

        Returns:
            VoiceCharacteristics extracted from documents
        """
        texts = []

        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                continue

            try:
                if path.suffix.lower() == '.txt':
                    with open(path, 'r', encoding='utf-8') as f:
                        texts.append(f.read())

                elif path.suffix.lower() == '.md':
                    with open(path, 'r', encoding='utf-8') as f:
                        # Remove markdown formatting
                        content = f.read()
                        content = re.sub(r'#+\s*', '', content)
                        content = re.sub(r'\*+', '', content)
                        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
                        texts.append(content)

                elif path.suffix.lower() == '.pdf':
                    try:
                        import PyPDF2
                        with open(path, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            for page in reader.pages[:20]:  # First 20 pages
                                texts.append(page.extract_text())
                    except ImportError:
                        logger.warning("PyPDF2 not available for PDF parsing")

                elif path.suffix.lower() == '.docx':
                    try:
                        from docx import Document
                        doc = Document(path)
                        for para in doc.paragraphs:
                            if para.text.strip():
                                texts.append(para.text)
                    except ImportError:
                        logger.warning("python-docx not available for DOCX parsing")

            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")

        if not texts:
            raise Exception("No text content could be extracted from documents")

        combined_text = "\n\n".join(texts)
        return self.analyzer.analyze_text(combined_text)

    async def analyze_text_samples(
        self,
        samples: List[str]
    ) -> VoiceCharacteristics:
        """
        Analyze text samples for voice characteristics.

        Args:
            samples: List of text samples

        Returns:
            VoiceCharacteristics extracted from samples
        """
        combined_text = "\n\n".join(samples)
        return self.analyzer.analyze_text(combined_text)

    async def create_voice_profile(
        self,
        name: str,
        description: str = "",
        samples: List[str] = None,
        website_url: str = None,
        document_paths: List[Path] = None,
        owner_id: str = "default"
    ) -> VoiceProfile:
        """
        Create a voice profile from various sources.

        Args:
            name: Profile name
            description: Profile description
            samples: Text samples
            website_url: Website to analyze
            document_paths: Documents to analyze
            owner_id: Owner user ID

        Returns:
            Created VoiceProfile
        """
        all_texts = []
        source_urls = []

        # Analyze samples
        if samples:
            all_texts.extend(samples)

        # Analyze website
        if website_url:
            try:
                web_chars = await self.analyze_website(website_url)
                source_urls.append(website_url)
                # We'll use the combined analysis
            except Exception as e:
                logger.warning(f"Website analysis failed: {e}")

        # Analyze documents
        if document_paths:
            try:
                for path in document_paths:
                    if Path(path).exists():
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            all_texts.append(f.read())
            except Exception as e:
                logger.warning(f"Document analysis failed: {e}")

        if not all_texts:
            raise Exception("No content provided for analysis")

        # Analyze combined content
        characteristics = self.analyzer.analyze_text("\n\n".join(all_texts))

        # Create profile
        profile_id = hashlib.md5(name.encode()).hexdigest()[:8]

        profile = VoiceProfile(
            id=profile_id,
            name=name,
            description=description or f"Voice profile for {name}",
            characteristics=characteristics,
            sample_texts=samples[:5] if samples else [],
            source_urls=source_urls,
            owner_id=owner_id
        )

        self._save_profile(profile)
        logger.info(f"Created voice profile: {profile_id} - {name}")

        return profile

    def get_profile(self, profile_id: str) -> Optional[VoiceProfile]:
        """Get voice profile by ID"""
        return self.profiles.get(profile_id)

    def list_profiles(self, owner_id: str = None) -> List[Dict[str, Any]]:
        """List all voice profiles"""
        profiles = list(self.profiles.values())
        if owner_id:
            profiles = [p for p in profiles if p.owner_id == owner_id]

        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "tone": p.characteristics.tone,
                "usage_count": p.usage_count,
                "created_at": p.created_at
            }
            for p in profiles
        ]

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a voice profile"""
        if profile_id in self.profiles:
            profile_file = self.storage_path / f"{profile_id}.json"
            if profile_file.exists():
                profile_file.unlink()
            del self.profiles[profile_id]
            return True
        return False

    def score_consistency(self, text: str, profile_id: str) -> Dict[str, Any]:
        """
        Score how well text matches a voice profile.

        Args:
            text: Text to score
            profile_id: Profile to compare against

        Returns:
            Dict with consistency scores
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return {"error": "Profile not found"}

        # Analyze the text
        text_chars = self.analyzer.analyze_text(text)
        profile_chars = profile.characteristics

        # Calculate similarity scores
        scores = {}

        # Formality match
        formality_diff = abs(text_chars.formality_level - profile_chars.formality_level)
        scores["formality"] = max(0, 1 - formality_diff)

        # Complexity match
        complexity_diff = abs(text_chars.sentence_complexity - profile_chars.sentence_complexity)
        scores["complexity"] = max(0, 1 - complexity_diff)

        # Sentence length match
        length_diff = abs(text_chars.avg_sentence_length - profile_chars.avg_sentence_length)
        scores["sentence_length"] = max(0, 1 - length_diff / 20)

        # Vocabulary level match
        vocab_match = 1.0 if text_chars.vocabulary_level == profile_chars.vocabulary_level else 0.5
        scores["vocabulary"] = vocab_match

        # Tone match
        tone_match = 1.0 if text_chars.tone == profile_chars.tone else 0.3
        scores["tone"] = tone_match

        # Personality traits overlap
        text_traits = set(text_chars.personality_traits)
        profile_traits = set(profile_chars.personality_traits)
        if profile_traits:
            trait_overlap = len(text_traits & profile_traits) / len(profile_traits)
            scores["personality"] = trait_overlap
        else:
            scores["personality"] = 0.5

        # Overall score
        overall = sum(scores.values()) / len(scores)

        return {
            "overall_score": round(overall, 2),
            "detailed_scores": {k: round(v, 2) for k, v in scores.items()},
            "recommendations": self._generate_recommendations(text_chars, profile_chars, scores)
        }

    def _generate_recommendations(
        self,
        text_chars: VoiceCharacteristics,
        profile_chars: VoiceCharacteristics,
        scores: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations to improve voice consistency"""
        recommendations = []

        if scores.get("formality", 1) < 0.7:
            if text_chars.formality_level < profile_chars.formality_level:
                recommendations.append("Make the language more formal")
            else:
                recommendations.append("Make the language more casual")

        if scores.get("sentence_length", 1) < 0.7:
            if text_chars.avg_sentence_length < profile_chars.avg_sentence_length:
                recommendations.append("Use longer, more developed sentences")
            else:
                recommendations.append("Break up long sentences for readability")

        if scores.get("tone", 1) < 0.7:
            recommendations.append(f"Adjust tone to be more {profile_chars.tone}")

        if scores.get("vocabulary", 1) < 0.7:
            recommendations.append(f"Adjust vocabulary level to {profile_chars.vocabulary_level}")

        return recommendations


# Demo function
async def demo_voice_learning():
    """Demonstrate voice learning capabilities"""
    print("Voice Learning System Demo")
    print("=" * 50)

    system = VoiceLearningSystem()

    # Create sample content
    samples = [
        """We're excited to share our latest innovation with you! Our team has been working
        tirelessly to create something that will transform how you work. Check out these
        amazing features - you're going to love them!""",

        """Hey there! Want to know the secret to productivity? It's not about working harder,
        it's about working smarter. Let us show you how our tools can help you crush your goals.""",

        """We believe in making technology accessible to everyone. That's why we've designed
        our platform to be super easy to use - no tech degree required! Join thousands of
        happy users who've already made the switch."""
    ]

    print("\n1. Analyzing sample content...")
    chars = await system.analyze_text_samples(samples)
    print(f"   Detected tone: {chars.tone}")
    print(f"   Formality level: {chars.formality_level:.2f}")
    print(f"   Vocabulary: {chars.vocabulary_level}")
    print(f"   Personality traits: {', '.join(chars.personality_traits)}")

    print("\n2. Creating voice profile...")
    profile = await system.create_voice_profile(
        name="Friendly Tech Brand",
        description="Casual, enthusiastic tech company voice",
        samples=samples
    )
    print(f"   Created profile: {profile.id} - {profile.name}")

    print("\n3. Profile prompt context:")
    print(profile.to_prompt_context()[:500] + "...")

    print("\n4. Consistency scoring...")
    test_text = "Our innovative solution leverages cutting-edge technology to deliver unprecedented results."
    score = system.score_consistency(test_text, profile.id)
    print(f"   Overall consistency: {score['overall_score']}")
    print(f"   Recommendations: {score['recommendations'][:2]}")

    print("\n Demo complete!")


if __name__ == "__main__":
    asyncio.run(demo_voice_learning())
