"""
Localization Manager - Handles multi-market campaign adaptation and cultural localization.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class LocalizationManager:
    """Manages campaign localization for different markets and cultures."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/localization_rules.json")
        self.localization_data = self._load_localization_data()
        logger.info("Localization manager initialized")
    
    def _load_localization_data(self) -> Dict[str, Any]:
        """Load localization rules and market data."""
        
        # Default localization data
        default_data = {
            "markets": {
                "US": {
                    "language": "en-US",
                    "currency": "USD",
                    "date_format": "MM/DD/YYYY",
                    "cultural_preferences": {
                        "color_associations": {
                            "trust": ["blue", "green"],
                            "energy": ["red", "orange"],
                            "luxury": ["gold", "black", "purple"]
                        },
                        "messaging_style": "direct",
                        "formality_level": "casual",
                        "call_to_action_preferences": ["Shop Now", "Get Yours", "Try Today"]
                    },
                    "regulatory_requirements": {
                        "disclaimer_placement": "bottom",
                        "age_restrictions": ["18+"],
                        "prohibited_claims": ["medical", "therapeutic"]
                    }
                },
                "UK": {
                    "language": "en-GB",
                    "currency": "GBP",
                    "date_format": "DD/MM/YYYY",
                    "cultural_preferences": {
                        "color_associations": {
                            "trust": ["navy", "green"],
                            "energy": ["red", "orange"],
                            "luxury": ["burgundy", "gold", "black"]
                        },
                        "messaging_style": "polite",
                        "formality_level": "semi-formal",
                        "call_to_action_preferences": ["Shop Now", "Discover More", "Learn More"]
                    },
                    "regulatory_requirements": {
                        "disclaimer_placement": "bottom",
                        "age_restrictions": ["18+"],
                        "prohibited_claims": ["medical", "cure", "guaranteed"]
                    }
                },
                "DE": {
                    "language": "de-DE",
                    "currency": "EUR",
                    "date_format": "DD.MM.YYYY",
                    "cultural_preferences": {
                        "color_associations": {
                            "trust": ["blue", "grey"],
                            "energy": ["red", "yellow"],
                            "luxury": ["black", "silver", "dark blue"]
                        },
                        "messaging_style": "formal",
                        "formality_level": "formal",
                        "call_to_action_preferences": ["Jetzt kaufen", "Mehr erfahren", "Entdecken"]
                    },
                    "regulatory_requirements": {
                        "disclaimer_placement": "prominent",
                        "age_restrictions": ["18+"],
                        "prohibited_claims": ["medical", "therapeutic", "guaranteed", "best"]
                    }
                },
                "JP": {
                    "language": "ja-JP",
                    "currency": "JPY",
                    "date_format": "YYYY/MM/DD",
                    "cultural_preferences": {
                        "color_associations": {
                            "trust": ["blue", "white"],
                            "energy": ["red", "orange"],
                            "luxury": ["black", "gold", "deep red"]
                        },
                        "messaging_style": "respectful",
                        "formality_level": "formal",
                        "call_to_action_preferences": ["今すぐ購入", "詳細を見る", "体験する"]
                    },
                    "regulatory_requirements": {
                        "disclaimer_placement": "prominent",
                        "age_restrictions": ["20+"],
                        "prohibited_claims": ["medical", "therapeutic", "miracle"]
                    }
                },
                "FR": {
                    "language": "fr-FR",
                    "currency": "EUR",
                    "date_format": "DD/MM/YYYY",
                    "cultural_preferences": {
                        "color_associations": {
                            "trust": ["blue", "white"],
                            "energy": ["red", "orange"],
                            "luxury": ["black", "gold", "burgundy"]
                        },
                        "messaging_style": "elegant",
                        "formality_level": "formal",
                        "call_to_action_preferences": ["Acheter maintenant", "Découvrir", "En savoir plus"]
                    },
                    "regulatory_requirements": {
                        "disclaimer_placement": "visible",
                        "age_restrictions": ["18+"],
                        "prohibited_claims": ["medical", "miraculous", "guaranteed"]
                    }
                }
            },
            "translations": {
                "campaign_messages": {
                    "Protect and Perfect Your Summer Glow": {
                        "en-US": "Protect and Perfect Your Summer Glow",
                        "en-GB": "Protect and Perfect Your Summer Glow",
                        "de-DE": "Schützen und Perfektionieren Sie Ihren Sommer-Glow",
                        "ja-JP": "夏の輝きを守り、完璧にする",
                        "fr-FR": "Protégez et Perfectionnez Votre Éclat d'Été"
                    },
                    "Fuel Your Winter Workouts": {
                        "en-US": "Fuel Your Winter Workouts", 
                        "en-GB": "Fuel Your Winter Workouts",
                        "de-DE": "Powern Sie Ihre Winter-Workouts",
                        "ja-JP": "冬のワークアウトにエネルギーを",
                        "fr-FR": "Alimentez Vos Entraînements d'Hiver"
                    },
                    "Make Your Home Smarter": {
                        "en-US": "Make Your Home Smarter",
                        "en-GB": "Make Your Home Smarter", 
                        "de-DE": "Machen Sie Ihr Zuhause intelligenter",
                        "ja-JP": "あなたの家をもっとスマートに",
                        "fr-FR": "Rendez Votre Maison Plus Intelligente"
                    }
                },
                "product_categories": {
                    "skincare": {
                        "en-US": "Skincare",
                        "en-GB": "Skincare",
                        "de-DE": "Hautpflege",
                        "ja-JP": "スキンケア",
                        "fr-FR": "Soins de la peau"
                    },
                    "fitness": {
                        "en-US": "Fitness",
                        "en-GB": "Fitness", 
                        "de-DE": "Fitness",
                        "ja-JP": "フィットネス",
                        "fr-FR": "Fitness"
                    }
                }
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_data = json.load(f)
                # Merge with defaults
                default_data.update(loaded_data)
                logger.info(f"Loaded localization data from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load localization data: {e}, using defaults")
        
        return default_data
    
    def localize_campaign_brief(self, campaign_brief: Dict[str, Any], target_market: str) -> Dict[str, Any]:
        """Localize a campaign brief for a specific market."""
        
        if target_market not in self.localization_data["markets"]:
            logger.warning(f"Market {target_market} not supported, using original brief")
            return campaign_brief
        
        market_data = self.localization_data["markets"][target_market]
        localized_brief = campaign_brief.copy()
        
        # Localize campaign message
        campaign_data = localized_brief.get("campaign_brief", {})
        original_message = campaign_data.get("campaign_message", "")
        
        if original_message:
            localized_message = self._translate_message(original_message, market_data["language"])
            campaign_data["campaign_message"] = localized_message
        
        # Adapt brand guidelines for cultural preferences
        brand_guidelines = campaign_data.get("brand_guidelines", {})
        if brand_guidelines:
            brand_guidelines = self._adapt_brand_guidelines(brand_guidelines, market_data)
            campaign_data["brand_guidelines"] = brand_guidelines
        
        # Add market-specific data
        campaign_data["localization"] = {
            "target_market": target_market,
            "language": market_data["language"],
            "currency": market_data["currency"],
            "cultural_adaptations": self._get_cultural_adaptations(market_data),
            "regulatory_requirements": market_data["regulatory_requirements"]
        }
        
        # Update target market
        campaign_data["target_market"] = target_market
        
        logger.info(f"Localized campaign for market: {target_market}")
        return localized_brief
    
    def _translate_message(self, message: str, target_language: str) -> str:
        """Translate campaign message to target language."""
        
        translations = self.localization_data.get("translations", {}).get("campaign_messages", {})
        
        if message in translations and target_language in translations[message]:
            return translations[message][target_language]
        
        # If no translation available, return original with note
        if target_language.startswith("en"):
            return message
        else:
            return f"{message} [Translation needed for {target_language}]"
    
    def _adapt_brand_guidelines(self, guidelines: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt brand guidelines for cultural preferences."""
        
        adapted_guidelines = guidelines.copy()
        cultural_prefs = market_data.get("cultural_preferences", {})
        
        # Suggest culturally appropriate colors if none specified
        if not guidelines.get("primary_colors") and "color_associations" in cultural_prefs:
            # Use trust colors as default for professional campaigns
            trust_colors = cultural_prefs["color_associations"].get("trust", ["#0066CC"])
            adapted_guidelines["suggested_colors"] = trust_colors
        
        # Add cultural context
        adapted_guidelines["cultural_context"] = {
            "messaging_style": cultural_prefs.get("messaging_style", "neutral"),
            "formality_level": cultural_prefs.get("formality_level", "casual"),
            "call_to_action_suggestions": cultural_prefs.get("call_to_action_preferences", [])
        }
        
        return adapted_guidelines
    
    def _get_cultural_adaptations(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get cultural adaptation recommendations."""
        
        cultural_prefs = market_data.get("cultural_preferences", {})
        
        return {
            "messaging_tone": cultural_prefs.get("messaging_style", "neutral"),
            "visual_preferences": cultural_prefs.get("color_associations", {}),
            "formality_guidance": cultural_prefs.get("formality_level", "casual"),
            "recommended_cta": cultural_prefs.get("call_to_action_preferences", [])
        }
    
    def get_supported_markets(self) -> List[str]:
        """Get list of supported markets."""
        return list(self.localization_data["markets"].keys())
    
    def get_market_info(self, market_code: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific market."""
        return self.localization_data["markets"].get(market_code)
    
    def validate_market_compliance(self, campaign_brief: Dict[str, Any], target_market: str) -> Dict[str, Any]:
        """Validate campaign compliance for specific market regulations."""
        
        if target_market not in self.localization_data["markets"]:
            return {"valid": False, "reason": f"Market {target_market} not supported"}
        
        market_data = self.localization_data["markets"][target_market]
        regulatory_reqs = market_data.get("regulatory_requirements", {})
        
        issues = []
        
        # Check for prohibited claims
        prohibited_claims = regulatory_reqs.get("prohibited_claims", [])
        campaign_message = campaign_brief.get("campaign_brief", {}).get("campaign_message", "")
        
        for claim in prohibited_claims:
            if claim.lower() in campaign_message.lower():
                issues.append(f"Contains prohibited claim '{claim}' for market {target_market}")
        
        # Check products for prohibited content
        products = campaign_brief.get("campaign_brief", {}).get("products", [])
        for i, product in enumerate(products):
            description = product.get("description", "").lower()
            for claim in prohibited_claims:
                if claim.lower() in description:
                    issues.append(f"Product {i+1} contains prohibited claim '{claim}' for market {target_market}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "market": target_market,
            "regulatory_requirements": regulatory_reqs
        }
    
    def generate_localization_report(self, original_brief: Dict[str, Any], localized_brief: Dict[str, Any], target_market: str) -> str:
        """Generate a human-readable localization report."""
        
        market_data = self.localization_data["markets"].get(target_market, {})
        
        report_lines = [
            "=" * 60,
            "LOCALIZATION REPORT",
            "=" * 60,
            f"Campaign: {localized_brief.get('campaign_brief', {}).get('campaign_id', 'Unknown')}",
            f"Target Market: {target_market}",
            f"Language: {market_data.get('language', 'Unknown')}",
            f"Currency: {market_data.get('currency', 'Unknown')}",
            ""
        ]
        
        # Message changes
        original_message = original_brief.get("campaign_brief", {}).get("campaign_message", "")
        localized_message = localized_brief.get("campaign_brief", {}).get("campaign_message", "")
        
        if original_message != localized_message:
            report_lines.extend([
                "📝 MESSAGE LOCALIZATION:",
                "-" * 40,
                f"Original: {original_message}",
                f"Localized: {localized_message}",
                ""
            ])
        
        # Cultural adaptations
        localization_data = localized_brief.get("campaign_brief", {}).get("localization", {})
        cultural_adaptations = localization_data.get("cultural_adaptations", {})
        
        if cultural_adaptations:
            report_lines.extend([
                "🌍 CULTURAL ADAPTATIONS:",
                "-" * 40,
                f"Messaging Tone: {cultural_adaptations.get('messaging_tone', 'N/A')}",
                f"Formality Level: {cultural_adaptations.get('formality_guidance', 'N/A')}",
                f"Recommended CTAs: {', '.join(cultural_adaptations.get('recommended_cta', []))}",
                ""
            ])
        
        # Regulatory requirements
        regulatory_reqs = localization_data.get("regulatory_requirements", {})
        if regulatory_reqs:
            report_lines.extend([
                "⚖️ REGULATORY REQUIREMENTS:",
                "-" * 40,
                f"Age Restrictions: {', '.join(regulatory_reqs.get('age_restrictions', []))}",
                f"Prohibited Claims: {', '.join(regulatory_reqs.get('prohibited_claims', []))}",
                f"Disclaimer Placement: {regulatory_reqs.get('disclaimer_placement', 'Standard')}",
                ""
            ])
        
        return "\n".join(report_lines)