#!/usr/bin/env python3
"""
GPT-Powered Text Generation Engine

Provides comprehensive text generation capabilities for marketing content including:
- Headlines, copy, CTAs
- Multiple copywriting frameworks (AIDA, PAS, FAB)
- Platform-specific content (Facebook, Instagram, LinkedIn, etc.)
- Long-form content generation
- Text transformation (tone, reading level, style)
"""

import asyncio
import json
import logging
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not available. Text generation will use fallback mode.")

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content that can be generated"""
    HEADLINE = "headline"
    COPY = "copy"
    CTA = "cta"
    EMAIL_SUBJECT = "email_subject"
    EMAIL_BODY = "email_body"
    SOCIAL_POST = "social_post"
    PRODUCT_DESCRIPTION = "product_description"
    BLOG_OUTLINE = "blog_outline"
    BLOG_CONTENT = "blog_content"
    AD_COPY = "ad_copy"


class CopywritingFramework(Enum):
    """Copywriting frameworks for structured content"""
    AIDA = "aida"  # Attention, Interest, Desire, Action
    PAS = "pas"    # Problem, Agitate, Solution
    FAB = "fab"    # Features, Advantages, Benefits
    FOUR_PS = "4ps"  # Promise, Picture, Proof, Push
    STAR = "star"  # Situation, Task, Action, Result
    BAB = "bab"    # Before, After, Bridge
    QUEST = "quest"  # Qualify, Understand, Educate, Stimulate, Transition


class Tone(Enum):
    """Content tone options"""
    FORMAL = "formal"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    HUMOROUS = "humorous"
    SERIOUS = "serious"
    INSPIRATIONAL = "inspirational"
    URGENT = "urgent"
    EMPATHETIC = "empathetic"
    AUTHORITATIVE = "authoritative"
    CONVERSATIONAL = "conversational"


class ReadingLevel(Enum):
    """Target reading levels"""
    ELEMENTARY = "elementary"      # Grade 5
    MIDDLE_SCHOOL = "middle_school"  # Grade 8
    HIGH_SCHOOL = "high_school"    # Grade 12
    COLLEGE = "college"            # College level
    PROFESSIONAL = "professional"  # Graduate/expert level


@dataclass
class VoiceProfile:
    """Brand voice profile for consistent content generation"""
    id: str
    name: str
    tone: str
    vocabulary_level: str
    sentence_style: str
    personality_traits: List[str]
    dos: List[str]
    donts: List[str]
    sample_phrases: List[str]
    created_at: str

    def to_prompt_context(self) -> str:
        """Convert voice profile to prompt context"""
        return f"""
