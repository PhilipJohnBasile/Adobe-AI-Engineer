"""
Grammar Checker Module

Provides comprehensive grammar, spelling, and style checking with auto-correction
capabilities. Integrates with LanguageTool API and provides fallback local checking.
"""

import re
import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Optional imports with fallbacks
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False

try:
    import language_tool_python
    HAS_LANGUAGE_TOOL = True
except ImportError:
    HAS_LANGUAGE_TOOL = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Types of grammar/spelling issues."""
    SPELLING = "spelling"
    GRAMMAR = "grammar"
    PUNCTUATION = "punctuation"
    STYLE = "style"
    TYPOGRAPHY = "typography"
    REDUNDANCY = "redundancy"
    WORD_CHOICE = "word_choice"
    CAPITALIZATION = "capitalization"


class IssueSeverity(Enum):
    """Severity levels for issues."""
    ERROR = "error"
    WARNING = "warning"
    SUGGESTION = "suggestion"
    HINT = "hint"


@dataclass
class GrammarIssue:
    """Represents a grammar or spelling issue."""
    issue_id: str
    issue_type: IssueType
    severity: IssueSeverity
    message: str
    context: str
    offset: int
    length: int
    original_text: str
    suggestions: List[str]
    rule_id: Optional[str] = None
    rule_description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "context": self.context,
            "offset": self.offset,
            "length": self.length,
            "original_text": self.original_text,
            "suggestions": self.suggestions,
            "rule_id": self.rule_id,
            "rule_description": self.rule_description
        }


@dataclass
class CheckResult:
    """Result of grammar checking."""
    original_text: str
    issues: List[GrammarIssue]
    corrected_text: Optional[str]
    stats: Dict[str, Any]
    checked_at: datetime = field(default_factory=datetime.now)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "issues": [i.to_dict() for i in self.issues],
            "corrected_text": self.corrected_text,
            "stats": self.stats,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "checked_at": self.checked_at.isoformat()
        }


class LocalGrammarChecker:
    """Local grammar checking without external API."""

    def __init__(self):
        self.common_misspellings = self._load_common_misspellings()
        self.grammar_rules = self._build_grammar_rules()

    def _load_common_misspellings(self) -> Dict[str, str]:
        """Load dictionary of common misspellings."""
        return {
            "teh": "the",
            "recieve": "receive",
            "occured": "occurred",
            "seperate": "separate",
            "definately": "definitely",
            "accomodate": "accommodate",
            "occassion": "occasion",
            "neccessary": "necessary",
            "untill": "until",
            "wierd": "weird",
            "acheive": "achieve",
            "beleive": "believe",
            "calender": "calendar",
            "collegue": "colleague",
            "commited": "committed",
            "concious": "conscious",
            "embarass": "embarrass",
            "enviroment": "environment",
            "existance": "existence",
            "foriegn": "foreign",
            "goverment": "government",
            "grammer": "grammar",
            "harrass": "harass",
            "immediatly": "immediately",
            "independant": "independent",
            "knowlege": "knowledge",
            "liason": "liaison",
            "maintainance": "maintenance",
            "millenium": "millennium",
            "noticable": "noticeable",
            "paralell": "parallel",
            "persistant": "persistent",
            "playwrite": "playwright",
            "privelege": "privilege",
            "pronounciation": "pronunciation",
            "publically": "publicly",
            "recomend": "recommend",
            "refered": "referred",
            "relevent": "relevant",
            "resistence": "resistance",
            "responsability": "responsibility",
            "rythm": "rhythm",
            "succesful": "successful",
            "supercede": "supersede",
            "surprize": "surprise",
            "threshhold": "threshold",
            "tommorow": "tomorrow",
            "truely": "truly",
            "tyrany": "tyranny",
            "underate": "underrate",
            "unfortunatly": "unfortunately",
            "untill": "until",
            "whereever": "wherever",
            "writting": "writing",
            "your're": "you're",
            "it's" + " is": "it is",  # Common confusion
            "alot": "a lot",
            "could of": "could have",
            "should of": "should have",
            "would of": "would have",
        }

    def _build_grammar_rules(self) -> List[Dict[str, Any]]:
        """Build list of grammar checking rules."""
        return [
            {
                "id": "DOUBLE_SPACE",
                "pattern": r"  +",
                "replacement": " ",
                "message": "Multiple spaces should be a single space",
                "type": IssueType.TYPOGRAPHY,
                "severity": IssueSeverity.WARNING
            },
            {
                "id": "SPACE_BEFORE_PUNCTUATION",
                "pattern": r"\s+([.,;:!?])",
                "replacement": r"\1",
                "message": "Remove space before punctuation",
                "type": IssueType.PUNCTUATION,
                "severity": IssueSeverity.ERROR
            },
            {
                "id": "MISSING_SPACE_AFTER_PUNCTUATION",
                "pattern": r"([.,;:!?])([A-Za-z])",
                "replacement": r"\1 \2",
                "message": "Add space after punctuation",
                "type": IssueType.PUNCTUATION,
                "severity": IssueSeverity.ERROR
            },
            {
                "id": "DOUBLE_PUNCTUATION",
                "pattern": r"([.,;:!?]){2,}",
                "replacement": r"\1",
                "message": "Remove duplicate punctuation",
                "type": IssueType.PUNCTUATION,
                "severity": IssueSeverity.WARNING
            },
            {
                "id": "SENTENCE_START_LOWERCASE",
                "pattern": r"(?<=[.!?]\s)([a-z])",
                "message": "Sentence should start with uppercase letter",
                "type": IssueType.CAPITALIZATION,
                "severity": IssueSeverity.ERROR
            },
            {
                "id": "A_VS_AN_CONSONANT",
                "pattern": r"\b[Aa]n\s+(?=[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ](?![aeiouAEIOU]))",
                "message": "Use 'a' before consonant sounds",
                "type": IssueType.GRAMMAR,
                "severity": IssueSeverity.ERROR
            },
            {
                "id": "A_VS_AN_VOWEL",
                "pattern": r"\b[Aa]\s+(?=[aeiouAEIOU])",
                "message": "Use 'an' before vowel sounds",
                "type": IssueType.GRAMMAR,
                "severity": IssueSeverity.ERROR
            },
            {
                "id": "PASSIVE_VOICE",
                "pattern": r"\b(was|were|is|are|been|being)\s+(being\s+)?(\w+ed)\b",
                "message": "Consider using active voice instead of passive voice",
                "type": IssueType.STYLE,
                "severity": IssueSeverity.SUGGESTION
            },
            {
                "id": "REDUNDANT_PHRASE",
                "patterns": [
                    (r"\b(absolutely)\s+(essential|necessary)\b", "Use just 'essential' or 'necessary'"),
                    (r"\b(advance)\s+(planning|warning)\b", "Remove 'advance' - it's redundant"),
                    (r"\b(basic)\s+(fundamentals|essentials)\b", "Use just 'fundamentals' or 'essentials'"),
                    (r"\b(close)\s+(proximity)\b", "Use just 'proximity' or 'close'"),
                    (r"\b(completely)\s+(eliminate|finish)\b", "The verb already implies completion"),
                    (r"\b(end)\s+(result)\b", "Use just 'result'"),
                    (r"\b(free)\s+(gift)\b", "Gifts are free by definition"),
                    (r"\b(future)\s+(plans)\b", "Plans are for the future by definition"),
                    (r"\b(past)\s+(history)\b", "History is in the past by definition"),
                    (r"\b(personal)\s+(opinion)\b", "Opinions are personal by nature"),
                    (r"\b(unexpected)\s+(surprise)\b", "Surprises are unexpected by definition"),
                ],
                "type": IssueType.REDUNDANCY,
                "severity": IssueSeverity.SUGGESTION
            },
            {
                "id": "THEIR_THERE_THEY",
                "patterns": [
                    (r"\btheir\s+(is|are|was|were)\b", "Did you mean 'there'?"),
                    (r"\bthere\s+(car|house|dog|cat|name|friend|family)\b", "Did you mean 'their'?"),
                ],
                "type": IssueType.SPELLING,
                "severity": IssueSeverity.ERROR
            },
            {
                "id": "ITS_VS_ITS",
                "patterns": [
                    (r"\bit's\s+(own|way|place|time|best)\b", "Did you mean 'its' (possessive)?"),
                ],
                "type": IssueType.GRAMMAR,
                "severity": IssueSeverity.ERROR
            },
            {
                "id": "YOUR_YOURE",
                "patterns": [
                    (r"\byour\s+(going|coming|doing|being|having)\b", "Did you mean 'you're'?"),
                    (r"\byou're\s+(car|house|dog|cat|name|friend|family)\b", "Did you mean 'your'?"),
                ],
                "type": IssueType.GRAMMAR,
                "severity": IssueSeverity.ERROR
            },
            {
                "id": "AFFECT_EFFECT",
                "patterns": [
                    (r"\bthe\s+affect\s+of\b", "Did you mean 'effect' (noun)?"),
                    (r"\bto\s+effect\s+(?!change|a\s+change)\w+\b", "Did you mean 'affect' (verb)?"),
                ],
                "type": IssueType.WORD_CHOICE,
                "severity": IssueSeverity.WARNING
            },
            {
                "id": "REPEATED_WORDS",
                "pattern": r"\b(\w+)\s+\1\b",
                "message": "Word appears to be repeated",
                "type": IssueType.TYPOGRAPHY,
                "severity": IssueSeverity.WARNING
            },
            {
                "id": "MISSING_PERIOD",
                "pattern": r"[a-z]\s*$",
                "message": "Sentence may be missing ending punctuation",
                "type": IssueType.PUNCTUATION,
                "severity": IssueSeverity.HINT
            }
        ]

    def check(self, text: str) -> List[GrammarIssue]:
        """Check text for grammar and spelling issues."""
        issues = []
        issue_counter = 0

        # Check for misspellings
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            if word in self.common_misspellings:
                # Find all occurrences
                for match in re.finditer(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE):
                    issue_counter += 1
                    issues.append(GrammarIssue(
                        issue_id=f"spell_{issue_counter}",
                        issue_type=IssueType.SPELLING,
                        severity=IssueSeverity.ERROR,
                        message=f"'{word}' is commonly misspelled",
                        context=self._get_context(text, match.start(), match.end()),
                        offset=match.start(),
                        length=len(word),
                        original_text=match.group(),
                        suggestions=[self.common_misspellings[word]],
                        rule_id="COMMON_MISSPELLING"
                    ))

        # Apply grammar rules
        for rule in self.grammar_rules:
            if "patterns" in rule:
                # Multi-pattern rule
                for pattern, message in rule["patterns"]:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        issue_counter += 1
                        issues.append(GrammarIssue(
                            issue_id=f"grammar_{issue_counter}",
                            issue_type=rule["type"],
                            severity=rule["severity"],
                            message=message,
                            context=self._get_context(text, match.start(), match.end()),
                            offset=match.start(),
                            length=match.end() - match.start(),
                            original_text=match.group(),
                            suggestions=[],
                            rule_id=rule["id"]
                        ))
            elif "pattern" in rule:
                for match in re.finditer(rule["pattern"], text):
                    issue_counter += 1
                    suggestion = []
                    if "replacement" in rule:
                        try:
                            suggestion = [re.sub(rule["pattern"], rule["replacement"], match.group())]
                        except Exception:
                            pass

                    issues.append(GrammarIssue(
                        issue_id=f"grammar_{issue_counter}",
                        issue_type=rule["type"],
                        severity=rule["severity"],
                        message=rule["message"],
                        context=self._get_context(text, match.start(), match.end()),
                        offset=match.start(),
                        length=match.end() - match.start(),
                        original_text=match.group(),
                        suggestions=suggestion,
                        rule_id=rule["id"]
                    ))

        # Use TextBlob for additional spelling check if available
        if HAS_TEXTBLOB:
            try:
                blob = TextBlob(text)
                # TextBlob's spelling correction
                for word in blob.words:
                    corrected = word.correct()
                    if str(corrected) != str(word) and len(word) > 2:
                        # Find word in text
                        for match in re.finditer(r'\b' + re.escape(str(word)) + r'\b', text):
                            # Check if we already have this issue
                            existing = [i for i in issues if i.offset == match.start()]
                            if not existing:
                                issue_counter += 1
                                issues.append(GrammarIssue(
                                    issue_id=f"spell_{issue_counter}",
                                    issue_type=IssueType.SPELLING,
                                    severity=IssueSeverity.WARNING,
                                    message=f"Possible spelling error",
                                    context=self._get_context(text, match.start(), match.end()),
                                    offset=match.start(),
                                    length=len(word),
                                    original_text=str(word),
                                    suggestions=[str(corrected)],
                                    rule_id="TEXTBLOB_SPELLING"
                                ))
                            break  # Only report first occurrence
            except Exception as e:
                logger.debug(f"TextBlob check failed: {e}")

        # Sort by position
        issues.sort(key=lambda x: x.offset)

        return issues

    def _get_context(self, text: str, start: int, end: int, context_size: int = 30) -> str:
        """Get surrounding context for an issue."""
        ctx_start = max(0, start - context_size)
        ctx_end = min(len(text), end + context_size)

        prefix = "..." if ctx_start > 0 else ""
        suffix = "..." if ctx_end < len(text) else ""

        return prefix + text[ctx_start:ctx_end] + suffix

    def auto_correct(self, text: str, issues: List[GrammarIssue]) -> str:
        """Apply automatic corrections for issues with suggestions."""
        # Sort issues by offset in reverse order to maintain positions
        sorted_issues = sorted(issues, key=lambda x: x.offset, reverse=True)

        corrected = text
        for issue in sorted_issues:
            if issue.suggestions and issue.severity in [IssueSeverity.ERROR, IssueSeverity.WARNING]:
                # Apply first suggestion
                start = issue.offset
                end = issue.offset + issue.length
                corrected = corrected[:start] + issue.suggestions[0] + corrected[end:]

        return corrected


class LanguageToolChecker:
    """Grammar checking using LanguageTool API."""

    def __init__(self, language: str = "en-US"):
        self.language = language
        self.api_url = os.getenv("LANGUAGETOOL_API_URL", "https://api.languagetoolplus.com/v2/check")
        self.api_key = os.getenv("LANGUAGETOOL_API_KEY")
        self.tool = None

        # Try to use local LanguageTool if available
        if HAS_LANGUAGE_TOOL:
            try:
                self.tool = language_tool_python.LanguageTool(language)
                logger.info("Using local LanguageTool")
            except Exception as e:
                logger.warning(f"Could not initialize local LanguageTool: {e}")

    def check(self, text: str) -> List[GrammarIssue]:
        """Check text using LanguageTool."""
        if self.tool:
            return self._check_local(text)
        elif HAS_REQUESTS and self.api_key:
            return self._check_api(text)
        else:
            logger.warning("LanguageTool not available, using local checker")
            return []

    def _check_local(self, text: str) -> List[GrammarIssue]:
        """Check using local LanguageTool."""
        issues = []

        try:
            matches = self.tool.check(text)

            for i, match in enumerate(matches):
                issue_type = self._categorize_rule(match.ruleId)
                severity = self._determine_severity(match)

                issues.append(GrammarIssue(
                    issue_id=f"lt_{i}",
                    issue_type=issue_type,
                    severity=severity,
                    message=match.message,
                    context=match.context,
                    offset=match.offset,
                    length=match.errorLength,
                    original_text=text[match.offset:match.offset + match.errorLength],
                    suggestions=match.replacements[:5] if match.replacements else [],
                    rule_id=match.ruleId,
                    rule_description=match.ruleIssueType
                ))
        except Exception as e:
            logger.error(f"LanguageTool check failed: {e}")

        return issues

    def _check_api(self, text: str) -> List[GrammarIssue]:
        """Check using LanguageTool API."""
        issues = []

        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = requests.post(
                self.api_url,
                data={
                    "text": text,
                    "language": self.language
                },
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            for i, match in enumerate(data.get("matches", [])):
                issue_type = self._categorize_rule(match.get("rule", {}).get("id", ""))
                severity = IssueSeverity.WARNING

                if match.get("rule", {}).get("issueType") == "misspelling":
                    issue_type = IssueType.SPELLING
                    severity = IssueSeverity.ERROR

                issues.append(GrammarIssue(
                    issue_id=f"lt_api_{i}",
                    issue_type=issue_type,
                    severity=severity,
                    message=match.get("message", ""),
                    context=match.get("context", {}).get("text", ""),
                    offset=match.get("offset", 0),
                    length=match.get("length", 0),
                    original_text=text[match.get("offset", 0):match.get("offset", 0) + match.get("length", 0)],
                    suggestions=[r.get("value", "") for r in match.get("replacements", [])[:5]],
                    rule_id=match.get("rule", {}).get("id"),
                    rule_description=match.get("rule", {}).get("description")
                ))
        except Exception as e:
            logger.error(f"LanguageTool API check failed: {e}")

        return issues

    def _categorize_rule(self, rule_id: str) -> IssueType:
        """Categorize rule by ID."""
        rule_id = rule_id.upper()

        if "SPELL" in rule_id or "TYPO" in rule_id:
            return IssueType.SPELLING
        elif "PUNCT" in rule_id or "COMMA" in rule_id or "APOSTROPHE" in rule_id:
            return IssueType.PUNCTUATION
        elif "STYLE" in rule_id or "REDUNDANT" in rule_id:
            return IssueType.STYLE
        elif "TYPOGRAPHY" in rule_id or "WHITESPACE" in rule_id:
            return IssueType.TYPOGRAPHY
        elif "UPPERCASE" in rule_id or "LOWERCASE" in rule_id or "CASE" in rule_id:
            return IssueType.CAPITALIZATION
        else:
            return IssueType.GRAMMAR

    def _determine_severity(self, match) -> IssueSeverity:
        """Determine severity from LanguageTool match."""
        if hasattr(match, 'ruleIssueType'):
            issue_type = match.ruleIssueType.lower()
            if "error" in issue_type or "misspelling" in issue_type:
                return IssueSeverity.ERROR
            elif "style" in issue_type:
                return IssueSeverity.SUGGESTION
            elif "hint" in issue_type:
                return IssueSeverity.HINT
        return IssueSeverity.WARNING


class GrammarChecker:
    """
    Main grammar checker interface combining multiple checking engines.

    Usage:
        checker = GrammarChecker()
        result = checker.check("This is a sentance with errrors.")
        print(result.issues)
        print(result.corrected_text)
    """

    def __init__(self, language: str = "en-US"):
        self.language = language
        self.local_checker = LocalGrammarChecker()
        self.languagetool_checker = LanguageToolChecker(language)

        # Custom dictionaries
        self.ignored_words: set = set()
        self.custom_dictionary: Dict[str, str] = {}

        # Statistics
        self.stats = {
            "total_checks": 0,
            "total_issues": 0,
            "auto_corrections": 0
        }

        logger.info(f"Grammar checker initialized for language: {language}")

    def check(self, text: str,
              use_languagetool: bool = True,
              check_spelling: bool = True,
              check_grammar: bool = True,
              check_style: bool = True,
              auto_correct: bool = False) -> CheckResult:
        """
        Check text for grammar, spelling, and style issues.

        Args:
            text: Text to check
            use_languagetool: Whether to use LanguageTool (if available)
            check_spelling: Check for spelling errors
            check_grammar: Check for grammar issues
            check_style: Check for style suggestions
            auto_correct: Automatically apply corrections

        Returns:
            CheckResult with issues and optional corrected text
        """
        if not text or not text.strip():
            return CheckResult(
                original_text=text,
                issues=[],
                corrected_text=text,
                stats={"word_count": 0, "character_count": 0}
            )

        self.stats["total_checks"] += 1
        all_issues = []

        # Run local checker
        local_issues = self.local_checker.check(text)
        all_issues.extend(local_issues)

        # Run LanguageTool if enabled
        if use_languagetool:
            lt_issues = self.languagetool_checker.check(text)
            # Merge issues, avoiding duplicates at same position
            existing_positions = {(i.offset, i.length) for i in all_issues}
            for issue in lt_issues:
                if (issue.offset, issue.length) not in existing_positions:
                    all_issues.append(issue)

        # Filter by check types
        filtered_issues = []
        for issue in all_issues:
            if not check_spelling and issue.issue_type == IssueType.SPELLING:
                continue
            if not check_grammar and issue.issue_type == IssueType.GRAMMAR:
                continue
            if not check_style and issue.issue_type in [IssueType.STYLE, IssueType.REDUNDANCY]:
                continue

            # Check ignored words
            if issue.original_text.lower() in self.ignored_words:
                continue

            # Apply custom dictionary corrections
            if issue.original_text.lower() in self.custom_dictionary:
                issue.suggestions.insert(0, self.custom_dictionary[issue.original_text.lower()])

            filtered_issues.append(issue)

        # Sort by position
        filtered_issues.sort(key=lambda x: x.offset)

        # Auto-correct if requested
        corrected_text = None
        if auto_correct:
            corrected_text = self.local_checker.auto_correct(text, filtered_issues)
            self.stats["auto_corrections"] += 1

        self.stats["total_issues"] += len(filtered_issues)

        # Calculate stats
        words = text.split()
        stats = {
            "word_count": len(words),
            "character_count": len(text),
            "sentence_count": len(re.findall(r'[.!?]+', text)),
            "issue_count": len(filtered_issues),
            "issues_by_type": self._count_by_type(filtered_issues),
            "issues_by_severity": self._count_by_severity(filtered_issues)
        }

        return CheckResult(
            original_text=text,
            issues=filtered_issues,
            corrected_text=corrected_text,
            stats=stats
        )

    def check_and_correct(self, text: str) -> Tuple[str, List[GrammarIssue]]:
        """
        Check and automatically correct text.

        Returns:
            Tuple of (corrected_text, list of issues found)
        """
        result = self.check(text, auto_correct=True)
        return result.corrected_text or text, result.issues

    def add_to_dictionary(self, word: str, correction: Optional[str] = None):
        """Add word to custom dictionary or ignore list."""
        if correction:
            self.custom_dictionary[word.lower()] = correction
        else:
            self.ignored_words.add(word.lower())

    def remove_from_dictionary(self, word: str):
        """Remove word from custom dictionary and ignore list."""
        word = word.lower()
        self.ignored_words.discard(word)
        self.custom_dictionary.pop(word, None)

    def get_suggestions(self, text: str, position: int) -> List[str]:
        """Get correction suggestions for word at position."""
        # Find word at position
        words = list(re.finditer(r'\b\w+\b', text))

        for match in words:
            if match.start() <= position <= match.end():
                word = match.group()

                # Check custom dictionary
                if word.lower() in self.custom_dictionary:
                    return [self.custom_dictionary[word.lower()]]

                # Check common misspellings
                if word.lower() in self.local_checker.common_misspellings:
                    return [self.local_checker.common_misspellings[word.lower()]]

                # Use TextBlob if available
                if HAS_TEXTBLOB:
                    try:
                        blob = TextBlob(word)
                        corrected = str(blob.correct())
                        if corrected != word:
                            return [corrected]
                    except Exception:
                        pass

        return []

    def _count_by_type(self, issues: List[GrammarIssue]) -> Dict[str, int]:
        """Count issues by type."""
        counts = {}
        for issue in issues:
            type_name = issue.issue_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

    def _count_by_severity(self, issues: List[GrammarIssue]) -> Dict[str, int]:
        """Count issues by severity."""
        counts = {}
        for issue in issues:
            severity_name = issue.severity.value
            counts[severity_name] = counts.get(severity_name, 0) + 1
        return counts

    def get_stats(self) -> Dict[str, Any]:
        """Get checker statistics."""
        return {
            **self.stats,
            "ignored_words_count": len(self.ignored_words),
            "custom_dictionary_count": len(self.custom_dictionary)
        }


class RealTimeGrammarChecker:
    """
    Real-time grammar checking for editor integration.
    Provides incremental checking for performance.
    """

    def __init__(self, language: str = "en-US"):
        self.checker = GrammarChecker(language)
        self.cache: Dict[str, CheckResult] = {}
        self.max_cache_size = 100

    def check_incremental(self, text: str, changed_range: Optional[Tuple[int, int]] = None) -> List[GrammarIssue]:
        """
        Check text incrementally, focusing on changed areas.

        Args:
            text: Full text to check
            changed_range: Optional (start, end) of changed portion

        Returns:
            List of issues in the changed area
        """
        # For small texts or no range, check everything
        if len(text) < 500 or changed_range is None:
            return self.checker.check(text).issues

        # Extract paragraph containing the change
        start, end = changed_range

        # Find paragraph boundaries
        para_start = text.rfind('\n', 0, start)
        para_start = 0 if para_start == -1 else para_start + 1

        para_end = text.find('\n', end)
        para_end = len(text) if para_end == -1 else para_end

        # Check just the paragraph
        paragraph = text[para_start:para_end]
        result = self.checker.check(paragraph)

        # Adjust offsets to full document
        for issue in result.issues:
            issue.offset += para_start

        return result.issues

    def check_line(self, line: str) -> List[GrammarIssue]:
        """Check a single line (for real-time typing)."""
        # Use cache for performance
        cache_key = line.strip()[:100]  # Limit cache key length

        if cache_key in self.cache:
            return self.cache[cache_key].issues

        result = self.checker.check(line, use_languagetool=False)  # Fast local check only

        # Manage cache size
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest entries
            oldest_keys = list(self.cache.keys())[:10]
            for key in oldest_keys:
                del self.cache[key]

        self.cache[cache_key] = result

        return result.issues

    def clear_cache(self):
        """Clear the checking cache."""
        self.cache.clear()


# Convenience functions
def check_grammar(text: str, auto_correct: bool = False) -> CheckResult:
    """Quick grammar check function."""
    checker = GrammarChecker()
    return checker.check(text, auto_correct=auto_correct)


def correct_text(text: str) -> str:
    """Automatically correct text and return corrected version."""
    checker = GrammarChecker()
    corrected, _ = checker.check_and_correct(text)
    return corrected


if __name__ == "__main__":
    # Demo
    checker = GrammarChecker()

    test_text = """
    This is a sentance with some errrors. Their going to the store
    tommorow.  We recieved the package yesterday.

    The affect of this decision was significant. Your doing great work!
    Its important to check your grammer before publishing.
    """

    print("=" * 60)
    print("GRAMMAR CHECKER DEMO")
    print("=" * 60)
    print("\nOriginal text:")
    print(test_text)

    result = checker.check(test_text, auto_correct=True)

    print("\n" + "-" * 60)
    print(f"Found {len(result.issues)} issues:")
    print("-" * 60)

    for issue in result.issues:
        print(f"\n[{issue.severity.value.upper()}] {issue.issue_type.value}")
        print(f"  Message: {issue.message}")
        print(f"  Text: '{issue.original_text}'")
        if issue.suggestions:
            print(f"  Suggestions: {', '.join(issue.suggestions)}")

    if result.corrected_text:
        print("\n" + "-" * 60)
        print("Auto-corrected text:")
        print("-" * 60)
        print(result.corrected_text)

    print("\n" + "-" * 60)
    print("Statistics:")
    print("-" * 60)
    for key, value in result.stats.items():
        print(f"  {key}: {value}")
