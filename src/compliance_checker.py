"""
Compliance Checker - Handles brand compliance and legal content validation.
"""

import logging
import re
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ComplianceChecker:
    """Validates content for brand compliance and legal requirements."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/compliance_rules.json")
        self.rules = self._load_compliance_rules()
        logger.info("Compliance checker initialized")
    
    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance rules from configuration file."""
        
        # Default compliance rules
        default_rules = {
            "prohibited_words": {
                "medical_claims": [
                    "cure", "cures", "treatment", "medical", "medicine",
                    "drug", "prescription", "therapeutic", "healing",
                    "disease", "diagnosis", "clinical", "doctor approved"
                ],
                "absolute_claims": [
                    "guaranteed", "100% effective", "miracle", "magic",
                    "instant", "overnight", "permanent", "forever",
                    "completely eliminates", "totally removes"
                ],
                "inappropriate_content": [
                    "addiction", "addictive", "drugs", "alcohol",
                    "smoking", "tobacco", "gambling", "violence"
                ],
                "competitive_claims": [
                    "better than", "superior to", "beats competition",
                    "number one", "#1", "best in market", "destroys competition"
                ],
                "age_restricted": [
                    "children under", "not for kids", "adult only",
                    "18+", "21+", "mature audiences"
                ]
            },
            "required_disclaimers": {
                "skincare": [
                    "individual results may vary",
                    "for external use only",
                    "consult dermatologist"
                ],
                "supplements": [
                    "not evaluated by FDA",
                    "not intended to diagnose",
                    "consult physician"
                ]
            },
            "brand_requirements": {
                "logo_placement": {
                    "required": True,
                    "min_size_percent": 5,
                    "preferred_positions": ["top-right", "bottom-right"]
                },
                "color_compliance": {
                    "required": True,
                    "tolerance_percent": 10
                },
                "font_requirements": {
                    "brand_fonts_only": False,
                    "readable_contrast": True
                }
            },
            "content_guidelines": {
                "max_text_density": 0.3,
                "min_contrast_ratio": 4.5,
                "inclusive_language": True,
                "accessibility_compliant": True
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_rules = json.load(f)
                # Merge with defaults
                default_rules.update(loaded_rules)
                logger.info(f"Loaded compliance rules from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load compliance rules: {e}, using defaults")
        
        return default_rules
    
    def check_campaign_brief(self, campaign_brief: Dict[str, Any]) -> Dict[str, Any]:
        """Check campaign brief for compliance issues."""
        
        issues = {
            "critical": [],
            "warnings": [],
            "suggestions": [],
            "passed_checks": []
        }
        
        brief_data = campaign_brief.get('campaign_brief', {})
        
        # Check campaign message
        campaign_message = brief_data.get('campaign_message', '')
        if campaign_message:
            message_issues = self._check_text_content(campaign_message, 'campaign_message')
            self._merge_issues(issues, message_issues)
        
        # Check product descriptions
        products = brief_data.get('products', [])
        for i, product in enumerate(products):
            product_name = product.get('name', f'Product {i+1}')
            description = product.get('description', '')
            
            if description:
                desc_issues = self._check_text_content(description, f'product_{i}_description')
                self._merge_issues(issues, desc_issues)
            
            # Check for required disclaimers based on product type
            self._check_disclaimers(product, issues)
        
        # Check brand guidelines compliance
        brand_guidelines = brief_data.get('brand_guidelines', {})
        if brand_guidelines:
            brand_issues = self._check_brand_guidelines(brand_guidelines)
            self._merge_issues(issues, brand_issues)
        
        # Calculate compliance score
        total_checks = len(issues['critical']) + len(issues['warnings']) + len(issues['suggestions']) + len(issues['passed_checks'])
        compliance_score = len(issues['passed_checks']) / max(total_checks, 1) * 100
        
        return {
            'compliance_score': compliance_score,
            'issues': issues,
            'recommendation': self._get_recommendation(issues),
            'checked_at': self._get_timestamp()
        }
    
    def _check_text_content(self, text: str, context: str) -> Dict[str, List]:
        """Check text content for prohibited words and phrases."""
        
        issues = {
            "critical": [],
            "warnings": [],
            "suggestions": [],
            "passed_checks": []
        }
        
        text_lower = text.lower()
        
        # Check prohibited words
        for category, words in self.rules['prohibited_words'].items():
            found_words = []
            for word in words:
                if re.search(r'\b' + re.escape(word.lower()) + r'\b', text_lower):
                    found_words.append(word)
            
            if found_words:
                severity = self._get_violation_severity(category)
                issue = {
                    'type': 'prohibited_content',
                    'category': category,
                    'context': context,
                    'found_words': found_words,
                    'text_snippet': text[:100] + '...' if len(text) > 100 else text,
                    'recommendation': f'Remove or replace prohibited {category} terms: {", ".join(found_words)}'
                }
                issues[severity].append(issue)
            else:
                issues['passed_checks'].append(f'{category}_check_passed')
        
        # Check for inclusive language
        if self.rules['content_guidelines']['inclusive_language']:
            inclusive_issues = self._check_inclusive_language(text, context)
            self._merge_issues(issues, inclusive_issues)
        
        return issues
    
    def _check_inclusive_language(self, text: str, context: str) -> Dict[str, List]:
        """Check for inclusive language compliance."""
        
        issues = {
            "critical": [],
            "warnings": [],
            "suggestions": [],
            "passed_checks": []
        }
        
        # Terms that should be avoided for inclusivity
        problematic_terms = {
            'gendered_assumptions': [
                'guys', 'mankind', 'manpower', 'chairman',
                'businessmen', 'policeman', 'fireman'
            ],
            'ableist_language': [
                'crazy', 'insane', 'lame', 'blind to',
                'deaf to', 'dumb', 'stupid'
            ],
            'age_discrimination': [
                'young people only', 'seniors can\'t', 'too old',
                'kids these days', 'boomer'
            ]
        }
        
        text_lower = text.lower()
        
        for category, terms in problematic_terms.items():
            found_terms = []
            for term in terms:
                if term in text_lower:
                    found_terms.append(term)
            
            if found_terms:
                issue = {
                    'type': 'inclusive_language',
                    'category': category,
                    'context': context,
                    'found_terms': found_terms,
                    'recommendation': f'Consider more inclusive alternatives for: {", ".join(found_terms)}'
                }
                issues['suggestions'].append(issue)
            else:
                issues['passed_checks'].append(f'{category}_inclusive_check_passed')
        
        return issues
    
    def _check_disclaimers(self, product: Dict[str, Any], issues: Dict[str, List]) -> None:
        """Check if required disclaimers are present for product type."""
        
        product_name = product.get('name', '').lower()
        description = product.get('description', '').lower()
        
        # Determine product category
        product_category = None
        if any(term in product_name + description for term in ['serum', 'cream', 'lotion', 'skincare']):
            product_category = 'skincare'
        elif any(term in product_name + description for term in ['supplement', 'vitamin', 'pill', 'capsule']):
            product_category = 'supplements'
        
        if product_category and product_category in self.rules['required_disclaimers']:
            required_disclaimers = self.rules['required_disclaimers'][product_category]
            missing_disclaimers = []
            
            for disclaimer in required_disclaimers:
                if disclaimer.lower() not in description:
                    missing_disclaimers.append(disclaimer)
            
            if missing_disclaimers:
                issue = {
                    'type': 'missing_disclaimers',
                    'category': product_category,
                    'context': f'product_{product.get("name", "unknown")}',
                    'missing_disclaimers': missing_disclaimers,
                    'recommendation': f'Add required disclaimers: {", ".join(missing_disclaimers)}'
                }
                issues['warnings'].append(issue)
            else:
                issues['passed_checks'].append(f'{product_category}_disclaimers_present')
    
    def _check_brand_guidelines(self, brand_guidelines: Dict[str, Any]) -> Dict[str, List]:
        """Check brand guidelines compliance."""
        
        issues = {
            "critical": [],
            "warnings": [],
            "suggestions": [],
            "passed_checks": []
        }
        
        brand_reqs = self.rules['brand_requirements']
        
        # Check logo requirements
        if brand_reqs['logo_placement']['required']:
            if not brand_guidelines.get('logo_required', False):
                issue = {
                    'type': 'brand_compliance',
                    'category': 'logo_missing',
                    'recommendation': 'Brand guidelines require logo placement'
                }
                issues['warnings'].append(issue)
            else:
                issues['passed_checks'].append('logo_requirement_met')
        
        # Check color compliance
        if brand_reqs['color_compliance']['required']:
            primary_colors = brand_guidelines.get('primary_colors', [])
            if not primary_colors:
                issue = {
                    'type': 'brand_compliance',
                    'category': 'colors_missing',
                    'recommendation': 'Define primary brand colors for compliance'
                }
                issues['suggestions'].append(issue)
            else:
                issues['passed_checks'].append('brand_colors_defined')
        
        return issues
    
    def _get_violation_severity(self, category: str) -> str:
        """Determine severity level for different violation categories."""
        
        critical_categories = ['medical_claims', 'inappropriate_content']
        warning_categories = ['absolute_claims', 'competitive_claims']
        
        if category in critical_categories:
            return 'critical'
        elif category in warning_categories:
            return 'warnings'
        else:
            return 'suggestions'
    
    def _merge_issues(self, target: Dict[str, List], source: Dict[str, List]) -> None:
        """Merge issue dictionaries."""
        for key in target:
            if key in source:
                target[key].extend(source[key])
    
    def _get_recommendation(self, issues: Dict[str, List]) -> str:
        """Generate overall recommendation based on issues found."""
        
        critical_count = len(issues['critical'])
        warning_count = len(issues['warnings'])
        suggestion_count = len(issues['suggestions'])
        
        if critical_count > 0:
            return f"BLOCKED: {critical_count} critical compliance issues must be resolved before proceeding."
        elif warning_count > 0:
            return f"REVIEW REQUIRED: {warning_count} warnings should be addressed before launch."
        elif suggestion_count > 0:
            return f"APPROVED WITH SUGGESTIONS: {suggestion_count} minor improvements recommended."
        else:
            return "APPROVED: All compliance checks passed."
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for compliance check."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_compliance_report(self, campaign_brief: Dict[str, Any]) -> str:
        """Generate a human-readable compliance report."""
        
        result = self.check_campaign_brief(campaign_brief)
        
        report_lines = [
            "=" * 60,
            "COMPLIANCE REPORT",
            "=" * 60,
            f"Campaign: {campaign_brief.get('campaign_brief', {}).get('campaign_id', 'Unknown')}",
            f"Checked at: {result['checked_at']}",
            f"Compliance Score: {result['compliance_score']:.1f}%",
            f"Overall Status: {result['recommendation']}",
            ""
        ]
        
        issues = result['issues']
        
        # Critical issues
        if issues['critical']:
            report_lines.extend([
                "🚨 CRITICAL ISSUES (Must Fix):",
                "-" * 40
            ])
            for issue in issues['critical']:
                report_lines.append(f"• {issue['recommendation']}")
                if 'found_words' in issue:
                    report_lines.append(f"  Found: {', '.join(issue['found_words'])}")
            report_lines.append("")
        
        # Warnings
        if issues['warnings']:
            report_lines.extend([
                "⚠️  WARNINGS (Should Fix):",
                "-" * 40
            ])
            for issue in issues['warnings']:
                report_lines.append(f"• {issue['recommendation']}")
            report_lines.append("")
        
        # Suggestions
        if issues['suggestions']:
            report_lines.extend([
                "💡 SUGGESTIONS (Consider):",
                "-" * 40
            ])
            for issue in issues['suggestions']:
                report_lines.append(f"• {issue['recommendation']}")
            report_lines.append("")
        
        # Passed checks
        if issues['passed_checks']:
            report_lines.extend([
                "✅ PASSED CHECKS:",
                "-" * 40
            ])
            passed_summary = {}
            for check in issues['passed_checks']:
                category = check.split('_')[0]
                passed_summary[category] = passed_summary.get(category, 0) + 1
            
            for category, count in passed_summary.items():
                report_lines.append(f"• {category.title()}: {count} checks passed")
        
        return "\n".join(report_lines)