Voice Profile: {self.name}
- Tone: {self.tone}
- Vocabulary: {self.vocabulary_level}
- Sentence Style: {self.sentence_style}
- Personality: {', '.join(self.personality_traits)}
- Do: {', '.join(self.dos)}
- Don't: {', '.join(self.donts)}
- Example Phrases: {', '.join(self.sample_phrases[:3])}
"""


@dataclass
class GenerationResult:
    """Result of text generation"""
    content: str
    content_type: str
    tokens_used: int
    cost: float
    model: str
    generation_time: float
    metadata: Dict[str, Any]


class TextGenerationEngine:
    """
    GPT-powered text generation engine for marketing content.

    Features:
    - Multiple content types (headlines, copy, CTAs, etc.)
    - Copywriting frameworks (AIDA, PAS, FAB, etc.)
    - Voice profile support for brand consistency
    - Platform-specific optimization
    - Cost tracking and caching
    """

    # Model configuration
    DEFAULT_MODEL = "gpt-4o"
    FAST_MODEL = "gpt-4o-mini"

    # Cost per 1K tokens (approximate)
    MODEL_COSTS = {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    }

    # Platform character limits
    PLATFORM_LIMITS = {
        "facebook_headline": 40,
        "facebook_primary": 125,
        "facebook_description": 30,
        "instagram_caption": 2200,
        "instagram_bio": 150,
        "twitter_post": 280,
        "linkedin_post": 3000,
        "linkedin_headline": 120,
        "google_ad_headline": 30,
        "google_ad_description": 90,
        "amazon_title": 200,
        "amazon_bullet": 500,
        "email_subject": 60,
        "meta_title": 60,
        "meta_description": 160,
    }

    def __init__(self, api_key: str = None):
        """Initialize the text generation engine"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if OPENAI_AVAILABLE and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            self.async_client = AsyncOpenAI(api_key=self.api_key)
            self.available = True
            logger.info("Text generation engine initialized with OpenAI")
        else:
            self.client = None
            self.async_client = None
            self.available = False
            logger.warning("Text generation engine running in fallback mode")

        # Cache for generated content
        self.cache_dir = Path("cache/text_generation")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Cost tracking
        self.total_tokens_used = 0
        self.total_cost = 0.0

        # Voice profiles
        self.voice_profiles: Dict[str, VoiceProfile] = {}
        self._load_voice_profiles()

    def _load_voice_profiles(self):
        """Load saved voice profiles"""
        profiles_file = self.cache_dir / "voice_profiles.json"
        if profiles_file.exists():
            try:
                with open(profiles_file, 'r') as f:
                    data = json.load(f)
                for profile_id, profile_data in data.items():
                    self.voice_profiles[profile_id] = VoiceProfile(**profile_data)
                logger.info(f"Loaded {len(self.voice_profiles)} voice profiles")
            except Exception as e:
                logger.error(f"Error loading voice profiles: {e}")

    def _save_voice_profiles(self):
        """Save voice profiles to disk"""
        profiles_file = self.cache_dir / "voice_profiles.json"
        try:
            data = {pid: asdict(profile) for pid, profile in self.voice_profiles.items()}
            with open(profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving voice profiles: {e}")

    def _get_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key for prompt"""
        content = f"{prompt}:{model}"
        return hashlib.md5(content.encode()).hexdigest()

    def _check_cache(self, cache_key: str) -> Optional[str]:
        """Check if response is cached"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                return data.get("content")
            except Exception:
                pass
        return None

    def _save_to_cache(self, cache_key: str, content: str, metadata: Dict):
        """Save response to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump({"content": content, "metadata": metadata}, f)
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")

    def _calculate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Calculate generation cost"""
        costs = self.MODEL_COSTS.get(model, self.MODEL_COSTS[self.DEFAULT_MODEL])
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        return input_cost + output_cost

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        use_cache: bool = True,
        voice_profile_id: str = None
    ) -> GenerationResult:
        """
        Generate text using GPT.

        Args:
            prompt: The generation prompt
            system_prompt: Optional system prompt for context
            model: Model to use (default: gpt-4o)
            temperature: Creativity level (0-1)
            max_tokens: Maximum tokens to generate
            use_cache: Whether to use cached responses
            voice_profile_id: Optional voice profile for brand consistency

        Returns:
            GenerationResult with generated content and metadata
        """
        model = model or self.DEFAULT_MODEL
        start_time = datetime.now()

        # Add voice profile context if specified
        if voice_profile_id and voice_profile_id in self.voice_profiles:
            voice_context = self.voice_profiles[voice_profile_id].to_prompt_context()
            system_prompt = f"{system_prompt or ''}\n\n{voice_context}"

        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(f"{system_prompt}:{prompt}", model)
            cached = self._check_cache(cache_key)
            if cached:
                return GenerationResult(
                    content=cached,
                    content_type="cached",
                    tokens_used=0,
                    cost=0.0,
                    model=model,
                    generation_time=0.0,
                    metadata={"cached": True}
                )

        if not self.available:
            # Fallback mode
            return self._fallback_generate(prompt, start_time)

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens

            cost = self._calculate_cost(input_tokens, output_tokens, model)
            self.total_tokens_used += total_tokens
            self.total_cost += cost

            generation_time = (datetime.now() - start_time).total_seconds()

            # Cache the result
            if use_cache:
                self._save_to_cache(cache_key, content, {
                    "model": model,
                    "tokens": total_tokens,
                    "cost": cost
                })

            return GenerationResult(
                content=content,
                content_type="generated",
                tokens_used=total_tokens,
                cost=cost,
                model=model,
                generation_time=generation_time,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "temperature": temperature
                }
            )

        except Exception as e:
            logger.error(f"Text generation error: {e}")
            return self._fallback_generate(prompt, start_time)

    def _fallback_generate(self, prompt: str, start_time: datetime) -> GenerationResult:
        """Fallback generation when API is unavailable"""
        # Extract key terms from prompt for basic content
        words = prompt.lower().split()
        product_terms = [w for w in words if len(w) > 4][:3]

        fallback_content = f"[Generated content for: {' '.join(product_terms)}]"

        return GenerationResult(
            content=fallback_content,
            content_type="fallback",
            tokens_used=0,
            cost=0.0,
            model="fallback",
            generation_time=(datetime.now() - start_time).total_seconds(),
            metadata={"fallback": True, "reason": "API unavailable"}
        )

    # ========== Headline Generation ==========

    async def generate_headlines(
        self,
        product: str,
        audience: str = None,
        tone: str = "professional",
        count: int = 5,
        max_length: int = None,
        voice_profile_id: str = None
    ) -> List[str]:
        """
        Generate headline variations.

        Args:
            product: Product or service name
            audience: Target audience description
            tone: Desired tone
            count: Number of variations
            max_length: Maximum character length
            voice_profile_id: Optional voice profile

        Returns:
            List of headline variations
        """
        system_prompt = """You are an expert copywriter specializing in compelling headlines.
Generate headlines that are attention-grabbing, benefit-focused, and action-oriented.
Return ONLY the headlines, one per line, numbered."""

        audience_context = f" for {audience}" if audience else ""
        length_context = f" (max {max_length} characters each)" if max_length else ""

        prompt = f"""Generate {count} compelling headline variations for: {product}{audience_context}

Tone: {tone}
{length_context}

Focus on:
- Clear value proposition
- Emotional triggers
- Curiosity gaps
- Power words
- Specificity"""

        result = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            voice_profile_id=voice_profile_id
        )

        # Parse headlines from response
        headlines = []
        for line in result.content.strip().split('\n'):
            line = line.strip()
            if line:
                # Remove numbering if present
                if line[0].isdigit() and '.' in line[:3]:
                    line = line.split('.', 1)[1].strip()
                if max_length and len(line) > max_length:
                    line = line[:max_length-3] + "..."
                headlines.append(line)

        return headlines[:count]

    # ========== Copy Generation ==========

    async def generate_copy(
        self,
        product: str,
        purpose: str,
        tone: str = "professional",
        length: str = "medium",
        framework: str = None,
        key_points: List[str] = None,
        cta: str = None,
        voice_profile_id: str = None
    ) -> str:
        """
        Generate marketing copy.

        Args:
            product: Product or service
            purpose: Purpose of the copy (e.g., "landing page", "email", "ad")
            tone: Desired tone
            length: "short" (~50 words), "medium" (~150 words), "long" (~300 words)
            framework: Copywriting framework to use (AIDA, PAS, etc.)
            key_points: Key points to include
            cta: Call to action to include
            voice_profile_id: Optional voice profile

        Returns:
            Generated copy text
        """
        length_map = {
            "short": "approximately 50 words",
            "medium": "approximately 150 words",
            "long": "approximately 300 words"
        }

        framework_instructions = ""
        if framework:
            framework_instructions = self._get_framework_instructions(framework)

        system_prompt = f"""You are an expert copywriter. Write compelling {purpose} copy.
{framework_instructions}
Write naturally and persuasively without using labels or headers."""

        key_points_text = ""
        if key_points:
            key_points_text = f"\n\nKey points to include:\n" + "\n".join(f"- {p}" for p in key_points)

        cta_text = f"\n\nInclude CTA: {cta}" if cta else ""

        prompt = f"""Write {purpose} copy for: {product}

Tone: {tone}
Length: {length_map.get(length, length_map['medium'])}
{key_points_text}
{cta_text}

Make it persuasive, benefit-focused, and emotionally engaging."""

        result = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=800,
            voice_profile_id=voice_profile_id
        )

        return result.content.strip()

    def _get_framework_instructions(self, framework: str) -> str:
        """Get instructions for copywriting framework"""
        frameworks = {
            "aida": """Use the AIDA framework:
- Attention: Hook the reader with a compelling opening
- Interest: Build interest with relevant benefits
- Desire: Create desire by painting a picture of success
- Action: End with a clear call to action""",

            "pas": """Use the PAS framework:
- Problem: Identify the reader's pain point
- Agitate: Amplify the problem's impact
- Solution: Present the product as the solution""",

            "fab": """Use the FAB framework:
- Features: Describe what the product does
- Advantages: Explain why these features matter
- Benefits: Show how it improves the reader's life""",

            "4ps": """Use the 4Ps framework:
- Promise: Make a bold promise
- Picture: Paint a vivid picture of success
- Proof: Provide evidence and credibility
- Push: Create urgency to act now""",

            "bab": """Use the BAB framework:
- Before: Describe life before the product
- After: Show the transformation
- Bridge: Explain how the product bridges the gap"""
        }
        return frameworks.get(framework.lower(), "")

    # ========== CTA Generation ==========

    async def generate_ctas(
        self,
        product: str,
        action: str,
        urgency: str = "medium",
        count: int = 5,
        voice_profile_id: str = None
    ) -> List[str]:
        """
        Generate call-to-action variations.

        Args:
            product: Product or service
            action: Desired action (e.g., "buy", "sign up", "download")
            urgency: "low", "medium", "high"
            count: Number of variations
            voice_profile_id: Optional voice profile

        Returns:
            List of CTA variations
        """
        urgency_context = {
            "low": "gentle and inviting",
            "medium": "encouraging with subtle urgency",
            "high": "urgent and action-oriented with scarcity"
        }

        system_prompt = """You are an expert at creating compelling calls-to-action.
Generate CTAs that are clear, action-oriented, and emotionally compelling.
Return ONLY the CTAs, one per line."""

        prompt = f"""Generate {count} call-to-action variations for {product}.

Desired action: {action}
Tone: {urgency_context.get(urgency, urgency_context['medium'])}

Mix these CTA styles:
- Benefit-focused ("Get your free...")
- Action verbs ("Start...", "Discover...", "Unlock...")
- Urgency ("Limited time...", "Don't miss...")
- Social proof ("Join 10,000+ users...")
- Risk reversal ("Try risk-free...")"""

        result = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.8,
            voice_profile_id=voice_profile_id
        )

        ctas = [line.strip() for line in result.content.strip().split('\n') if line.strip()]
        # Remove numbering if present
        ctas = [cta.split('.', 1)[1].strip() if cta[0].isdigit() and '.' in cta[:3] else cta for cta in ctas]

        return ctas[:count]

    # ========== Platform-Specific Generation ==========

    async def generate_social_post(
        self,
        product: str,
        platform: str,
        purpose: str = "promotion",
        include_hashtags: bool = True,
        include_emoji: bool = True,
        voice_profile_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate platform-specific social media post.

        Args:
            product: Product or service
            platform: Target platform (facebook, instagram, linkedin, twitter)
            purpose: Post purpose (promotion, announcement, engagement)
            include_hashtags: Whether to include hashtags
            include_emoji: Whether to include emojis
            voice_profile_id: Optional voice profile

        Returns:
            Dict with post content and metadata
        """
        platform_configs = {
            "facebook": {
                "limit": 63206,
                "optimal": 80,
                "style": "conversational, engaging, encourages comments",
                "features": "Can include links, questions, polls"
            },
            "instagram": {
                "limit": 2200,
                "optimal": 150,
                "style": "visual storytelling, emotional, aspirational",
                "features": "Heavy hashtag usage (up to 30), emojis welcomed"
            },
            "linkedin": {
                "limit": 3000,
                "optimal": 150,
                "style": "professional, insightful, thought leadership",
                "features": "Business-focused, industry insights, career-related"
            },
            "twitter": {
                "limit": 280,
                "optimal": 100,
                "style": "concise, punchy, trending-aware",
                "features": "Limited characters, hashtags important for discovery"
            }
        }

        config = platform_configs.get(platform.lower(), platform_configs["facebook"])

        emoji_instruction = "Include relevant emojis naturally" if include_emoji else "Do not use emojis"
        hashtag_instruction = "Include 3-5 relevant hashtags" if include_hashtags else "Do not include hashtags"

        system_prompt = f"""You are a social media expert specializing in {platform}.
Create engaging posts optimized for {platform}'s algorithm and audience.
Style: {config['style']}
{config['features']}"""

        prompt = f"""Create a {platform} post for: {product}

Purpose: {purpose}
Optimal length: ~{config['optimal']} characters (max {config['limit']})

{emoji_instruction}
{hashtag_instruction}

Make it engaging and shareable."""

        result = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            voice_profile_id=voice_profile_id
        )

        return {
            "platform": platform,
            "content": result.content.strip(),
            "character_count": len(result.content.strip()),
            "limit": config["limit"],
            "optimal_length": config["optimal"],
            "tokens_used": result.tokens_used,
            "cost": result.cost
        }

    # ========== Email Generation ==========

    async def generate_email(
        self,
        product: str,
        email_type: str,
        subject_variations: int = 3,
        tone: str = "professional",
        cta: str = None,
        voice_profile_id: str = None
    ) -> Dict[str, Any]:
        """
        Generate marketing email with subject lines.

        Args:
            product: Product or service
            email_type: Type of email (promotional, welcome, announcement, nurture)
            subject_variations: Number of subject line options
            tone: Desired tone
            cta: Call to action
            voice_profile_id: Optional voice profile

        Returns:
            Dict with subject lines and email body
        """
        # Generate subject lines
        subjects = await self.generate_headlines(
            product=product,
            tone=tone,
            count=subject_variations,
            max_length=60,
            voice_profile_id=voice_profile_id
        )

        # Generate email body
        system_prompt = f"""You are an expert email copywriter.
Write {email_type} emails that get opened, read, and clicked.
Use short paragraphs, clear formatting, and compelling copy."""

        cta_instruction = f"\nInclude CTA: {cta}" if cta else ""

        prompt = f"""Write a {email_type} email for: {product}

Tone: {tone}
Length: 150-250 words
{cta_instruction}

Structure:
- Hook opening line
- Value proposition
- Key benefits (bullet points if appropriate)
- Social proof or credibility
- Clear call to action
- Friendly sign-off"""

        result = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            voice_profile_id=voice_profile_id
        )

        return {
            "subject_lines": subjects,
            "body": result.content.strip(),
            "email_type": email_type,
            "tokens_used": result.tokens_used,
            "cost": result.cost
        }

    # ========== Text Transformation ==========

    async def rewrite(
        self,
        text: str,
        target_tone: str = None,
        target_reading_level: str = None,
        preserve_length: bool = True,
        voice_profile_id: str = None
    ) -> str:
        """
        Rewrite text with different tone or reading level.

        Args:
            text: Original text to rewrite
            target_tone: Target tone (from Tone enum)
            target_reading_level: Target reading level (from ReadingLevel enum)
            preserve_length: Keep similar length
            voice_profile_id: Optional voice profile

        Returns:
            Rewritten text
        """
        instructions = []

        if target_tone:
            instructions.append(f"Change the tone to {target_tone}")

        if target_reading_level:
            level_descriptions = {
                "elementary": "simple words, short sentences (5th grade level)",
                "middle_school": "clear language, moderate complexity (8th grade)",
                "high_school": "standard vocabulary, varied sentences (12th grade)",
                "college": "sophisticated vocabulary, complex ideas",
                "professional": "expert-level, industry terminology appropriate"
            }
            desc = level_descriptions.get(target_reading_level, target_reading_level)
            instructions.append(f"Adjust reading level to {desc}")

        if preserve_length:
            instructions.append("Keep the length approximately the same")

        system_prompt = """You are an expert editor. Rewrite text while preserving its core message.
Only output the rewritten text, no explanations."""

        prompt = f"""Rewrite this text:

"{text}"

Instructions:
{chr(10).join('- ' + i for i in instructions)}"""

        result = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            voice_profile_id=voice_profile_id
        )

        return result.content.strip().strip('"')

    async def simplify(self, text: str, target_level: str = "middle_school") -> str:
        """Simplify text to target reading level"""
        return await self.rewrite(text, target_reading_level=target_level)

    async def change_tone(self, text: str, target_tone: str) -> str:
        """Change the tone of text"""
        return await self.rewrite(text, target_tone=target_tone)

    # ========== Summarization ==========

    async def summarize(
        self,
        text: str,
        format: str = "paragraph",
        max_length: int = None,
        focus: str = None
    ) -> str:
        """
        Summarize long text.

        Args:
            text: Text to summarize
            format: "paragraph", "bullets", "tldr"
            max_length: Maximum words in summary
            focus: Specific aspect to focus on

        Returns:
            Summarized text
        """
        format_instructions = {
            "paragraph": "Write a concise paragraph summary",
            "bullets": "Create a bullet-point summary with 3-7 key points",
            "tldr": "Write a one-sentence TL;DR summary"
        }

        system_prompt = """You are an expert at distilling complex information into clear summaries.
Only output the summary, no additional commentary."""

        length_instruction = f" (maximum {max_length} words)" if max_length else ""
        focus_instruction = f"\nFocus especially on: {focus}" if focus else ""

        prompt = f"""{format_instructions.get(format, format_instructions['paragraph'])}{length_instruction}

Text to summarize:
{text}
{focus_instruction}"""

        result = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt
        )

        return result.content.strip()

    # ========== Voice Profile Management ==========

    async def create_voice_profile(
        self,
        name: str,
        samples: List[str],
        description: str = None
    ) -> VoiceProfile:
        """
        Create a voice profile from text samples.

        Args:
            name: Profile name
            samples: List of text samples in the brand's voice
            description: Optional description

        Returns:
            Created VoiceProfile
        """
        samples_text = "\n---\n".join(samples[:5])  # Use up to 5 samples

        system_prompt = """You are an expert at analyzing writing styles and brand voices.
Analyze the provided text samples and extract the voice characteristics.
Return a JSON object with the analysis."""

        prompt = f"""Analyze these text samples to create a brand voice profile:

{samples_text}

Return JSON with:
{{
    "tone": "primary tone (e.g., professional, casual, friendly)",
    "vocabulary_level": "simple/moderate/sophisticated/technical",
    "sentence_style": "short and punchy / varied / long and flowing",
    "personality_traits": ["trait1", "trait2", "trait3"],
    "dos": ["things to do in this voice"],
    "donts": ["things to avoid"],
    "sample_phrases": ["characteristic phrases found"]
}}"""

        result = await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3
        )

        # Parse JSON response
        try:
            # Extract JSON from response
            content = result.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            analysis = json.loads(content)
        except json.JSONDecodeError:
            # Fallback defaults
            analysis = {
                "tone": "professional",
                "vocabulary_level": "moderate",
                "sentence_style": "varied",
                "personality_traits": ["clear", "direct", "helpful"],
                "dos": ["Be concise", "Use active voice"],
                "donts": ["Use jargon", "Be overly formal"],
                "sample_phrases": []
            }

        profile_id = hashlib.md5(name.encode()).hexdigest()[:8]

        profile = VoiceProfile(
            id=profile_id,
            name=name,
            tone=analysis.get("tone", "professional"),
            vocabulary_level=analysis.get("vocabulary_level", "moderate"),
            sentence_style=analysis.get("sentence_style", "varied"),
            personality_traits=analysis.get("personality_traits", []),
            dos=analysis.get("dos", []),
            donts=analysis.get("donts", []),
            sample_phrases=analysis.get("sample_phrases", []),
            created_at=datetime.now().isoformat()
        )

        self.voice_profiles[profile_id] = profile
        self._save_voice_profiles()

        return profile

    def get_voice_profile(self, profile_id: str) -> Optional[VoiceProfile]:
        """Get voice profile by ID"""
        return self.voice_profiles.get(profile_id)

    def list_voice_profiles(self) -> List[Dict]:
        """List all voice profiles"""
        return [
            {"id": p.id, "name": p.name, "tone": p.tone}
            for p in self.voice_profiles.values()
        ]

    # ========== Usage Statistics ==========

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get generation usage statistics"""
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_cost": round(self.total_cost, 4),
            "voice_profiles_count": len(self.voice_profiles),
            "api_available": self.available
        }


