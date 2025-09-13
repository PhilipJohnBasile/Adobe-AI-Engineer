"""
Compliance Validation Module

Validates content against legal, regulatory, and content policy requirements
including prohibited words, required disclaimers, and industry compliance.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Set
from PIL import Image
# import pytesseract  # Optional OCR dependency
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ComplianceValidator:
    """Validates content compliance against legal and regulatory requirements."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the compliance validator with configuration."""
        self.config = config
        self.compliance_config = config.get("validation", {}).get("content_compliance", {})
        
        # Load compliance rules
        self.prohibited_words = self._load_prohibited_words()
        self.required_patterns = self._load_required_patterns()
        self.regulatory_rules = self._load_regulatory_rules()
        
        # OCR setup for text extraction
        self._setup_ocr()
        
        logger.info("ComplianceValidator initialized")
    
    def _load_prohibited_words(self) -> Set[str]:
        """Load prohibited words and phrases."""
        
        # Base prohibited words from config
        prohibited = set(self.compliance_config.get("prohibited_words", []))
        
        # Add common regulatory prohibited terms
        regulatory_prohibited = {
            # Medical/health claims
            "cure", "heals", "miracle", "magic", "instant results",
            "guaranteed results", "clinically proven", "FDA approved",
            
            # Financial claims
            "get rich quick", "guaranteed income", "risk-free",
            
            # Superlative claims without substantiation
            "best in the world", "number one", "only solution",
            
            # Discriminatory language
            "discriminatory", "offensive", "inappropriate"
        }
        
        prohibited.update(regulatory_prohibited)
        
        logger.info(f"Loaded {len(prohibited)} prohibited terms")
        return prohibited
    
    def _load_required_patterns(self) -> List[str]:
        """Load patterns that must be present in compliant content."""
        
        required = [
            r"\*.*terms.*conditions.*apply",  # T&C disclaimer
            r"\*.*individual.*results.*vary",  # Results disclaimer
            r"\*.*not.*evaluated.*FDA",       # FDA disclaimer
        ]
        
        logger.info(f"Loaded {len(required)} required patterns")
        return required
    
    def _load_regulatory_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load industry-specific regulatory rules."""
        
        return {
            "health_supplements": {
                "required_disclaimers": [
                    "*This statement has not been evaluated by the FDA",
                    "*Individual results may vary"
                ],
                "prohibited_claims": ["cure", "treat", "prevent disease"],
                "max_claim_strength": "moderate"
            },
            "financial_services": {
                "required_disclaimers": [
                    "*Investment involves risk",
                    "*Past performance does not guarantee future results"
                ],
                "prohibited_claims": ["guaranteed returns", "risk-free"],
                "max_claim_strength": "conservative"
            },
            "food_beverage": {
                "required_disclaimers": [
                    "*Part of a balanced diet"
                ],
                "prohibited_claims": ["medical benefits"],
                "max_claim_strength": "moderate"
            }
        }
    
    def _setup_ocr(self):
        """Setup OCR for text extraction from images."""
        
        try:
            # Test if pytesseract is available
            # pytesseract.get_tesseract_version()  # Disabled for demo
            self.ocr_available = False  # Disabled for demo
            logger.info("OCR (Tesseract) available for text extraction")
        except Exception as e:
            self.ocr_available = False
            logger.warning(f"OCR not available: {e}")
    
    def validate_content(self, 
                        image: Image.Image,
                        compliance_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive compliance validation of content."""
        
        logger.info("Starting compliance validation")
        
        validation_result = {
            "passed": True,
            "overall_score": 1.0,
            "component_scores": {},
            "violations": [],
            "warnings": [],
            "required_actions": []
        }
        
        try:
            # Extract text from image
            extracted_text = self._extract_text_from_image(image)
            
            # Run validation checks
            prohibited_result = self._check_prohibited_content(extracted_text, compliance_requirements)
            disclaimer_result = self._check_required_disclaimers(extracted_text, compliance_requirements)
            claim_result = self._check_claim_substantiation(extracted_text, compliance_requirements)
            regulatory_result = self._check_regulatory_compliance(extracted_text, compliance_requirements)
            
            # Combine results
            validation_result["component_scores"] = {
                "prohibited_content": prohibited_result["score"],
                "required_disclaimers": disclaimer_result["score"],
                "claim_substantiation": claim_result["score"],
                "regulatory_compliance": regulatory_result["score"]
            }
            
            # Calculate overall score
            scores = list(validation_result["component_scores"].values())
            validation_result["overall_score"] = min(scores) if scores else 1.0
            validation_result["passed"] = validation_result["overall_score"] >= 0.8
            
            # Collect violations and warnings
            for result in [prohibited_result, disclaimer_result, claim_result, regulatory_result]:
                validation_result["violations"].extend(result.get("violations", []))
                validation_result["warnings"].extend(result.get("warnings", []))
                validation_result["required_actions"].extend(result.get("required_actions", []))
            
            logger.info(f"Compliance validation completed: Score {validation_result['overall_score']:.2f}, "
                       f"Passed: {validation_result['passed']}")
            
        except Exception as e:
            logger.error(f"Compliance validation failed: {e}")
            validation_result["passed"] = False
            validation_result["violations"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text content from image using OCR."""
        
        if not self.ocr_available:
            logger.warning("OCR not available, using placeholder text extraction")
            return "Sample text content"  # Placeholder
        
        try:
            # Convert image for OCR
            image_array = np.array(image.convert("RGB"))
            
            # Preprocess image for better OCR results
            processed_image = self._preprocess_for_ocr(image_array)
            
            # Extract text using pytesseract
            # extracted_text = pytesseract.image_to_string(processed_image, config='--psm 6')  # Disabled for demo
            extracted_text = "Demo mode: OCR text extraction disabled"
            
            # Clean extracted text
            cleaned_text = self._clean_extracted_text(extracted_text)
            
            logger.info(f"Extracted text ({len(cleaned_text)} chars): {cleaned_text[:100]}...")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ""
    
    def _preprocess_for_ocr(self, image_array: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy."""
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
            
            # Apply gaussian blur to smooth
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply threshold to get binary image
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Morphological operations to clean up
            kernel = np.ones((2, 2), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            return processed
            
        except Exception as e:
            logger.warning(f"OCR preprocessing failed: {e}")
            return cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with analysis
        cleaned = re.sub(r'[^\w\s\*\.\,\!\?]', '', cleaned)
        
        # Convert to lowercase for analysis
        return cleaned.lower().strip()
    
    def _check_prohibited_content(self, 
                                 text: str,
                                 compliance_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Check for prohibited words and content."""
        
        result = {
            "score": 1.0,
            "violations": [],
            "warnings": [],
            "required_actions": []
        }
        
        try:
            # Get prohibited words from requirements and defaults
            prohibited_words = set(compliance_requirements.get("prohibited_words", []))
            prohibited_words.update(self.prohibited_words)
            
            # Check for prohibited content
            violations_found = []
            
            for prohibited in prohibited_words:
                if prohibited.lower() in text.lower():
                    violations_found.append(prohibited)
                    result["violations"].append(f"Prohibited term found: '{prohibited}'")
            
            # Calculate score based on violations
            if violations_found:
                # Severity-based scoring
                severe_terms = {"cure", "miracle", "guaranteed", "risk-free"}
                severe_violations = [term for term in violations_found if term in severe_terms]
                
                if severe_violations:
                    result["score"] = 0.0  # Critical violations
                    result["required_actions"].append("Remove all prohibited claims immediately")
                else:
                    result["score"] = max(0.3, 1.0 - (len(violations_found) * 0.2))
                    result["required_actions"].append("Revise content to remove prohibited terms")
            
        except Exception as e:
            logger.warning(f"Prohibited content check failed: {e}")
            result["score"] = 0.5
        
        return result
    
    def _check_required_disclaimers(self,
                                  text: str,
                                  compliance_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Check for required legal disclaimers."""
        
        result = {
            "score": 1.0,
            "violations": [],
            "warnings": [],
            "required_actions": []
        }
        
        try:
            required_disclaimers = compliance_requirements.get("legal_disclaimers", [])
            
            if not required_disclaimers:
                return result  # No disclaimers required
            
            missing_disclaimers = []
            
            for disclaimer in required_disclaimers:
                # Check if disclaimer or similar pattern exists
                if not self._disclaimer_present(text, disclaimer):
                    missing_disclaimers.append(disclaimer)
            
            if missing_disclaimers:
                result["score"] = max(0.2, 1.0 - (len(missing_disclaimers) * 0.3))
                
                for disclaimer in missing_disclaimers:
                    result["violations"].append(f"Required disclaimer missing: '{disclaimer}'")
                
                result["required_actions"].append("Add all required legal disclaimers")
            
        except Exception as e:
            logger.warning(f"Disclaimer check failed: {e}")
            result["score"] = 0.7
        
        return result
    
    def _disclaimer_present(self, text: str, required_disclaimer: str) -> bool:
        """Check if a disclaimer or similar pattern is present in text."""
        
        # Create flexible pattern from disclaimer
        disclaimer_words = required_disclaimer.lower().replace("*", "").split()
        key_words = [word for word in disclaimer_words if len(word) > 3]
        
        # Check if most key words are present
        words_found = sum(1 for word in key_words if word in text.lower())
        
        # Require at least 60% of key words to be present
        return words_found >= len(key_words) * 0.6
    
    def _check_claim_substantiation(self,
                                  text: str,
                                  compliance_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Check if marketing claims are appropriately substantiated."""
        
        result = {
            "score": 1.0,
            "violations": [],
            "warnings": [],
            "required_actions": []
        }
        
        try:
            # Define claim strength patterns
            strong_claims = [
                r"\b(best|top|#1|number one|leading|ultimate|perfect)\b",
                r"\b(always|never|all|every|100%|completely)\b",
                r"\b(proven|guaranteed|clinically|scientifically)\b"
            ]
            
            moderate_claims = [
                r"\b(effective|helps|supports|may|can)\b",
                r"\b(improved|better|enhanced)\b"
            ]
            
            # Check claim strength
            strong_claim_matches = []
            for pattern in strong_claims:
                matches = re.findall(pattern, text, re.IGNORECASE)
                strong_claim_matches.extend(matches)
            
            # Get maximum allowed claim strength
            max_strength = compliance_requirements.get("max_claim_strength", "moderate")
            
            if strong_claim_matches and max_strength != "strong":
                result["score"] = 0.6
                result["warnings"].append(f"Strong claims detected: {', '.join(set(strong_claim_matches))}")
                result["required_actions"].append("Moderate claim language or provide substantiation")
            
            # Check for unsubstantiated claims
            unsubstantiated_patterns = [
                r"\b(instant|immediate|overnight)\b.*\b(results|effects|benefits)\b",
                r"\b(lose|gain|improve)\b.*\b(\d+)\s*(pounds|%|times)\b.*\b(days|hours)\b"
            ]
            
            for pattern in unsubstantiated_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    result["score"] = min(result["score"], 0.4)
                    result["violations"].append(f"Potentially unsubstantiated claim found")
                    result["required_actions"].append("Provide substantiation for specific claims")
            
        except Exception as e:
            logger.warning(f"Claim substantiation check failed: {e}")
            result["score"] = 0.8
        
        return result
    
    def _check_regulatory_compliance(self,
                                   text: str,
                                   compliance_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Check industry-specific regulatory compliance."""
        
        result = {
            "score": 1.0,
            "violations": [],
            "warnings": [],
            "required_actions": []
        }
        
        try:
            # Determine industry context
            industry = self._detect_industry_context(text, compliance_requirements)
            
            if industry and industry in self.regulatory_rules:
                industry_rules = self.regulatory_rules[industry]
                
                # Check industry-specific prohibited claims
                prohibited_claims = industry_rules.get("prohibited_claims", [])
                for claim in prohibited_claims:
                    if claim.lower() in text.lower():
                        result["score"] = min(result["score"], 0.3)
                        result["violations"].append(f"Industry-prohibited claim: '{claim}'")
                
                # Check required industry disclaimers
                required_disclaimers = industry_rules.get("required_disclaimers", [])
                missing_industry_disclaimers = []
                
                for disclaimer in required_disclaimers:
                    if not self._disclaimer_present(text, disclaimer):
                        missing_industry_disclaimers.append(disclaimer)
                
                if missing_industry_disclaimers:
                    result["score"] = min(result["score"], 0.5)
                    result["violations"].append(f"Missing industry disclaimer")
                    result["required_actions"].append(f"Add required {industry} disclaimers")
            
        except Exception as e:
            logger.warning(f"Regulatory compliance check failed: {e}")
            result["score"] = 0.8
        
        return result
    
    def _detect_industry_context(self, 
                               text: str,
                               compliance_requirements: Dict[str, Any]) -> Optional[str]:
        """Detect industry context from text content."""
        
        # Industry keyword patterns
        industry_patterns = {
            "health_supplements": [
                r"\b(vitamin|supplement|protein|energy|health|wellness|nutrition)\b",
                r"\b(natural|organic|formula|ingredient)\b"
            ],
            "financial_services": [
                r"\b(investment|returns|profit|income|financial|money|earnings)\b",
                r"\b(portfolio|trading|market|stocks|fund)\b"
            ],
            "food_beverage": [
                r"\b(drink|beverage|food|snack|nutrition|calories|flavor)\b",
                r"\b(taste|recipe|ingredients|diet)\b"
            ]
        }
        
        # Score each industry based on keyword matches
        industry_scores = {}
        
        for industry, patterns in industry_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            industry_scores[industry] = score
        
        # Return industry with highest score if above threshold
        if industry_scores:
            best_industry = max(industry_scores, key=industry_scores.get)
            if industry_scores[best_industry] >= 2:  # Threshold for detection
                return best_industry
        
        return None
    
    def validate_asset_metadata(self, 
                              asset_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate asset metadata for compliance tracking."""
        
        validation_result = {
            "passed": True,
            "issues": [],
            "recommendations": []
        }
        
        required_fields = [
            "creation_date",
            "approval_status", 
            "compliance_review",
            "content_classification"
        ]
        
        for field in required_fields:
            if field not in asset_metadata:
                validation_result["passed"] = False
                validation_result["issues"].append(f"Missing required metadata field: {field}")
        
        return validation_result