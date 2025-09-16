"""
Free Content Moderation and Brand Safety System
Uses open-source libraries and free APIs for content analysis
"""

import re
import json
import requests
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from PIL import Image, ImageStat
import numpy as np
from datetime import datetime
import os


class ContentRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModerationCategory(Enum):
    SAFE = "safe"
    ADULT = "adult"
    VIOLENCE = "violence"
    HATE_SPEECH = "hate_speech"
    DRUGS = "drugs"
    WEAPONS = "weapons"
    GAMBLING = "gambling"
    INAPPROPRIATE = "inappropriate"


@dataclass
class ModerationResult:
    """Result of content moderation analysis"""
    category: ModerationCategory
    risk_level: ContentRisk
    confidence: float
    flags: List[str]
    details: Dict[str, Any]
    timestamp: str


class TextModerator:
    """Free text content moderation using keyword analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Comprehensive keyword lists (free alternative to paid services)
        self.risk_keywords = {
            ModerationCategory.ADULT: [
                "explicit", "adult", "pornographic", "sexual", "nude", "naked",
                "sex", "porn", "xxx", "erotic", "intimate", "seductive"
            ],
            ModerationCategory.VIOLENCE: [
                "violence", "violent", "kill", "murder", "death", "weapon", "gun",
                "knife", "blood", "fight", "attack", "assault", "torture"
            ],
            ModerationCategory.HATE_SPEECH: [
                "hate", "racist", "discrimination", "bigot", "supremacist",
                "offensive", "slur", "derogatory", "harassment"
            ],
            ModerationCategory.DRUGS: [
                "drugs", "cocaine", "heroin", "marijuana", "cannabis", "meth",
                "addiction", "substance", "illegal drugs", "narcotics"
            ],
            ModerationCategory.WEAPONS: [
                "weapons", "firearms", "ammunition", "explosives", "bomb",
                "terrorist", "warfare", "military grade"
            ],
            ModerationCategory.GAMBLING: [
                "gambling", "casino", "betting", "poker", "slots", "lottery",
                "wager", "jackpot", "odds", "blackjack"
            ]
        }
        
        # Medical claims (compliance risk)
        self.medical_keywords = [
            "cure", "treat", "heal", "medical", "therapeutic", "clinical",
            "FDA approved", "doctor recommended", "scientifically proven",
            "miracle", "breakthrough", "revolutionary treatment"
        ]
        
        # Brand safety keywords
        self.brand_unsafe_keywords = [
            "controversial", "scandal", "bankruptcy", "lawsuit", "fraud",
            "crisis", "disaster", "tragedy", "accident", "emergency"
        ]
    
    def moderate_text(self, text: str, context: str = "general") -> ModerationResult:
        """Moderate text content for safety and compliance"""
        if not text:
            return ModerationResult(
                ModerationCategory.SAFE, ContentRisk.LOW, 1.0, [],
                {"message": "No text to analyze"}, datetime.now().isoformat()
            )
        
        text_lower = text.lower()
        flags = []
        risk_scores = {}
        
        # Check each category
        for category, keywords in self.risk_keywords.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                flags.extend([f"{category.value}:{kw}" for kw in matches])
                risk_scores[category] = len(matches) / len(keywords)
        
        # Check medical claims
        medical_matches = [kw for kw in self.medical_keywords if kw in text_lower]
        if medical_matches:
            flags.extend([f"medical_claim:{kw}" for kw in medical_matches])
            risk_scores[ModerationCategory.INAPPROPRIATE] = len(medical_matches) / len(self.medical_keywords)
        
        # Check brand safety
        brand_unsafe_matches = [kw for kw in self.brand_unsafe_keywords if kw in text_lower]
        if brand_unsafe_matches:
            flags.extend([f"brand_unsafe:{kw}" for kw in brand_unsafe_matches])
        
        # Determine overall category and risk
        if not risk_scores:
            category = ModerationCategory.SAFE
            risk_level = ContentRisk.LOW
            confidence = 0.95
        else:
            # Find highest risk category
            category = max(risk_scores.keys(), key=lambda k: risk_scores[k])
            max_score = risk_scores[category]
            
            # Determine risk level based on score
            if max_score >= 0.5:
                risk_level = ContentRisk.CRITICAL
            elif max_score >= 0.3:
                risk_level = ContentRisk.HIGH
            elif max_score >= 0.1:
                risk_level = ContentRisk.MEDIUM
            else:
                risk_level = ContentRisk.LOW
            
            confidence = min(0.9, 0.5 + max_score)
        
        return ModerationResult(
            category=category,
            risk_level=risk_level,
            confidence=confidence,
            flags=flags,
            details={
                "text_length": len(text),
                "risk_scores": {k.value: v for k, v in risk_scores.items()},
                "medical_claims": len(medical_matches),
                "brand_safety_issues": len(brand_unsafe_matches),
                "total_flags": len(flags)
            },
            timestamp=datetime.now().isoformat()
        )


class ImageModerator:
    """Free image content moderation using basic analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def moderate_image(self, image_path: str) -> ModerationResult:
        """Moderate image content using free analysis methods"""
        try:
            # Basic image analysis
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Basic statistical analysis
                stat = ImageStat.Stat(img)
                
                # Get image properties
                width, height = img.size
                aspect_ratio = width / height
                
                # Simple heuristics for content detection
                flags = []
                risk_level = ContentRisk.LOW
                category = ModerationCategory.SAFE
                
                # Check for suspicious aspect ratios (potential inappropriate content)
                if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                    flags.append("unusual_aspect_ratio")
                
                # Check color distribution (very basic)
                avg_colors = stat.mean
                if len(avg_colors) >= 3:
                    r, g, b = avg_colors[:3]
                    
                    # Very red images might be concerning
                    if r > g + 50 and r > b + 50:
                        flags.append("high_red_content")
                        risk_level = ContentRisk.MEDIUM
                    
                    # Very dark images
                    if sum(avg_colors[:3]) / 3 < 50:
                        flags.append("very_dark_image")
                
                # Check image size (unusually small might be suspicious)
                if width < 100 or height < 100:
                    flags.append("very_small_image")
                
                # File size heuristics
                file_size = os.path.getsize(image_path)
                if file_size > 10 * 1024 * 1024:  # > 10MB
                    flags.append("large_file_size")
                elif file_size < 1024:  # < 1KB
                    flags.append("tiny_file_size")
                    risk_level = ContentRisk.MEDIUM
                
                confidence = 0.6 if flags else 0.8  # Lower confidence for basic analysis
                
                return ModerationResult(
                    category=category,
                    risk_level=risk_level,
                    confidence=confidence,
                    flags=flags,
                    details={
                        "image_size": f"{width}x{height}",
                        "aspect_ratio": aspect_ratio,
                        "file_size_bytes": file_size,
                        "avg_colors": avg_colors,
                        "color_variance": stat.var if hasattr(stat, 'var') else None,
                        "analysis_method": "basic_statistical"
                    },
                    timestamp=datetime.now().isoformat()
                )
        
        except Exception as e:
            self.logger.error(f"Error analyzing image {image_path}: {e}")
            return ModerationResult(
                ModerationCategory.INAPPROPRIATE, ContentRisk.HIGH, 0.1, 
                ["analysis_error"], {"error": str(e)}, datetime.now().isoformat()
            )


