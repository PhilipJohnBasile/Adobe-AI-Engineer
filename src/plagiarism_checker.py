"""
Plagiarism Checker Module

Provides content originality verification through multiple methods:
- Copyscape API integration (primary)
- Web search comparison
- Internal content fingerprinting
- Similarity detection algorithms
"""

import re
import os
import json
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
import math

# Optional imports with fallbacks
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PlagiarismMatch:
    """Represents a potential plagiarism match."""
    match_id: str
    source_url: Optional[str]
    source_title: Optional[str]
    matched_text: str
    original_text: str
    similarity_score: float
    start_position: int
    end_position: int
    match_type: str  # "exact", "paraphrase", "similar"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_id": self.match_id,
            "source_url": self.source_url,
            "source_title": self.source_title,
            "matched_text": self.matched_text,
            "original_text": self.original_text,
            "similarity_score": self.similarity_score,
            "start_position": self.start_position,
            "end_position": self.end_position,
            "match_type": self.match_type
        }


@dataclass
class PlagiarismReport:
    """Complete plagiarism check report."""
    text_checked: str
    overall_score: float  # 0-100, 100 = completely original
    matches: List[PlagiarismMatch]
    unique_content_percentage: float
    word_count: int
    sentences_checked: int
    sources_found: int
    check_timestamp: datetime = field(default_factory=datetime.now)
    check_method: str = "hybrid"

    @property
    def is_original(self) -> bool:
        """Consider content original if above 85% unique."""
        return self.unique_content_percentage >= 85.0

    @property
    def risk_level(self) -> str:
        """Get risk level based on originality."""
        if self.unique_content_percentage >= 95:
            return "very_low"
        elif self.unique_content_percentage >= 85:
            return "low"
        elif self.unique_content_percentage >= 70:
            return "medium"
        elif self.unique_content_percentage >= 50:
            return "high"
        else:
            return "critical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "unique_content_percentage": self.unique_content_percentage,
            "is_original": self.is_original,
            "risk_level": self.risk_level,
            "word_count": self.word_count,
            "sentences_checked": self.sentences_checked,
            "sources_found": self.sources_found,
            "matches": [m.to_dict() for m in self.matches],
            "check_timestamp": self.check_timestamp.isoformat(),
            "check_method": self.check_method
        }


