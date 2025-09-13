"""
Text Generation Module

Handles AI-powered text generation and localization for campaign messages,
headlines, and copy across different regions and languages.
"""

import os
import logging
import openai
from typing import Dict, List, Any, Optional, Tuple
import json
import time

logger = logging.getLogger(__name__)


class TextGenerator:
    """Manages AI text generation and localization for campaigns."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the text generator with configuration."""
        self.config = config
        self.text_config = config.get("text_generation", {})
        
        # Initialize Adobe Sensei and fallback API clients
        self._init_api_clients()
        
        # Localization templates and rules
        self.localization_rules = self._load_localization_rules()
        
        logger.info("TextGenerator initialized")
    
    def _init_api_clients(self):
        """Initialize OpenAI API client for text generation."""
        # Load environment variables from .env file
        from pathlib import Path
        import os
        env_path = Path(__file__).parent.parent.parent / "config" / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.strip() and not line.startswith('#') and '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # OpenAI API configuration for text generation
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI API configured for text generation")
        else:
            logger.warning("OpenAI API not configured - missing API key")
            self.openai_client = None
    
    def _load_localization_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load localization rules and cultural guidelines."""
        return {
            "en": {
                "name": "English",
                "tone_preferences": "Direct, confident, action-oriented",
                "cultural_notes": "Values efficiency and results",
                "max_headline_length": 60,
                "max_body_length": 150,
                "call_to_action_style": "Imperative verbs (Try, Get, Discover)"
            },
            "es": {
                "name": "Spanish",
                "tone_preferences": "Warm, family-oriented, passionate",
                "cultural_notes": "Family and community focus",
                "max_headline_length": 70,
                "max_body_length": 180,
                "call_to_action_style": "Inviting and inclusive"
            },
            "fr": {
                "name": "French", 
                "tone_preferences": "Sophisticated, elegant, quality-focused",
                "cultural_notes": "Appreciation for craftsmanship and tradition",
                "max_headline_length": 75,
                "max_body_length": 170,
                "call_to_action_style": "Subtle sophistication"
            },
            "de": {
                "name": "German",
                "tone_preferences": "Precise, reliable, quality-focused",
                "cultural_notes": "Values engineering and precision",
                "max_headline_length": 65,
                "max_body_length": 160,
                "call_to_action_style": "Clear and factual"
            },
            "it": {
                "name": "Italian",
                "tone_preferences": "Passionate, aesthetic, lifestyle-focused", 
                "cultural_notes": "Beauty and style appreciation",
                "max_headline_length": 70,
                "max_body_length": 175,
                "call_to_action_style": "Emotional connection"
            }
        }
    
    def generate_localized_copy(self,
                              product: Dict[str, Any],
                              campaign_brief: Dict[str, Any],
                              region: Dict[str, Any],
                              format_config: Dict[str, Any]) -> Dict[str, str]:
        """Generate localized copy for a specific product, region, and format."""
        
        logger.info(f"Generating localized copy for {product['name']} in {region['region']}")
        
        # Determine target language
        primary_language = region.get("languages", ["en"])[0]
        
        # Generate copy for each required element
        copy_elements = {}
        
        # Main headline
        copy_elements["headline"] = self._generate_headline(
            product, campaign_brief, region, primary_language
        )
        
        # Secondary text/body
        copy_elements["body_text"] = self._generate_body_text(
            product, campaign_brief, region, primary_language
        )
        
        # Call to action
        copy_elements["cta"] = self._generate_cta(
            campaign_brief, region, primary_language
        )
        
        # Benefit callouts
        copy_elements["benefit_callout"] = self._generate_benefit_callout(
            product, region, primary_language
        )
        
        # Legal disclaimer (if required)
        if campaign_brief.get("compliance_requirements", {}).get("legal_disclaimers"):
            copy_elements["disclaimer"] = self._localize_disclaimer(
                campaign_brief["compliance_requirements"]["legal_disclaimers"][0],
                primary_language
            )
        
        logger.info(f"Generated copy elements: {list(copy_elements.keys())}")
        return copy_elements
    
    def _generate_headline(self,
                         product: Dict[str, Any],
                         campaign_brief: Dict[str, Any],
                         region: Dict[str, Any], 
                         language: str) -> str:
        """Generate a compelling headline for the campaign."""
        
        localization_rules = self.localization_rules.get(language, self.localization_rules["en"])
        max_length = localization_rules["max_headline_length"]
        tone = localization_rules["tone_preferences"]
        
        prompt = f"""Create a compelling marketing headline for {product['name']} targeting {region['region']}.

Product Information:
- Name: {product['name']}
- Category: {product['category']}
- Key Benefits: {', '.join(product.get('key_benefits', []))}
- Price Point: {product.get('target_price', 'Premium')}