class BrandSafetyValidator:
    """Brand safety validation for creative content"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Brand safety categories
        self.unsafe_contexts = {
            "controversial_topics": [
                "politics", "political", "election", "voting", "government",
                "religion", "religious", "church", "mosque", "temple",
                "abortion", "immigration", "climate change"
            ],
            "negative_news": [
                "disaster", "tragedy", "accident", "crisis", "emergency",
                "pandemic", "war", "conflict", "terrorism", "crime"
            ],
            "adult_adjacent": [
                "dating", "romance", "relationship", "mature", "suggestive",
                "intimate", "seductive", "provocative"
            ],
            "financial_risk": [
                "investment", "cryptocurrency", "trading", "forex", "loan",
                "debt", "bankruptcy", "financial advice", "get rich quick"
            ]
        }
        
        # Industry-specific brand safety rules
        self.industry_rules = {
            "healthcare": {
                "avoid": ["miracle cure", "instant results", "guaranteed"],
                "require": ["consult doctor", "FDA", "clinical"]
            },
            "finance": {
                "avoid": ["guaranteed returns", "risk-free", "get rich"],
                "require": ["terms apply", "regulated", "licensed"]
            },
            "food": {
                "avoid": ["cure disease", "medical benefits", "lose weight fast"],
                "require": ["balanced diet", "nutritional"]
            }
        }
    
    def validate_brand_safety(
        self, 
        content: str, 
        industry: str = "general",
        brand_guidelines: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Validate content for brand safety"""
        
        content_lower = content.lower()
        violations = []
        warnings = []
        recommendations = []
        
        # Check unsafe contexts
        for context, keywords in self.unsafe_contexts.items():
            matches = [kw for kw in keywords if kw in content_lower]
            if matches:
                violations.append({
                    "type": "unsafe_context",
                    "context": context,
                    "matches": matches,
                    "severity": "medium"
                })
        
        # Check industry-specific rules
        if industry in self.industry_rules:
            rules = self.industry_rules[industry]
            
            # Check avoided terms
            for avoid_term in rules.get("avoid", []):
                if avoid_term in content_lower:
                    violations.append({
                        "type": "industry_violation",
                        "industry": industry,
                        "term": avoid_term,
                        "severity": "high"
                    })
            
            # Check required terms
            for required_term in rules.get("require", []):
                if required_term not in content_lower:
                    warnings.append({
                        "type": "missing_required",
                        "industry": industry,
                        "missing_term": required_term,
                        "recommendation": f"Consider adding '{required_term}' for compliance"
                    })
        
        # Check brand guidelines compliance
        if brand_guidelines:
            if "prohibited_words" in brand_guidelines:
                for word in brand_guidelines["prohibited_words"]:
                    if word.lower() in content_lower:
                        violations.append({
                            "type": "brand_guideline",
                            "prohibited_word": word,
                            "severity": "high"
                        })
            
            if "required_disclaimers" in brand_guidelines:
                for disclaimer in brand_guidelines["required_disclaimers"]:
                    if disclaimer.lower() not in content_lower:
                        warnings.append({
                            "type": "missing_disclaimer",
                            "disclaimer": disclaimer,
                            "recommendation": f"Add disclaimer: '{disclaimer}'"
                        })
        
        # Generate recommendations
        if violations:
            recommendations.append("Review content for brand safety violations")
        if warnings:
            recommendations.append("Consider adding required disclaimers and compliance terms")
        if not violations and not warnings:
            recommendations.append("Content appears brand-safe")
        
        # Calculate safety score
        violation_count = len(violations)
        warning_count = len(warnings)
        safety_score = max(0, 100 - (violation_count * 20) - (warning_count * 5))
        
        # Determine overall status
        if violation_count > 0:
            status = "violations_found"
        elif warning_count > 0:
            status = "warnings_found"
        else:
            status = "safe"
        
        return {
            "status": status,
            "safety_score": safety_score,
            "violations": violations,
            "warnings": warnings,
            "recommendations": recommendations,
            "industry": industry,
            "analysis_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_violations": violation_count,
                "total_warnings": warning_count,
                "critical_issues": len([v for v in violations if v.get("severity") == "high"])
            }
        }


