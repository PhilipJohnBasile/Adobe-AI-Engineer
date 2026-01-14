#!/usr/bin/env python3
"""
Style Rules Engine

Custom settings to enforce specific formatting, terminology, or grammatical
rules across all generated content.

Features:
- Custom rule creation (grammar, terminology, formatting, tone)
- Rule validation and auto-fixing
- Pre-built rule sets (AP Style, Chicago, etc.)
- Team rule sharing
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of style rules"""
    GRAMMAR = "grammar"
    TERMINOLOGY = "terminology"
    FORMATTING = "formatting"
    TONE = "tone"
    BRAND = "brand"
    PUNCTUATION = "punctuation"
    CAPITALIZATION = "capitalization"


class RuleSeverity(Enum):
    """Rule severity levels"""
    ERROR = "error"      # Must fix
    WARNING = "warning"  # Should fix
    INFO = "info"        # Suggestion


@dataclass
class StyleRule:
    """A single style rule"""
    id: str
    name: str
    description: str
    rule_type: str
    pattern: str  # Regex pattern to match
    replacement: Optional[str] = None  # Auto-fix replacement
    message: str = ""  # Message to show when violated
    severity: str = RuleSeverity.WARNING.value
    enabled: bool = True
    case_sensitive: bool = False
    tags: List[str] = field(default_factory=list)
    examples: Dict[str, str] = field(default_factory=dict)  # bad -> good


@dataclass
class StyleViolation:
    """A detected style violation"""
    rule_id: str
    rule_name: str
    message: str
    severity: str
    matched_text: str
    position: Tuple[int, int]  # start, end
    suggestion: Optional[str] = None
    context: str = ""


@dataclass
class ValidationResult:
    """Result of style validation"""
    text: str
    violations: List[StyleViolation]
    error_count: int
    warning_count: int
    info_count: int
    score: float  # 0-100, higher is better
    auto_fixed_text: Optional[str] = None