Campaign Context:
- Primary Message: {campaign_brief.get('campaign_message', {}).get('primary_headline', '')}
- Target Audience: {campaign_brief.get('target_audience', {}).get('primary', {}).get('demographics', '')}
- Brand Voice: {campaign_brief.get('campaign_message', {}).get('brand_voice', '')}
- Regional Context: {region.get('cultural_notes', '')}

Language and Localization:
- Target Language: {language} ({localization_rules['name']})
- Cultural Tone: {tone}
- Cultural Notes: {localization_rules['cultural_notes']}
- Maximum Length: {max_length} characters

Requirements:
1. Create exactly ONE headline that is compelling and memorable
2. Incorporate the key product benefit naturally
3. Match the cultural tone and preferences for {language}
4. Stay within {max_length} characters
5. Avoid direct translation - create culturally appropriate copy
6. Make it actionable and engaging

Return only the headline text, no quotation marks or additional text."""
        
        # Use OpenAI as primary service
        if self.openai_client:
            headline = self._generate_with_openai(prompt, max_length)
            if headline:
                return headline
            logger.warning("OpenAI text generation failed")
        
        # Final fallback to campaign brief
        logger.warning("All text generation services failed, using fallback headline")
        return campaign_brief.get("campaign_message", {}).get("primary_headline", "Discover More")
    
    def _generate_with_adobe_sensei(self, prompt: str, language: str, max_length: int) -> Optional[str]:
        """Generate text using Adobe Sensei API."""
        
        try:
            logger.info(f"Generating text with Adobe Sensei for language: {language}")
            
            headers = {
                'Authorization': f'Bearer {self.adobe_access_token}',
                'x-api-key': self.adobe_client_id,
                'Content-Type': 'application/json'
            }
            
            payload = {
                "prompt": prompt,
                "language": language,
                "maxLength": max_length,
                "temperature": self.text_config.get("temperature", 0.7),
                "features": {
                    "brandVoice": True,
                    "culturalAdaptation": True,
                    "complianceCheck": True
                },
                "outputType": "marketing_headline"
            }
            
            sensei_endpoint = f"{self.adobe_sensei_endpoint}/v1/text/generate"
            
            response = requests.post(sensei_endpoint, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("content"):
                headline = result["content"].strip()
                
                # Validate length
                if len(headline) > max_length:
                    headline = headline[:max_length-3] + "..."
                
                logger.info(f"Adobe Sensei generated headline ({language}): {headline}")
                return headline
                
        except Exception as e:
            logger.warning(f"Adobe Sensei text generation failed: {e}")
        
        return None
    
    def _generate_with_openai(self, prompt: str, max_length: int) -> Optional[str]:
        """Generate text using OpenAI as fallback."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.text_config.get("services", {}).get("openai", {}).get("model", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=self.text_config.get("temperature", 0.7)
            )
            
            headline = response.choices[0].message.content.strip()
            
            # Validate length
            if len(headline) > max_length:
                headline = headline[:max_length-3] + "..."
            
            logger.info(f"OpenAI generated headline: {headline}")
            return headline
            
        except Exception as e:
            logger.error(f"OpenAI text generation failed: {e}")
            return None
    
    def _generate_body_text(self,
                          product: Dict[str, Any],
                          campaign_brief: Dict[str, Any],
                          region: Dict[str, Any],
                          language: str) -> str:
        """Generate body text/secondary copy."""
        
        localization_rules = self.localization_rules.get(language, self.localization_rules["en"])
        max_length = localization_rules["max_body_length"]
        
        prompt = f"""Create engaging body text for a social media ad promoting {product['name']}.

Context:
- Product: {product['name']} ({product['category']})
- Key Benefits: {', '.join(product.get('key_benefits', []))}
- Target Region: {region['region']}
- Cultural Context: {region.get('cultural_notes', '')}
- Target Language: {language} ({localization_rules['name']})

Copy Requirements:
- Maximum {max_length} characters
- Tone: {localization_rules['tone_preferences']}
- Cultural sensitivity: {localization_rules['cultural_notes']}
- Focus on emotional connection and product benefits
- Suitable for social media format

Create compelling body text that complements the headline and drives engagement.
Return only the body text, no quotation marks."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.text_config.get("model", "gpt-4-turbo-preview"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=self.text_config.get("temperature", 0.7)
            )
            
            body_text = response.choices[0].message.content.strip()
            
            # Validate length
            if len(body_text) > max_length:
                body_text = body_text[:max_length-3] + "..."
            
            logger.info(f"Generated body text ({language}): {body_text[:50]}...")
            return body_text
            
        except Exception as e:
            logger.error(f"Failed to generate body text: {e}")
            return campaign_brief.get("campaign_message", {}).get("secondary_headline", "")
    
    def _generate_cta(self,
                     campaign_brief: Dict[str, Any],
                     region: Dict[str, Any],
                     language: str) -> str:
        """Generate call-to-action text."""
        
        localization_rules = self.localization_rules.get(language, self.localization_rules["en"])
        cta_style = localization_rules["call_to_action_style"]
        
        base_cta = campaign_brief.get("campaign_message", {}).get("call_to_action", "Try Now")
        
        # Language-specific CTA translations and cultural adaptations
        cta_translations = {
            "en": {"Try Now": "Try Now", "Learn More": "Learn More", "Shop Now": "Shop Now"},
            "es": {"Try Now": "Prueba Ahora", "Learn More": "Descubre Más", "Shop Now": "Compra Ahora"},
            "fr": {"Try Now": "Essayez Maintenant", "Learn More": "En Savoir Plus", "Shop Now": "Acheter"},
            "de": {"Try Now": "Jetzt Probieren", "Learn More": "Mehr Erfahren", "Shop Now": "Jetzt Kaufen"},
            "it": {"Try Now": "Prova Ora", "Learn More": "Scopri Di Più", "Shop Now": "Acquista Ora"}
        }
        
        # Get appropriate translation
        lang_ctas = cta_translations.get(language, cta_translations["en"])
        localized_cta = lang_ctas.get(base_cta, base_cta)
        
        logger.info(f"Generated CTA ({language}): {localized_cta}")
        return localized_cta
    
    def _generate_benefit_callout(self,
                                product: Dict[str, Any],
                                region: Dict[str, Any],
                                language: str) -> str:
        """Generate a short benefit callout."""
        
        benefits = product.get("key_benefits", [])
        if not benefits:
            return ""
        
        # Select most relevant benefit for the region
        primary_benefit = benefits[0]  # Simplified selection
        
        # Create localized benefit callout
        benefit_templates = {
            "en": "✓ {benefit}",
            "es": "✓ {benefit}",
            "fr": "✓ {benefit}",
            "de": "✓ {benefit}",
            "it": "✓ {benefit}"
        }
        
        template = benefit_templates.get(language, benefit_templates["en"])
        callout = template.format(benefit=primary_benefit)
        
        logger.info(f"Generated benefit callout ({language}): {callout}")
        return callout
    
    def _localize_disclaimer(self, disclaimer: str, language: str) -> str:
        """Localize legal disclaimers."""
        
        # Basic disclaimer translations
        disclaimer_translations = {
            "en": disclaimer,
            "es": "*Se aplican términos y condiciones",
            "fr": "*Conditions générales applicables", 
            "de": "*Es gelten die Allgemeinen Geschäftsbedingungen",
            "it": "*Si applicano termini e condizioni"
        }
        
        # For legal text, we'd normally use professional translation services
        # This is a simplified example
        localized = disclaimer_translations.get(language, disclaimer)
        
        logger.info(f"Localized disclaimer ({language}): {localized}")
        return localized
    
    def optimize_text_for_format(self,
                               copy_elements: Dict[str, str],
                               format_config: Dict[str, Any]) -> Dict[str, str]:
        """Optimize text elements for specific format constraints."""
        
        format_name = format_config.get("name", "").lower()
        
        # Format-specific optimizations
        if "story" in format_name:
            # Vertical format - shorter headlines work better
            if len(copy_elements.get("headline", "")) > 40:
                copy_elements["headline"] = copy_elements["headline"][:37] + "..."
        
        elif "landscape" in format_name:
            # Horizontal format - can accommodate longer text
            pass
        
        elif "square" in format_name:
            # Square format - balanced text distribution
            pass
        
        logger.info(f"Optimized text for {format_name} format")
        return copy_elements
    
    def validate_text_compliance(self,
                               copy_elements: Dict[str, str],
                               compliance_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate text against compliance requirements."""
        
        validation_result = {
            "passed": True,
            "issues": [],
            "flagged_content": []
        }
        
        # Check for prohibited words
        prohibited_words = compliance_requirements.get("prohibited_words", [])
        
        for element_name, text in copy_elements.items():
            for word in prohibited_words:
                if word.lower() in text.lower():
                    validation_result["passed"] = False
                    validation_result["issues"].append(f"Prohibited word '{word}' found in {element_name}")
                    validation_result["flagged_content"].append({
                        "element": element_name,
                        "word": word,
                        "text": text
                    })
        
        # Check for required disclaimers
        required_disclaimers = compliance_requirements.get("legal_disclaimers", [])
        if required_disclaimers and "disclaimer" not in copy_elements:
            validation_result["passed"] = False
            validation_result["issues"].append("Required disclaimer missing")
        
        logger.info(f"Text compliance validation: {'PASSED' if validation_result['passed'] else 'FAILED'}")
        return validation_result