class ComprehensiveContentModerator:
    """Main content moderation system combining all moderation types"""
    
    def __init__(self):
        self.text_moderator = TextModerator()
        self.image_moderator = ImageModerator()
        self.brand_safety = BrandSafetyValidator()
        self.logger = logging.getLogger(__name__)
    
    def moderate_campaign_content(
        self,
        campaign_brief: Dict[str, Any],
        generated_images: List[str] = None,
        industry: str = "general"
    ) -> Dict[str, Any]:
        """Comprehensive moderation of entire campaign content"""
        
        results = {
            "campaign_id": campaign_brief.get("campaign_brief", {}).get("campaign_id", "unknown"),
            "moderation_timestamp": datetime.now().isoformat(),
            "overall_status": "safe",
            "overall_risk": ContentRisk.LOW.value,
            "text_moderation": {},
            "image_moderation": [],
            "brand_safety": {},
            "summary": {
                "total_flags": 0,
                "critical_issues": 0,
                "recommendations": []
            }
        }
        
        try:
            brief = campaign_brief.get("campaign_brief", {})
            
            # Moderate text content
            text_content = []
            
            # Campaign message
            if "campaign_message" in brief:
                text_content.append(("campaign_message", brief["campaign_message"]))
            
            # Product descriptions
            for i, product in enumerate(brief.get("products", [])):
                if "description" in product:
                    text_content.append((f"product_{i}_description", product["description"]))
                if "name" in product:
                    text_content.append((f"product_{i}_name", product["name"]))
            
            # Moderate all text content
            text_results = {}
            max_text_risk = ContentRisk.LOW
            
            for content_type, content in text_content:
                if content:
                    mod_result = self.text_moderator.moderate_text(content, content_type)
                    text_results[content_type] = {
                        "category": mod_result.category.value,
                        "risk_level": mod_result.risk_level.value,
                        "confidence": mod_result.confidence,
                        "flags": mod_result.flags,
                        "details": mod_result.details
                    }
                    
                    # Track highest risk
                    if mod_result.risk_level.value != ContentRisk.LOW.value:
                        if mod_result.risk_level == ContentRisk.CRITICAL:
                            max_text_risk = ContentRisk.CRITICAL
                        elif mod_result.risk_level == ContentRisk.HIGH and max_text_risk != ContentRisk.CRITICAL:
                            max_text_risk = ContentRisk.HIGH
                        elif mod_result.risk_level == ContentRisk.MEDIUM and max_text_risk == ContentRisk.LOW:
                            max_text_risk = ContentRisk.MEDIUM
            
            results["text_moderation"] = text_results
            
            # Moderate generated images
            image_results = []
            max_image_risk = ContentRisk.LOW
            
            if generated_images:
                for img_path in generated_images:
                    if os.path.exists(img_path):
                        mod_result = self.image_moderator.moderate_image(img_path)
                        image_results.append({
                            "image_path": img_path,
                            "category": mod_result.category.value,
                            "risk_level": mod_result.risk_level.value,
                            "confidence": mod_result.confidence,
                            "flags": mod_result.flags,
                            "details": mod_result.details
                        })
                        
                        # Track highest risk
                        if mod_result.risk_level.value != ContentRisk.LOW.value:
                            if mod_result.risk_level == ContentRisk.CRITICAL:
                                max_image_risk = ContentRisk.CRITICAL
                            elif mod_result.risk_level == ContentRisk.HIGH and max_image_risk != ContentRisk.CRITICAL:
                                max_image_risk = ContentRisk.HIGH
                            elif mod_result.risk_level == ContentRisk.MEDIUM and max_image_risk == ContentRisk.LOW:
                                max_image_risk = ContentRisk.MEDIUM
            
            results["image_moderation"] = image_results
            
            # Brand safety validation
            all_text = " ".join([content for _, content in text_content])
            brand_guidelines = brief.get("brand_guidelines", {})
            
            brand_safety_result = self.brand_safety.validate_brand_safety(
                all_text, industry, brand_guidelines
            )
            results["brand_safety"] = brand_safety_result
            
            # Determine overall status and risk
            overall_risk = max(max_text_risk, max_image_risk)
            
            if brand_safety_result["summary"]["critical_issues"] > 0:
                overall_risk = ContentRisk.CRITICAL
            elif brand_safety_result["summary"]["total_violations"] > 0:
                overall_risk = max(overall_risk, ContentRisk.HIGH)
            
            results["overall_risk"] = overall_risk.value
            
            if overall_risk == ContentRisk.CRITICAL:
                results["overall_status"] = "blocked"
            elif overall_risk == ContentRisk.HIGH:
                results["overall_status"] = "review_required"
            elif overall_risk == ContentRisk.MEDIUM:
                results["overall_status"] = "warnings"
            else:
                results["overall_status"] = "safe"
            
            # Generate summary
            total_flags = sum(len(result.get("flags", [])) for result in text_results.values())
            total_flags += sum(len(result.get("flags", [])) for result in image_results)
            
            critical_issues = brand_safety_result["summary"]["critical_issues"]
            critical_issues += len([r for r in text_results.values() if r.get("risk_level") == "critical"])
            critical_issues += len([r for r in image_results if r.get("risk_level") == "critical"])
            
            recommendations = brand_safety_result["recommendations"].copy()
            if critical_issues > 0:
                recommendations.insert(0, "CRITICAL: Content contains high-risk elements that must be addressed")
            if total_flags > 0:
                recommendations.append(f"Review and address {total_flags} flagged elements")
            
            results["summary"] = {
                "total_flags": total_flags,
                "critical_issues": critical_issues,
                "recommendations": recommendations,
                "moderation_score": max(0, 100 - (critical_issues * 25) - (total_flags * 2))
            }
            
        except Exception as e:
            self.logger.error(f"Error in content moderation: {e}")
            results["overall_status"] = "error"
            results["error"] = str(e)
        
        return results
    
    def get_moderation_summary(self, results: Dict[str, Any]) -> str:
        """Generate human-readable moderation summary"""
        status = results["overall_status"]
        risk = results["overall_risk"]
        summary = results["summary"]
        
        if status == "blocked":
            return f"🚨 BLOCKED - Critical content violations detected ({summary['critical_issues']} critical issues)"
        elif status == "review_required":
            return f"⚠️ REVIEW REQUIRED - High-risk content needs approval ({summary['total_flags']} flags)"
        elif status == "warnings":
            return f"⚡ WARNINGS - Minor issues detected ({summary['total_flags']} flags)"
        elif status == "safe":
            return f"✅ SAFE - Content approved for publication (Score: {summary.get('moderation_score', 0)})"
        else:
            return f"❌ ERROR - Moderation analysis failed"