class StyleRulesEngine:
    """
    Engine for enforcing style rules across content.

    Features:
    - Custom rule creation
    - Pre-built rule sets
    - Auto-fixing violations
    - Rule management
    """

    def __init__(self, storage_path: str = "data/style_rules"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.rules: Dict[str, StyleRule] = {}
        self._load_builtin_rules()
        self._load_custom_rules()

    def _load_builtin_rules(self):
        """Load built-in style rules"""

        # ========== GRAMMAR RULES ==========

        self.rules["oxford_comma"] = StyleRule(
            id="oxford_comma",
            name="Oxford Comma",
            description="Use Oxford comma before 'and' in lists",
            rule_type=RuleType.GRAMMAR.value,
            pattern=r"(\w+),\s+(\w+)\s+and\s+(\w+)",
            replacement=None,  # Complex rule, needs context
            message="Consider adding Oxford comma: '{matched}' -> '{matched[:-4]}, and{matched[-4:]}'",
            severity=RuleSeverity.INFO.value,
            examples={"red, white and blue": "red, white, and blue"}
        )

        self.rules["passive_voice"] = StyleRule(
            id="passive_voice",
            name="Passive Voice Detection",
            description="Detect passive voice constructions",
            rule_type=RuleType.GRAMMAR.value,
            pattern=r"\b(is|are|was|were|been|being)\s+(\w+ed)\b",
            replacement=None,
            message="Passive voice detected: '{matched}'. Consider using active voice.",
            severity=RuleSeverity.INFO.value,
            examples={"was completed": "completed", "is used": "uses"}
        )

        self.rules["double_spaces"] = StyleRule(
            id="double_spaces",
            name="Double Spaces",
            description="Remove double spaces",
            rule_type=RuleType.FORMATTING.value,
            pattern=r"  +",
            replacement=" ",
            message="Multiple spaces detected",
            severity=RuleSeverity.WARNING.value
        )

        self.rules["sentence_space"] = StyleRule(
            id="sentence_space",
            name="Single Space After Period",
            description="Use single space after period",
            rule_type=RuleType.PUNCTUATION.value,
            pattern=r"\.\s{2,}",
            replacement=". ",
            message="Use single space after period",
            severity=RuleSeverity.WARNING.value
        )

        # ========== PUNCTUATION RULES ==========

        self.rules["no_double_punctuation"] = StyleRule(
            id="no_double_punctuation",
            name="No Double Punctuation",
            description="Avoid double punctuation marks",
            rule_type=RuleType.PUNCTUATION.value,
            pattern=r"([!?.])\1+",
            replacement=r"\1",
            message="Remove duplicate punctuation",
            severity=RuleSeverity.ERROR.value,
            examples={"!!": "!", "??": "?", "..": "."}
        )

        self.rules["smart_quotes"] = StyleRule(
            id="smart_quotes",
            name="Smart Quotes",
            description="Use smart quotes instead of straight quotes",
            rule_type=RuleType.FORMATTING.value,
            pattern=r'"([^"]*)"',
            replacement=None,  # Handled specially
            message="Consider using smart quotes",
            severity=RuleSeverity.INFO.value,
            examples={'"hello"': '"hello"'}
        )

        self.rules["ellipsis"] = StyleRule(
            id="ellipsis",
            name="Proper Ellipsis",
            description="Use proper ellipsis character",
            rule_type=RuleType.PUNCTUATION.value,
            pattern=r"\.{3}",
            replacement="…",
            message="Use proper ellipsis character (…)",
            severity=RuleSeverity.INFO.value
        )

        # ========== CAPITALIZATION RULES ==========

        self.rules["sentence_caps"] = StyleRule(
            id="sentence_caps",
            name="Sentence Capitalization",
            description="Sentences should start with capital letter",
            rule_type=RuleType.CAPITALIZATION.value,
            pattern=r"(?<=[.!?]\s)([a-z])",
            replacement=None,  # Handled specially
            message="Sentence should start with capital letter",
            severity=RuleSeverity.ERROR.value
        )

        self.rules["no_all_caps"] = StyleRule(
            id="no_all_caps",
            name="No All Caps",
            description="Avoid all caps words (except acronyms)",
            rule_type=RuleType.TONE.value,
            pattern=r"\b[A-Z]{4,}\b",
            replacement=None,
            message="Avoid all caps: '{matched}'",
            severity=RuleSeverity.WARNING.value,
            tags=["tone", "professional"]
        )

        # ========== TERMINOLOGY RULES ==========

        self.rules["email_spelling"] = StyleRule(
            id="email_spelling",
            name="Email Spelling",
            description="Use 'email' not 'e-mail'",
            rule_type=RuleType.TERMINOLOGY.value,
            pattern=r"\be-mail\b",
            replacement="email",
            message="Use 'email' instead of 'e-mail'",
            severity=RuleSeverity.WARNING.value,
            case_sensitive=False
        )

        self.rules["website_spelling"] = StyleRule(
            id="website_spelling",
            name="Website Spelling",
            description="Use 'website' not 'web site'",
            rule_type=RuleType.TERMINOLOGY.value,
            pattern=r"\bweb\s+site\b",
            replacement="website",
            message="Use 'website' instead of 'web site'",
            severity=RuleSeverity.WARNING.value,
            case_sensitive=False
        )

        self.rules["internet_caps"] = StyleRule(
            id="internet_caps",
            name="Internet Capitalization",
            description="Lowercase 'internet'",
            rule_type=RuleType.CAPITALIZATION.value,
            pattern=r"\bInternet\b",
            replacement="internet",
            message="Use lowercase 'internet'",
            severity=RuleSeverity.INFO.value
        )

        # ========== TONE RULES ==========

        self.rules["no_exclamation_overuse"] = StyleRule(
            id="no_exclamation_overuse",
            name="Exclamation Mark Moderation",
            description="Avoid overusing exclamation marks",
            rule_type=RuleType.TONE.value,
            pattern=r"!(?=.*!.*!)",
            replacement=None,
            message="Consider reducing exclamation mark usage",
            severity=RuleSeverity.INFO.value,
            tags=["professional", "tone"]
        )

        self.rules["no_very"] = StyleRule(
            id="no_very",
            name="Avoid 'Very'",
            description="Replace 'very' with stronger words",
            rule_type=RuleType.TONE.value,
            pattern=r"\bvery\s+(\w+)",
            replacement=None,
            message="Consider replacing 'very {matched}' with a stronger word",
            severity=RuleSeverity.INFO.value,
            examples={
                "very good": "excellent",
                "very bad": "terrible",
                "very big": "huge",
                "very small": "tiny"
            }
        )

        # ========== BRAND RULES ==========

        self.rules["trademark_symbols"] = StyleRule(
            id="trademark_symbols",
            name="Trademark Symbols",
            description="Ensure proper trademark symbols on first use",
            rule_type=RuleType.BRAND.value,
            pattern=r"(?<![®™])\b(iPhone|iPad|Android|Windows|Google|Facebook|Instagram)\b(?![®™])",
            replacement=None,
            message="Consider adding trademark symbol on first use: '{matched}'",
            severity=RuleSeverity.INFO.value
        )

        logger.info(f"Loaded {len(self.rules)} built-in style rules")

    def _load_custom_rules(self):
        """Load custom rules from disk"""
        rules_file = self.storage_path / "custom_rules.json"
        if rules_file.exists():
            try:
                with open(rules_file, 'r') as f:
                    custom_rules = json.load(f)
                for rule_data in custom_rules:
                    rule = StyleRule(**rule_data)
                    self.rules[rule.id] = rule
                logger.info(f"Loaded {len(custom_rules)} custom rules")
            except Exception as e:
                logger.error(f"Error loading custom rules: {e}")

    def _save_custom_rules(self):
        """Save custom rules to disk"""
        custom_rules = [
            asdict(rule) for rule in self.rules.values()
            if rule.id not in self._get_builtin_rule_ids()
        ]
        rules_file = self.storage_path / "custom_rules.json"
        with open(rules_file, 'w') as f:
            json.dump(custom_rules, f, indent=2)

    def _get_builtin_rule_ids(self) -> set:
        """Get IDs of built-in rules"""
        return {
            "oxford_comma", "passive_voice", "double_spaces", "sentence_space",
            "no_double_punctuation", "smart_quotes", "ellipsis", "sentence_caps",
            "no_all_caps", "email_spelling", "website_spelling", "internet_caps",
            "no_exclamation_overuse", "no_very", "trademark_symbols"
        }

    def add_rule(self, rule: StyleRule) -> bool:
        """Add a custom rule"""
        try:
            # Validate regex pattern
            re.compile(rule.pattern)
            self.rules[rule.id] = rule
            self._save_custom_rules()
            return True
        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return False

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a custom rule"""
        if rule_id in self._get_builtin_rule_ids():
            logger.warning("Cannot remove built-in rule")
            return False

        if rule_id in self.rules:
            del self.rules[rule_id]
            self._save_custom_rules()
            return True
        return False

    def enable_rule(self, rule_id: str, enabled: bool = True) -> bool:
        """Enable or disable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = enabled
            return True
        return False

    def check_content(
        self,
        content: str,
        rule_types: List[str] = None,
        severity_threshold: str = None
    ) -> ValidationResult:
        """
        Check content against style rules.

        Args:
            content: Content to check
            rule_types: Filter by rule types
            severity_threshold: Minimum severity to report

        Returns:
            ValidationResult with violations
        """
        violations = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            if rule_types and rule.rule_type not in rule_types:
                continue

            # Apply regex
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(rule.pattern, flags)
            except re.error:
                continue

            for match in pattern.finditer(content):
                # Check severity threshold
                if severity_threshold:
                    if self._severity_below_threshold(rule.severity, severity_threshold):
                        continue

                # Create violation
                matched_text = match.group(0)
                start, end = match.span()

                # Get context
                context_start = max(0, start - 30)
                context_end = min(len(content), end + 30)
                context = content[context_start:context_end]

                # Calculate suggestion
                suggestion = None
                if rule.replacement:
                    suggestion = pattern.sub(rule.replacement, matched_text, count=1)

                violation = StyleViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    message=rule.message.replace("{matched}", matched_text),
                    severity=rule.severity,
                    matched_text=matched_text,
                    position=(start, end),
                    suggestion=suggestion,
                    context=f"...{context}..."
                )
                violations.append(violation)

        # Count by severity
        error_count = sum(1 for v in violations if v.severity == RuleSeverity.ERROR.value)
        warning_count = sum(1 for v in violations if v.severity == RuleSeverity.WARNING.value)
        info_count = sum(1 for v in violations if v.severity == RuleSeverity.INFO.value)

        # Calculate score (100 - penalties)
        penalty = error_count * 10 + warning_count * 3 + info_count * 1
        score = max(0, 100 - penalty)

        return ValidationResult(
            text=content,
            violations=violations,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            score=score
        )

    def _severity_below_threshold(self, severity: str, threshold: str) -> bool:
        """Check if severity is below threshold"""
        severity_order = {
            RuleSeverity.INFO.value: 0,
            RuleSeverity.WARNING.value: 1,
            RuleSeverity.ERROR.value: 2
        }
        return severity_order.get(severity, 0) < severity_order.get(threshold, 0)

    def auto_fix(self, content: str, rule_ids: List[str] = None) -> Tuple[str, List[str]]:
        """
        Automatically fix violations where possible.

        Args:
            content: Content to fix
            rule_ids: Specific rules to apply (all if None)

        Returns:
            Tuple of (fixed_content, list of fixes applied)
        """
        fixed_content = content
        fixes_applied = []

        for rule in self.rules.values():
            if not rule.enabled or not rule.replacement:
                continue

            if rule_ids and rule.id not in rule_ids:
                continue

            # Apply replacement
            flags = 0 if rule.case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(rule.pattern, flags)
                matches = pattern.findall(fixed_content)

                if matches:
                    fixed_content = pattern.sub(rule.replacement, fixed_content)
                    fixes_applied.append(f"{rule.name}: {len(matches) if isinstance(matches, list) else 1} fix(es)")

            except re.error:
                continue

        return fixed_content, fixes_applied

    def list_rules(
        self,
        rule_type: str = None,
        enabled_only: bool = False
    ) -> List[Dict[str, Any]]:
        """List all rules"""
        rules = list(self.rules.values())

        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]

        if enabled_only:
            rules = [r for r in rules if r.enabled]

        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "type": r.rule_type,
                "severity": r.severity,
                "enabled": r.enabled,
                "builtin": r.id in self._get_builtin_rule_ids()
            }
            for r in rules
        ]

    def get_rule_types(self) -> List[Dict[str, Any]]:
        """Get available rule types"""
        return [
            {"id": rt.value, "name": rt.value.title()}
            for rt in RuleType
        ]

    def create_rule_set(
        self,
        name: str,
        rule_ids: List[str]
    ) -> Dict[str, Any]:
        """Create a named set of rules"""
        rule_set = {
            "name": name,
            "rules": rule_ids,
            "created_at": datetime.now().isoformat()
        }

        # Save rule set
        sets_file = self.storage_path / "rule_sets.json"
        sets = {}
        if sets_file.exists():
            with open(sets_file, 'r') as f:
                sets = json.load(f)

        sets[name] = rule_set
        with open(sets_file, 'w') as f:
            json.dump(sets, f, indent=2)

        return rule_set

    def apply_rule_set(self, name: str) -> bool:
        """Apply a rule set (enable only those rules)"""
        sets_file = self.storage_path / "rule_sets.json"
        if not sets_file.exists():
            return False

        with open(sets_file, 'r') as f:
            sets = json.load(f)

        if name not in sets:
            return False

        rule_ids = sets[name].get("rules", [])

        # Disable all, then enable set rules
        for rule in self.rules.values():
            rule.enabled = rule.id in rule_ids

        return True