# Demo function
async def demo_text_generation():
    """Demonstrate text generation capabilities"""
    print("Text Generation Engine Demo")
    print("=" * 50)

    engine = TextGenerationEngine()

    if not engine.available:
        print("OpenAI API not available. Running in fallback mode.")
        return

    # Generate headlines
    print("\n1. HEADLINE GENERATION:")
    headlines = await engine.generate_headlines(
        product="AI-Powered Marketing Platform",
        audience="small business owners",
        tone="professional",
        count=5
    )
    for i, headline in enumerate(headlines, 1):
        print(f"   {i}. {headline}")

    # Generate copy
    print("\n2. COPY GENERATION (AIDA Framework):")
    copy = await engine.generate_copy(
        product="AI-Powered Marketing Platform",
        purpose="landing page",
        framework="aida",
        key_points=["Save 10 hours/week", "AI-powered automation", "No technical skills required"]
    )
    print(f"   {copy[:300]}...")

    # Generate CTAs
    print("\n3. CTA GENERATION:")
    ctas = await engine.generate_ctas(
        product="AI Marketing Platform",
        action="start free trial",
        urgency="high",
        count=5
    )
    for cta in ctas:
        print(f"   - {cta}")

    # Generate social post
    print("\n4. SOCIAL POST (Instagram):")
    post = await engine.generate_social_post(
        product="AI Marketing Platform",
        platform="instagram",
        purpose="product launch"
    )
    print(f"   {post['content'][:200]}...")

    # Usage stats
    print("\n5. USAGE STATISTICS:")
    stats = engine.get_usage_stats()
    print(f"   Tokens used: {stats['total_tokens_used']}")
    print(f"   Total cost: ${stats['total_cost']:.4f}")


if __name__ == "__main__":
    asyncio.run(demo_text_generation())