class ContentFingerprinter:
    """
    Generate and compare content fingerprints for plagiarism detection.
    Uses shingling and MinHash for efficient similarity detection.
    """

    def __init__(self, shingle_size: int = 5, num_hashes: int = 100):
        self.shingle_size = shingle_size
        self.num_hashes = num_hashes
        self.fingerprint_db: Dict[str, Dict[str, Any]] = {}

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.split()

    def _create_shingles(self, text: str) -> Set[str]:
        """Create word-level shingles from text."""
        words = self._tokenize(text)
        shingles = set()

        for i in range(len(words) - self.shingle_size + 1):
            shingle = " ".join(words[i:i + self.shingle_size])
            shingles.add(shingle)

        return shingles

    def _hash_shingle(self, shingle: str, seed: int) -> int:
        """Hash a shingle with a seed for MinHash."""
        return int(hashlib.md5(f"{seed}{shingle}".encode()).hexdigest(), 16)

    def create_minhash_signature(self, text: str) -> List[int]:
        """Create MinHash signature for text."""
        shingles = self._create_shingles(text)

        if not shingles:
            return [0] * self.num_hashes

        signature = []
        for seed in range(self.num_hashes):
            min_hash = min(self._hash_shingle(s, seed) for s in shingles)
            signature.append(min_hash)

        return signature

    def estimate_similarity(self, sig1: List[int], sig2: List[int]) -> float:
        """Estimate Jaccard similarity from MinHash signatures."""
        if not sig1 or not sig2:
            return 0.0

        matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
        return matches / len(sig1)

    def add_to_database(self, doc_id: str, text: str, metadata: Optional[Dict] = None):
        """Add document fingerprint to database."""
        signature = self.create_minhash_signature(text)
        shingles = self._create_shingles(text)

        self.fingerprint_db[doc_id] = {
            "signature": signature,
            "shingles": shingles,
            "metadata": metadata or {},
            "added_at": datetime.now().isoformat()
        }

    def find_similar(self, text: str, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Find similar documents in database."""
        query_sig = self.create_minhash_signature(text)
        results = []

        for doc_id, doc_data in self.fingerprint_db.items():
            similarity = self.estimate_similarity(query_sig, doc_data["signature"])
            if similarity >= threshold:
                results.append((doc_id, similarity))

        return sorted(results, key=lambda x: x[1], reverse=True)

    def get_exact_matches(self, text: str) -> Dict[str, List[str]]:
        """Find exact shingle matches with stored documents."""
        query_shingles = self._create_shingles(text)
        matches = {}

        for doc_id, doc_data in self.fingerprint_db.items():
            common = query_shingles.intersection(doc_data["shingles"])
            if common:
                matches[doc_id] = list(common)

        return matches


class CopyscapeClient:
    """
    Copyscape API client for professional plagiarism detection.
    Requires API credentials from copyscape.com
    """

    API_URL = "https://www.copyscape.com/api/"

    def __init__(self):
        self.username = os.getenv("COPYSCAPE_USERNAME")
        self.api_key = os.getenv("COPYSCAPE_API_KEY")
        self.enabled = bool(self.username and self.api_key)

        if not self.enabled:
            logger.warning("Copyscape API credentials not configured")

    def check_text(self, text: str, full_comparison: bool = False) -> List[Dict[str, Any]]:
        """
        Check text for plagiarism using Copyscape API.

        Args:
            text: Text to check
            full_comparison: Get full text comparisons (uses more credits)

        Returns:
            List of matched sources
        """
        if not self.enabled or not HAS_REQUESTS:
            return []

        try:
            params = {
                "u": self.username,
                "o": self.api_key,
                "t": text,
                "f": "json"
            }

            if full_comparison:
                params["c"] = "1"

            response = requests.post(
                f"{self.API_URL}",
                data=params,
                timeout=60
            )
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                logger.error(f"Copyscape API error: {data['error']}")
                return []

            return data.get("result", [])

        except Exception as e:
            logger.error(f"Copyscape API request failed: {e}")
            return []

    def check_url(self, url: str) -> List[Dict[str, Any]]:
        """Check URL for plagiarism using Copyscape API."""
        if not self.enabled or not HAS_REQUESTS:
            return []

        try:
            params = {
                "u": self.username,
                "o": self.api_key,
                "q": url,
                "f": "json"
            }

            response = requests.get(
                f"{self.API_URL}",
                params=params,
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            return data.get("result", [])

        except Exception as e:
            logger.error(f"Copyscape URL check failed: {e}")
            return []

    def get_credits(self) -> Optional[int]:
        """Get remaining API credits."""
        if not self.enabled or not HAS_REQUESTS:
            return None

        try:
            params = {
                "u": self.username,
                "o": self.api_key,
                "f": "json"
            }

            response = requests.get(
                f"{self.API_URL}balance/",
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            return data.get("value")

        except Exception as e:
            logger.error(f"Failed to get Copyscape credits: {e}")
            return None


class SemanticSimilarityChecker:
    """
    Use sentence embeddings for semantic similarity detection.
    Catches paraphrased content that word-matching might miss.
    """

    def __init__(self):
        self.model = None
        self.enabled = HAS_SENTENCE_TRANSFORMERS

        if self.enabled:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Semantic similarity model loaded")
            except Exception as e:
                logger.warning(f"Could not load sentence transformer: {e}")
                self.enabled = False

        self.document_embeddings: Dict[str, np.ndarray] = {}

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def get_embeddings(self, texts: List[str]) -> Optional[Any]:
        """Get embeddings for list of texts."""
        if not self.enabled or not self.model:
            return None

        try:
            return self.model.encode(texts, convert_to_numpy=True)
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            return None

    def add_document(self, doc_id: str, text: str):
        """Add document embeddings for comparison."""
        if not self.enabled:
            return

        sentences = self._split_sentences(text)
        embeddings = self.get_embeddings(sentences)

        if embeddings is not None:
            self.document_embeddings[doc_id] = {
                "sentences": sentences,
                "embeddings": embeddings
            }

    def find_similar_sentences(self, text: str, threshold: float = 0.85) -> List[Dict[str, Any]]:
        """Find semantically similar sentences in stored documents."""
        if not self.enabled or not self.document_embeddings:
            return []

        sentences = self._split_sentences(text)
        query_embeddings = self.get_embeddings(sentences)

        if query_embeddings is None:
            return []

        matches = []

        for doc_id, doc_data in self.document_embeddings.items():
            doc_embeddings = doc_data["embeddings"]
            doc_sentences = doc_data["sentences"]

            # Calculate similarity matrix
            similarity_matrix = np.dot(query_embeddings, doc_embeddings.T)

            for i, query_sent in enumerate(sentences):
                max_sim_idx = np.argmax(similarity_matrix[i])
                max_sim = similarity_matrix[i][max_sim_idx]

                if max_sim >= threshold:
                    matches.append({
                        "query_sentence": query_sent,
                        "matched_sentence": doc_sentences[max_sim_idx],
                        "similarity": float(max_sim),
                        "doc_id": doc_id
                    })

        return sorted(matches, key=lambda x: x["similarity"], reverse=True)


class TfidfChecker:
    """
    TF-IDF based similarity checking.
    Good for catching close paraphrases and rewording.
    """

    def __init__(self):
        self.enabled = HAS_SKLEARN
        self.vectorizer = None
        self.document_vectors = {}
        self.documents: Dict[str, str] = {}

        if self.enabled:
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                stop_words='english',
                max_features=10000
            )

    def add_document(self, doc_id: str, text: str):
        """Add document for comparison."""
        if not self.enabled:
            return

        self.documents[doc_id] = text
        self._rebuild_index()

    def _rebuild_index(self):
        """Rebuild TF-IDF index with all documents."""
        if not self.documents:
            return

        all_texts = list(self.documents.values())
        all_ids = list(self.documents.keys())

        try:
            vectors = self.vectorizer.fit_transform(all_texts)

            for i, doc_id in enumerate(all_ids):
                self.document_vectors[doc_id] = vectors[i]
        except Exception as e:
            logger.error(f"Failed to build TF-IDF index: {e}")

    def check_similarity(self, text: str) -> List[Tuple[str, float]]:
        """Check text similarity against stored documents."""
        if not self.enabled or not self.document_vectors:
            return []

        try:
            query_vector = self.vectorizer.transform([text])
            results = []

            for doc_id, doc_vector in self.document_vectors.items():
                similarity = cosine_similarity(query_vector, doc_vector)[0][0]
                results.append((doc_id, float(similarity)))

            return sorted(results, key=lambda x: x[1], reverse=True)
        except Exception as e:
            logger.error(f"TF-IDF similarity check failed: {e}")
            return []


class PlagiarismChecker:
    """
    Main plagiarism checker combining multiple detection methods.

    Usage:
        checker = PlagiarismChecker()
        report = checker.check("Your content here...")
        print(f"Originality: {report.unique_content_percentage}%")
    """

    def __init__(self):
        self.copyscape = CopyscapeClient()
        self.fingerprinter = ContentFingerprinter()
        self.semantic_checker = SemanticSimilarityChecker()
        self.tfidf_checker = TfidfChecker()

        # Internal content database for self-plagiarism detection
        self.content_db: Dict[str, Dict[str, Any]] = {}

        # Statistics
        self.stats = {
            "total_checks": 0,
            "total_matches_found": 0,
            "average_originality": 100.0
        }

        logger.info("Plagiarism checker initialized")
        if self.copyscape.enabled:
            logger.info("Copyscape API enabled")

    def check(self, text: str,
              use_copyscape: bool = True,
              check_internal: bool = True,
              check_semantic: bool = True,
              deep_check: bool = False) -> PlagiarismReport:
        """
        Check text for plagiarism.

        Args:
            text: Text to check
            use_copyscape: Use Copyscape API if available
            check_internal: Check against internal content database
            check_semantic: Use semantic similarity detection
            deep_check: Perform more thorough checking (slower)

        Returns:
            PlagiarismReport with detailed results
        """
        if not text or not text.strip():
            return PlagiarismReport(
                text_checked=text,
                overall_score=100.0,
                matches=[],
                unique_content_percentage=100.0,
                word_count=0,
                sentences_checked=0,
                sources_found=0
            )

        self.stats["total_checks"] += 1
        all_matches = []
        matched_ranges: List[Tuple[int, int]] = []

        # Word and sentence counts
        words = text.split()
        sentences = re.split(r'(?<=[.!?])\s+', text)
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])

        # Check internal content database first
        if check_internal and self.content_db:
            internal_matches = self._check_internal(text)
            for match in internal_matches:
                all_matches.append(match)
                matched_ranges.append((match.start_position, match.end_position))

        # Check with Copyscape API
        if use_copyscape and self.copyscape.enabled:
            copyscape_matches = self._check_copyscape(text, deep_check)
            for match in copyscape_matches:
                # Avoid duplicate ranges
                if not self._overlaps(matched_ranges, match.start_position, match.end_position):
                    all_matches.append(match)
                    matched_ranges.append((match.start_position, match.end_position))

        # Semantic similarity check
        if check_semantic and self.semantic_checker.enabled:
            semantic_matches = self._check_semantic(text)
            for match in semantic_matches:
                if not self._overlaps(matched_ranges, match.start_position, match.end_position):
                    all_matches.append(match)
                    matched_ranges.append((match.start_position, match.end_position))

        # Fingerprint similarity check
        fingerprint_matches = self._check_fingerprints(text)
        for match in fingerprint_matches:
            if not self._overlaps(matched_ranges, match.start_position, match.end_position):
                all_matches.append(match)
                matched_ranges.append((match.start_position, match.end_position))

        # Calculate originality
        matched_chars = sum(end - start for start, end in matched_ranges)
        total_chars = len(text)
        unique_percentage = max(0, 100 * (1 - matched_chars / total_chars)) if total_chars > 0 else 100

        # Update stats
        self.stats["total_matches_found"] += len(all_matches)
        total_checks = self.stats["total_checks"]
        self.stats["average_originality"] = (
            (self.stats["average_originality"] * (total_checks - 1) + unique_percentage) / total_checks
        )

        sources = set(m.source_url for m in all_matches if m.source_url)

        return PlagiarismReport(
            text_checked=text,
            overall_score=unique_percentage,
            matches=all_matches,
            unique_content_percentage=unique_percentage,
            word_count=word_count,
            sentences_checked=sentence_count,
            sources_found=len(sources),
            check_method="hybrid"
        )

    def _check_internal(self, text: str) -> List[PlagiarismMatch]:
        """Check against internal content database."""
        matches = []

        # Use fingerprinting for quick check
        similar_docs = self.fingerprinter.find_similar(text, threshold=0.2)

        for doc_id, similarity in similar_docs:
            if doc_id in self.content_db:
                doc_data = self.content_db[doc_id]

                # Find specific matching segments
                exact_matches = self.fingerprinter.get_exact_matches(text)

                if doc_id in exact_matches:
                    for shingle in exact_matches[doc_id][:5]:  # Limit matches
                        # Find position in text
                        pos = text.lower().find(shingle.split()[0])
                        if pos >= 0:
                            matches.append(PlagiarismMatch(
                                match_id=f"internal_{doc_id}_{len(matches)}",
                                source_url=None,
                                source_title=doc_data.get("title", f"Document {doc_id}"),
                                matched_text=shingle,
                                original_text=shingle,
                                similarity_score=similarity,
                                start_position=pos,
                                end_position=pos + len(shingle),
                                match_type="exact" if similarity > 0.9 else "similar"
                            ))

        return matches

    def _check_copyscape(self, text: str, full_comparison: bool) -> List[PlagiarismMatch]:
        """Check with Copyscape API."""
        matches = []

        results = self.copyscape.check_text(text, full_comparison)

        for i, result in enumerate(results):
            url = result.get("url", "")
            title = result.get("title", "Unknown Source")
            matched_text = result.get("textsnippet", "")
            percent_match = float(result.get("percentmatched", 0))

            # Estimate position (Copyscape doesn't always provide this)
            pos = text.find(matched_text[:50]) if matched_text else 0
            pos = max(0, pos)

            matches.append(PlagiarismMatch(
                match_id=f"copyscape_{i}",
                source_url=url,
                source_title=title,
                matched_text=matched_text,
                original_text=matched_text,
                similarity_score=percent_match / 100,
                start_position=pos,
                end_position=pos + len(matched_text),
                match_type="exact" if percent_match > 90 else "similar"
            ))

        return matches

    def _check_semantic(self, text: str) -> List[PlagiarismMatch]:
        """Check for semantic similarity."""
        matches = []

        similar_sentences = self.semantic_checker.find_similar_sentences(text, threshold=0.85)

        for i, result in enumerate(similar_sentences[:10]):  # Limit results
            query_sent = result["query_sentence"]
            matched_sent = result["matched_sentence"]
            similarity = result["similarity"]

            pos = text.find(query_sent)
            pos = max(0, pos)

            matches.append(PlagiarismMatch(
                match_id=f"semantic_{i}",
                source_url=None,
                source_title=f"Document {result['doc_id']}",
                matched_text=matched_sent,
                original_text=query_sent,
                similarity_score=similarity,
                start_position=pos,
                end_position=pos + len(query_sent),
                match_type="paraphrase"
            ))

        return matches

    def _check_fingerprints(self, text: str) -> List[PlagiarismMatch]:
        """Check using content fingerprints."""
        matches = []

        similar = self.fingerprinter.find_similar(text, threshold=0.3)

        for doc_id, similarity in similar[:5]:
            if similarity > 0.5:  # Only report significant matches
                matches.append(PlagiarismMatch(
                    match_id=f"fingerprint_{doc_id}",
                    source_url=None,
                    source_title=f"Document {doc_id}",
                    matched_text="",
                    original_text="",
                    similarity_score=similarity,
                    start_position=0,
                    end_position=len(text),
                    match_type="similar"
                ))

        return matches

    def _overlaps(self, ranges: List[Tuple[int, int]], start: int, end: int) -> bool:
        """Check if a range overlaps with existing ranges."""
        for r_start, r_end in ranges:
            if start < r_end and end > r_start:
                return True
        return False

    def add_to_database(self, doc_id: str, text: str,
                        title: Optional[str] = None,
                        metadata: Optional[Dict] = None):
        """
        Add content to internal database for self-plagiarism detection.

        Args:
            doc_id: Unique document identifier
            text: Document text
            title: Document title
            metadata: Additional metadata
        """
        self.content_db[doc_id] = {
            "text": text,
            "title": title or doc_id,
            "metadata": metadata or {},
            "added_at": datetime.now().isoformat()
        }

        # Add to fingerprinting database
        self.fingerprinter.add_to_database(doc_id, text, metadata)

        # Add to semantic checker
        if self.semantic_checker.enabled:
            self.semantic_checker.add_document(doc_id, text)

        # Add to TF-IDF checker
        if self.tfidf_checker.enabled:
            self.tfidf_checker.add_document(doc_id, text)

        logger.info(f"Added document '{doc_id}' to plagiarism database")

    def remove_from_database(self, doc_id: str):
        """Remove document from internal database."""
        self.content_db.pop(doc_id, None)
        self.fingerprinter.fingerprint_db.pop(doc_id, None)
        self.semantic_checker.document_embeddings.pop(doc_id, None)
        self.tfidf_checker.documents.pop(doc_id, None)

    def compare_texts(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Compare two texts for similarity.

        Returns:
            Dictionary with similarity metrics
        """
        # Fingerprint similarity
        sig1 = self.fingerprinter.create_minhash_signature(text1)
        sig2 = self.fingerprinter.create_minhash_signature(text2)
        fingerprint_sim = self.fingerprinter.estimate_similarity(sig1, sig2)

        # Semantic similarity (if available)
        semantic_sim = 0.0
        if self.semantic_checker.enabled:
            emb1 = self.semantic_checker.get_embeddings([text1])
            emb2 = self.semantic_checker.get_embeddings([text2])
            if emb1 is not None and emb2 is not None:
                semantic_sim = float(np.dot(emb1[0], emb2[0]))

        # Word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        jaccard = len(words1 & words2) / len(words1 | words2) if words1 | words2 else 0

        # Combined score
        overall = (fingerprint_sim + semantic_sim + jaccard) / 3

        return {
            "overall_similarity": overall,
            "fingerprint_similarity": fingerprint_sim,
            "semantic_similarity": semantic_sim,
            "word_overlap": jaccard,
            "are_similar": overall > 0.5,
            "likely_plagiarism": overall > 0.7
        }

    def get_unique_phrases(self, text: str, min_length: int = 5) -> List[str]:
        """
        Extract phrases that appear to be unique/original.

        Args:
            text: Text to analyze
            min_length: Minimum phrase length in words

        Returns:
            List of unique phrases
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        unique_phrases = []

        for sentence in sentences:
            words = sentence.split()
            if len(words) < min_length:
                continue

            # Check if sentence matches anything in database
            similar = self.fingerprinter.find_similar(sentence, threshold=0.3)

            if not similar:
                unique_phrases.append(sentence.strip())

        return unique_phrases

    def get_stats(self) -> Dict[str, Any]:
        """Get checker statistics."""
        return {
            **self.stats,
            "documents_in_database": len(self.content_db),
            "copyscape_enabled": self.copyscape.enabled,
            "semantic_enabled": self.semantic_checker.enabled,
            "copyscape_credits": self.copyscape.get_credits()
        }


class BatchPlagiarismChecker:
    """Check multiple documents for plagiarism efficiently."""

    def __init__(self, checker: Optional[PlagiarismChecker] = None):
        self.checker = checker or PlagiarismChecker()

    def check_batch(self, documents: List[Dict[str, str]],
                    cross_check: bool = True) -> Dict[str, PlagiarismReport]:
        """
        Check multiple documents.

        Args:
            documents: List of {"id": "...", "text": "..."} dicts
            cross_check: Also check documents against each other

        Returns:
            Dictionary of doc_id -> PlagiarismReport
        """
        results = {}

        # First, add all documents to internal database if cross-checking
        if cross_check:
            for doc in documents:
                self.checker.add_to_database(
                    doc_id=doc["id"],
                    text=doc["text"],
                    title=doc.get("title")
                )

        # Check each document
        for doc in documents:
            # Temporarily remove from database to avoid self-match
            if cross_check:
                self.checker.remove_from_database(doc["id"])

            report = self.checker.check(doc["text"])
            results[doc["id"]] = report

            # Re-add for next document's cross-check
            if cross_check:
                self.checker.add_to_database(
                    doc_id=doc["id"],
                    text=doc["text"],
                    title=doc.get("title")
                )

        return results

    def generate_summary_report(self, results: Dict[str, PlagiarismReport]) -> Dict[str, Any]:
        """Generate summary report for batch check."""
        total_docs = len(results)
        original_docs = sum(1 for r in results.values() if r.is_original)
        avg_originality = sum(r.unique_content_percentage for r in results.values()) / total_docs if total_docs > 0 else 0

        risk_counts = Counter(r.risk_level for r in results.values())

        flagged_docs = [
            {"id": doc_id, "originality": r.unique_content_percentage, "risk": r.risk_level}
            for doc_id, r in results.items()
            if not r.is_original
        ]

        return {
            "total_documents": total_docs,
            "original_documents": original_docs,
            "flagged_documents": len(flagged_docs),
            "average_originality": avg_originality,
            "risk_distribution": dict(risk_counts),
            "flagged": sorted(flagged_docs, key=lambda x: x["originality"])
        }


# Convenience function
def check_plagiarism(text: str) -> PlagiarismReport:
    """Quick plagiarism check function."""
    checker = PlagiarismChecker()
    return checker.check(text)


if __name__ == "__main__":
    # Demo
    checker = PlagiarismChecker()

    # Add some content to internal database
    checker.add_to_database(
        "doc1",
        "The quick brown fox jumps over the lazy dog. This is a common pangram used in typing tests.",
        title="Sample Document 1"
    )

    checker.add_to_database(
        "doc2",
        "Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
        title="Sample Document 2"
    )

    # Check some text
    test_text = """
    The quick brown fox jumps over the lazy dog. This is a common pangram.

    Artificial intelligence is transforming how we work and live. Machine learning
    enables systems to improve from experience without being explicitly programmed.

    This is completely original content that should not match anything in the database.
    Creative writing about unique topics ensures high originality scores.
    """

    print("=" * 60)
    print("PLAGIARISM CHECKER DEMO")
    print("=" * 60)
    print("\nText being checked:")
    print(test_text[:200] + "...")

    report = checker.check(test_text)

    print("\n" + "-" * 60)
    print("RESULTS")
    print("-" * 60)
    print(f"Originality Score: {report.unique_content_percentage:.1f}%")
    print(f"Risk Level: {report.risk_level}")
    print(f"Is Original: {report.is_original}")
    print(f"Word Count: {report.word_count}")
    print(f"Matches Found: {len(report.matches)}")

    if report.matches:
        print("\nMatches:")
        for match in report.matches[:5]:
            print(f"\n  Type: {match.match_type}")
            print(f"  Source: {match.source_title}")
            print(f"  Similarity: {match.similarity_score:.2%}")
            if match.matched_text:
                print(f"  Text: '{match.matched_text[:50]}...'")

    print("\n" + "-" * 60)
    print("Checker Stats:")
    print("-" * 60)
    stats = checker.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