# Pre-built rule sets
class RuleSets:
    """Pre-built rule sets for common style guides"""

    @staticmethod
    def ap_style() -> List[str]:
        """AP Style rules"""
        return [
            "email_spelling", "website_spelling", "internet_caps",
            "no_double_punctuation", "double_spaces", "sentence_caps"
        ]

    @staticmethod
    def professional() -> List[str]:
        """Professional writing rules"""
        return [
            "no_all_caps", "no_exclamation_overuse", "passive_voice",
            "double_spaces", "sentence_caps", "no_double_punctuation"
        ]

    @staticmethod
    def casual() -> List[str]:
        """Casual writing rules (minimal)"""
        return ["double_spaces", "no_double_punctuation"]

    @staticmethod
    def marketing() -> List[str]:
        """Marketing content rules"""
        return [
            "no_very", "double_spaces", "sentence_caps",
            "no_double_punctuation"
        ]


# Demo function
def demo_style_rules():
    """Demonstrate style rules engine"""
    print("Style Rules Engine Demo")
    print("=" * 50)

    engine = StyleRulesEngine()

    # Show available rule types
    print("\n1. Available rule types:")
    for rt in engine.get_rule_types():
        print(f"   - {rt['name']}")

    # Show rules count
    print(f"\n2. Total rules: {len(engine.rules)}")
    for rt in RuleType:
        count = len([r for r in engine.rules.values() if r.rule_type == rt.value])
        print(f"   - {rt.value}: {count}")

    # Check sample content
    print("\n3. Checking sample content...")
    sample = """
    This is a sample text with some  double spaces. Also e-mail should be email!!
    The Internet is VERY important. This content was completed yesterday.
    """

    result = engine.check_content(sample)
    print(f"   Score: {result.score}/100")
    print(f"   Errors: {result.error_count}")
    print(f"   Warnings: {result.warning_count}")
    print(f"   Info: {result.info_count}")

    print("\n   Violations found:")
    for v in result.violations[:5]:
        print(f"   - [{v.severity}] {v.rule_name}: {v.message}")

    # Auto-fix
    print("\n4. Auto-fixing content...")
    fixed, fixes = engine.auto_fix(sample)
    print(f"   Fixes applied: {len(fixes)}")
    for fix in fixes:
        print(f"   - {fix}")

    print("\n Demo complete!")


if __name__ == "__main__":
    demo_style_rules()
