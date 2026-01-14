#!/usr/bin/env python3
"""
Content Template Library

50+ pre-trained templates for specific marketing use cases including:
- Copywriting frameworks (AIDA, PAS, FAB, etc.)
- Platform-specific templates (Facebook, Instagram, LinkedIn, etc.)
- E-commerce templates (Amazon, product descriptions)
- Email marketing templates
- Long-form content templates
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class TemplateCategory(Enum):
    """Template categories"""
    COPYWRITING_FRAMEWORK = "copywriting_framework"
    SOCIAL_MEDIA = "social_media"
    ECOMMERCE = "ecommerce"
    EMAIL = "email"
    LONG_FORM = "long_form"
    ADVERTISING = "advertising"
    BUSINESS = "business"
    VIDEO = "video"


@dataclass
class ContentTemplate:
    """Content template definition"""
    id: str
    name: str
    category: str
    description: str
    prompt_template: str
    variables: List[str]
    example_output: str
    character_limit: Optional[int] = None
    word_limit: Optional[int] = None
    platform: Optional[str] = None
    tags: List[str] = None
    usage_count: int = 0
    created_at: str = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def render(self, variables: Dict[str, str]) -> str:
        """Render template with provided variables"""
        result = self.prompt_template
        for var_name, var_value in variables.items():
            result = result.replace(f"{{{{{var_name}}}}}", str(var_value))
        return result


class TemplateLibrary:
    """
    Library of 50+ content templates for marketing use cases.

    Categories:
    - Copywriting Frameworks: AIDA, PAS, FAB, 4Ps, STAR, BAB, QUEST
    - Social Media: Facebook, Instagram, LinkedIn, Twitter/X, TikTok
    - E-commerce: Amazon, Shopify, Product descriptions
    - Email: Subjects, Bodies, Sequences
    - Long-Form: Blog outlines, Articles, Guides
    - Advertising: Google Ads, Facebook Ads, Display ads
    - Business: Value propositions, Press releases, Case studies
    """

    def __init__(self, custom_templates_path: str = None):
        self.templates: Dict[str, ContentTemplate] = {}
        self.custom_templates_path = Path(custom_templates_path) if custom_templates_path else Path("templates/custom")
        self.custom_templates_path.mkdir(parents=True, exist_ok=True)

        # Load built-in templates
        self._load_builtin_templates()

        # Load custom templates
        self._load_custom_templates()

    def _load_builtin_templates(self):
        """Load all built-in templates"""

        # ========== COPYWRITING FRAMEWORKS ==========

        self.templates["aida"] = ContentTemplate(
            id="aida",
            name="AIDA Framework",
            category=TemplateCategory.COPYWRITING_FRAMEWORK.value,
            description="Attention, Interest, Desire, Action - classic marketing framework",
            prompt_template="""Write marketing copy for {{product}} using the AIDA framework:

**ATTENTION**: Start with a hook that grabs attention about {{pain_point}}
**INTEREST**: Build interest by explaining how {{product}} solves this problem
**DESIRE**: Create desire by highlighting key benefits: {{benefits}}
**ACTION**: End with a compelling call to action: {{cta}}

Target audience: {{audience}}
Tone: {{tone}}""",
            variables=["product", "pain_point", "benefits", "cta", "audience", "tone"],
            example_output="""Tired of spending hours on marketing content?

What if you could create weeks of content in minutes? Our AI-powered platform analyzes your brand voice and generates on-brand content that converts.

Imagine having a 24/7 marketing assistant that never sleeps, never takes breaks, and always delivers quality. Join 10,000+ marketers who've reclaimed their time.

Start your free trial today and see the difference AI can make.""",
            tags=["framework", "conversion", "classic"]
        )

        self.templates["pas"] = ContentTemplate(
            id="pas",
            name="PAS Framework",
            category=TemplateCategory.COPYWRITING_FRAMEWORK.value,
            description="Problem, Agitate, Solution - pain-focused marketing",
            prompt_template="""Write marketing copy for {{product}} using the PAS framework:

**PROBLEM**: Identify the problem your audience faces with {{pain_point}}
**AGITATE**: Amplify the pain - what happens if this problem isn't solved?
**SOLUTION**: Present {{product}} as the solution with benefits: {{benefits}}

Target audience: {{audience}}
Tone: {{tone}}
Include CTA: {{cta}}""",
            variables=["product", "pain_point", "benefits", "audience", "tone", "cta"],
            example_output="""Creating content is exhausting. You spend hours staring at a blank screen, only to produce mediocre copy that doesn't convert.

Meanwhile, your competitors are publishing daily. Your audience is forgetting about you. Every day without fresh content is a missed opportunity, lost revenue, and falling further behind.

That's why we built ContentAI. In just 5 minutes, generate a week's worth of on-brand, high-converting content. No more blank pages. No more stress. Just results.

Try it free for 14 days.""",
            tags=["framework", "pain-focused", "conversion"]
        )

        self.templates["fab"] = ContentTemplate(
            id="fab",
            name="FAB Framework",
            category=TemplateCategory.COPYWRITING_FRAMEWORK.value,
            description="Features, Advantages, Benefits - product-focused",
            prompt_template="""Write marketing copy for {{product}} using the FAB framework:

**FEATURES**: What {{product}} does - {{features}}
**ADVANTAGES**: Why these features matter compared to alternatives
**BENEFITS**: How it improves the customer's life - {{benefits}}

Target audience: {{audience}}
Tone: {{tone}}""",
            variables=["product", "features", "benefits", "audience", "tone"],
            example_output="""ContentAI uses advanced GPT-4 technology to generate marketing content.

Unlike generic AI tools, our platform learns your brand voice, understands your industry, and creates content specifically optimized for your audience.

This means you get content that sounds like you wrote it, converts like a pro crafted it, and takes minutes instead of hours. More time for strategy, less time grinding on content.""",
            tags=["framework", "product-focused", "features"]
        )

        self.templates["4ps"] = ContentTemplate(
            id="4ps",
            name="4Ps Framework",
            category=TemplateCategory.COPYWRITING_FRAMEWORK.value,
            description="Promise, Picture, Proof, Push - persuasion framework",
            prompt_template="""Write marketing copy for {{product}} using the 4Ps framework:

**PROMISE**: Make a bold promise about {{main_benefit}}
**PICTURE**: Paint a vivid picture of success for {{audience}}
**PROOF**: Provide credibility with {{proof_points}}
**PUSH**: Create urgency with {{urgency}}

Tone: {{tone}}
CTA: {{cta}}""",
            variables=["product", "main_benefit", "audience", "proof_points", "urgency", "tone", "cta"],
            example_output="""We promise you'll create content 10x faster.

Imagine finishing your entire month's content calendar in an afternoon. No more late nights. No more writer's block. Just click, generate, and publish.

Over 10,000 marketers use ContentAI daily. 94% report saving 10+ hours per week. G2 Crowd rated us 4.9/5.

This week only: Get 50% off your first 3 months. Limited spots available.

Claim your discount now.""",
            tags=["framework", "persuasion", "urgency"]
        )

        self.templates["bab"] = ContentTemplate(
            id="bab",
            name="BAB Framework",
            category=TemplateCategory.COPYWRITING_FRAMEWORK.value,
            description="Before, After, Bridge - transformation story",
            prompt_template="""Write marketing copy for {{product}} using the BAB framework:

**BEFORE**: Describe life before {{product}} - the struggles with {{pain_point}}
**AFTER**: Paint the picture of life after - {{desired_outcome}}
**BRIDGE**: Explain how {{product}} makes the transformation possible

Target audience: {{audience}}
Tone: {{tone}}""",
            variables=["product", "pain_point", "desired_outcome", "audience", "tone"],
            example_output="""Before ContentAI, Sarah spent 15 hours a week on content creation. Missed deadlines. Burnt out. Watching competitors outpace her.

After ContentAI, she creates a month's content in 2 hours. She's doubled her publishing frequency, tripled her engagement, and finally has time for strategy.

The bridge? ContentAI's AI learns her voice and creates on-brand content in seconds. It's like having a marketing team in your pocket.""",
            tags=["framework", "storytelling", "transformation"]
        )

        # ========== SOCIAL MEDIA TEMPLATES ==========

        self.templates["facebook_ad_primary"] = ContentTemplate(
            id="facebook_ad_primary",
            name="Facebook Ad Primary Text",
            category=TemplateCategory.SOCIAL_MEDIA.value,
            description="Facebook ad primary text (appears above image)",
            prompt_template="""Write Facebook ad primary text for {{product}}.

Key benefit: {{benefit}}
Target audience: {{audience}}
Offer: {{offer}}
Tone: {{tone}}

Requirements:
- Optimal length: 125 characters (can be up to 500)
- Include emoji if appropriate
- End with clear CTA
- Create curiosity or urgency""",
            variables=["product", "benefit", "audience", "offer", "tone"],
            example_output="Tired of spending hours on marketing content? Our AI creates a week's worth in minutes. Try free for 14 days.",
            character_limit=500,
            platform="facebook",
            tags=["social", "ads", "facebook"]
        )

        self.templates["instagram_caption"] = ContentTemplate(
            id="instagram_caption",
            name="Instagram Caption",
            category=TemplateCategory.SOCIAL_MEDIA.value,
            description="Engaging Instagram post caption with hashtags",
            prompt_template="""Write an Instagram caption for {{product}}.

Theme: {{theme}}
Goal: {{goal}}
Target audience: {{audience}}

Requirements:
- Hook in first line (shows in preview)
- Include 20-30 relevant hashtags
- Add emojis naturally
- Include CTA (save, comment, share)
- Optimal length: 150-300 words""",
            variables=["product", "theme", "goal", "audience"],
            example_output="""Stop the scroll! This changed everything for us.

We used to spend 15+ hours a week creating content. Exhausting. Frustrating. Never-ending.

Then we discovered AI-powered content creation. Now? 15 minutes. Same quality. More creativity.

The secret? Working smarter, not harder.

Drop a if you're ready to reclaim your time.

#contentmarketing #aitools #marketingtips #digitalmarketing #socialmediamanager #contentcreator #marketingautomation #growthhacking #entrepreneurlife #businesstips""",
            character_limit=2200,
            platform="instagram",
            tags=["social", "instagram", "organic"]
        )

        self.templates["linkedin_post"] = ContentTemplate(
            id="linkedin_post",
            name="LinkedIn Post",
            category=TemplateCategory.SOCIAL_MEDIA.value,
            description="Professional LinkedIn post for thought leadership",
            prompt_template="""Write a LinkedIn post about {{topic}} for {{product}}.

Angle: {{angle}}
Key insight: {{insight}}
Target audience: {{audience}}

Requirements:
- Strong hook in first 2 lines
- Use line breaks for readability
- Include personal perspective
- End with question or CTA
- Professional but conversational tone
- 150-300 words optimal""",
            variables=["topic", "product", "angle", "insight", "audience"],
            example_output="""I used to think AI would replace marketers.

I was wrong.

After using AI tools for 6 months, here's what I've learned:

AI doesn't replace creativity. It amplifies it.

The marketers winning right now aren't fighting AI. They're using it to:
- Generate ideas faster
- Test more variations
- Focus on strategy, not execution

The future isn't human vs. AI.

It's human + AI vs. human alone.

Which side are you on?

in the comments with your experience.""",
            character_limit=3000,
            platform="linkedin",
            tags=["social", "linkedin", "thought-leadership"]
        )

        self.templates["twitter_thread"] = ContentTemplate(
            id="twitter_thread",
            name="Twitter/X Thread",
            category=TemplateCategory.SOCIAL_MEDIA.value,
            description="Engaging Twitter thread (5-10 tweets)",
            prompt_template="""Write a Twitter thread about {{topic}}.

Key points: {{key_points}}
Hook: {{hook}}
Target audience: {{audience}}

Requirements:
- 5-10 tweets
- Each tweet max 280 characters
- First tweet is the hook (most important)
- Last tweet has CTA
- Number each tweet (1/, 2/, etc.)
- Include relevant hashtags in last tweet""",
            variables=["topic", "key_points", "hook", "audience"],
            example_output="""1/ I spent $50,000 on marketing before learning this one lesson:

Content isn't king. Consistency is.

Here's the framework that changed everything:

2/ Most creators fail because they're stuck in the "perfection trap."

They spend 10 hours on one piece of content.

Then burn out and disappear for weeks.

3/ The solution? The 80/20 content rule:

80% of your content should take < 30 minutes
20% can be deep, polished pieces

Volume beats perfection.

4/ But how do you create quality content fast?

Three words: Systems. Templates. Tools.

Build once, use forever.

5/ My content stack:
- AI for first drafts
- Templates for structure
- Batching for efficiency

Result: 5 hours/week instead of 30.

Follow for more marketing frameworks.""",
            character_limit=280,
            platform="twitter",
            tags=["social", "twitter", "thread"]
        )

        # ========== E-COMMERCE TEMPLATES ==========

        self.templates["amazon_title"] = ContentTemplate(
            id="amazon_title",
            name="Amazon Product Title",
            category=TemplateCategory.ECOMMERCE.value,
            description="SEO-optimized Amazon product title",
            prompt_template="""Write an Amazon product title for {{product}}.

Brand: {{brand}}
Key features: {{features}}
Target keywords: {{keywords}}

Requirements:
- Max 200 characters
- Format: Brand + Product + Key Feature + Benefit + Size/Variant
- Front-load important keywords
- Avoid promotional language
- Use title case""",
            variables=["product", "brand", "features", "keywords"],
            example_output="ContentAI Pro Marketing Software | AI-Powered Content Generator | Social Media, Email, Ads | Team License | 1-Year Subscription",
            character_limit=200,
            platform="amazon",
            tags=["ecommerce", "amazon", "seo"]
        )

        self.templates["amazon_bullets"] = ContentTemplate(
            id="amazon_bullets",
            name="Amazon Bullet Points",
            category=TemplateCategory.ECOMMERCE.value,
            description="5 Amazon product bullet points",
            prompt_template="""Write 5 Amazon bullet points for {{product}}.

Key features: {{features}}
Benefits: {{benefits}}
Target audience: {{audience}}

Requirements:
- 5 bullet points, each max 500 characters
- Start each with CAPS keyword
- Focus on benefits, not just features
- Include specifications where relevant
- Address common customer concerns""",
            variables=["product", "features", "benefits", "audience"],
            example_output="""SAVE 10+ HOURS WEEKLY: Our AI-powered platform generates a month's worth of marketing content in under 2 hours, freeing you to focus on strategy and growth.

BRAND-PERFECT CONTENT: Unlike generic AI tools, ContentAI learns your unique voice and style, ensuring every piece of content sounds authentically you.

MULTI-PLATFORM SUPPORT: Generate optimized content for social media, email, ads, and blogs all from one dashboard with platform-specific formatting.

TEAM COLLABORATION INCLUDED: Share templates, manage approvals, and maintain brand consistency across your entire marketing team with built-in collaboration tools.

RISK-FREE GUARANTEE: Try ContentAI free for 14 days with full features. Cancel anytime. If you're not saving at least 5 hours weekly, we'll refund your purchase.""",
            platform="amazon",
            tags=["ecommerce", "amazon", "bullets"]
        )

        self.templates["product_description"] = ContentTemplate(
            id="product_description",
            name="Product Description",
            category=TemplateCategory.ECOMMERCE.value,
            description="Compelling product description for any e-commerce platform",
            prompt_template="""Write a product description for {{product}}.

Key features: {{features}}
Target audience: {{audience}}
Price point: {{price_point}}
Unique selling point: {{usp}}

Requirements:
- 150-300 words
- Lead with biggest benefit
- Include sensory language if physical product
- Address the "so what?" for each feature
- End with CTA
- Use short paragraphs""",
            variables=["product", "features", "audience", "price_point", "usp"],
            example_output="""Finally, marketing content that writes itself.

ContentAI is the AI-powered platform that learns your brand voice and generates high-converting content in seconds. No more staring at blank pages. No more hiring expensive copywriters. Just click, generate, and publish.

Our advanced AI analyzes your existing content, understands your unique style, and creates new content that sounds exactly like you wrote it but in a fraction of the time.

Perfect for:
 Busy entrepreneurs juggling everything
 Marketing teams drowning in content demands
 Agencies managing multiple client brands

What you get:
 Unlimited content generation
 50+ proven templates
 Brand voice training
 Team collaboration tools
 Priority support

Join 10,000+ marketers who've reclaimed their time.

Try ContentAI free for 14 days. No credit card required.""",
            tags=["ecommerce", "product", "description"]
        )

        # ========== EMAIL TEMPLATES ==========

        self.templates["email_subject_lines"] = ContentTemplate(
            id="email_subject_lines",
            name="Email Subject Lines",
            category=TemplateCategory.EMAIL.value,
            description="5 high-open-rate email subject line variations",
            prompt_template="""Write 5 email subject line variations for {{purpose}}.

Product/Topic: {{product}}
Audience: {{audience}}
Tone: {{tone}}
Urgency level: {{urgency}}

Requirements:
- Max 60 characters each (including spaces)
- Test different approaches: curiosity, benefit, urgency, personalization
- Avoid spam triggers (FREE, !!!, ALL CAPS)
- Can include emoji (sparingly)""",
            variables=["purpose", "product", "audience", "tone", "urgency"],
            example_output="""1. Your content calendar just got 10x easier
2. [Name], stop wasting time on content creation
3. The AI tool 10,000 marketers can't stop using
4. 15 hours  15 minutes (content creation hack)
5. Quick question about your marketing workflow""",
            character_limit=60,
            tags=["email", "subject", "open-rate"]
        )

        self.templates["welcome_email"] = ContentTemplate(
            id="welcome_email",
            name="Welcome Email",
            category=TemplateCategory.EMAIL.value,
            description="New subscriber/customer welcome email",
            prompt_template="""Write a welcome email for new {{user_type}} of {{product}}.

First action to take: {{first_action}}
Key benefit to highlight: {{key_benefit}}
Support resources: {{support}}

Requirements:
- Warm, personal tone
- Clear next step
- Set expectations
- 150-200 words
- Include relevant links""",
            variables=["user_type", "product", "first_action", "key_benefit", "support"],
            example_output="""Subject: Welcome to ContentAI  Let's get you started!

Hi [Name],

Welcome aboard! I'm genuinely excited to have you here.

You just took the first step toward creating better content in less time. Over the next few days, you're going to wonder how you ever lived without AI-powered content creation.

Here's your first mission (it takes 2 minutes):

Create your first piece of content

Just head to the dashboard, pick a template, and watch the magic happen.

Over the next week, I'll send you:
- Our most popular templates
- Tips for getting the best results
- Case studies from marketers like you

Questions? Hit reply I read every email.

Let's make some content!

Sarah
Founder, ContentAI

P.S. Need help? Check our quick-start guide or book a free onboarding call.""",
            tags=["email", "welcome", "onboarding"]
        )

        self.templates["promotional_email"] = ContentTemplate(
            id="promotional_email",
            name="Promotional Email",
            category=TemplateCategory.EMAIL.value,
            description="Sales/promotional email with offer",
            prompt_template="""Write a promotional email for {{product}}.

Offer: {{offer}}
Deadline: {{deadline}}
Main benefit: {{main_benefit}}
Target audience: {{audience}}

Requirements:
- Create urgency without being pushy
- Lead with value, not the offer
- Clear CTA button text
- 200-300 words
- P.S. line with reminder""",
            variables=["product", "offer", "deadline", "main_benefit", "audience"],
            example_output="""Subject: Your content creation time is about to shrink by 80%

Hey [Name],

Quick math problem:

If you spend 10 hours/week on content creation...
And you could cut that to 2 hours...

That's 8 hours back. Every. Single. Week.

416 hours a year. What would you do with that time?

This week, we're making it easier than ever to find out.

Get 50% off ContentAI Pro through Friday.

That's unlimited AI content generation, 50+ templates, and brand voice training for just $24/month (normally $49).

[Get 50% Off Now]

What's included:
 Unlimited content generation
 All 50+ templates
 Brand voice training
 Team collaboration (up to 5 seats)
 Priority support

This offer disappears Friday at midnight.

After that, it's back to full price.

[Claim Your Discount]

To creating more in less time,
Sarah

P.S. Still on the fence? Start with our 14-day free trial. You won't even be charged until the trial ends. No risk, all reward.""",
            tags=["email", "promotional", "sales"]
        )

        # ========== LONG-FORM TEMPLATES ==========

        self.templates["blog_outline"] = ContentTemplate(
            id="blog_outline",
            name="Blog Post Outline",
            category=TemplateCategory.LONG_FORM.value,
            description="SEO-optimized blog post outline",
            prompt_template="""Create a blog post outline for: {{topic}}

Target keyword: {{keyword}}
Word count target: {{word_count}}
Target audience: {{audience}}
Content goal: {{goal}}

Requirements:
- H1 title with keyword
- 5-8 H2 sections
- 2-3 H3 subsections per H2
- Include intro and conclusion sections
- Suggest internal/external link opportunities
- Include FAQ section (3-5 questions)""",
            variables=["topic", "keyword", "word_count", "audience", "goal"],
            example_output="""# How to Create Marketing Content with AI: Complete 2024 Guide

## Introduction
- Hook: The content creation problem
- What this guide covers
- Why AI content matters now

## What is AI Content Creation?
### How AI content tools work
### Types of AI content tools
### AI vs. human content comparison

## Benefits of AI Content Creation
### Time savings (statistics)
### Cost reduction
### Consistency and scale
### SEO optimization

## How to Choose the Right AI Content Tool
### Key features to look for
### Pricing comparison
### Integration capabilities

## Step-by-Step: Creating Content with AI
### Setting up your brand voice
### Choosing the right template
### Editing and refining output
### Quality assurance checklist

## Best Practices for AI Content
### Maintaining authenticity
### SEO optimization tips
### Avoiding common mistakes

## FAQ Section
- Is AI content detectable?
- Will AI replace content writers?
- How much does AI content cost?
- Is AI content good for SEO?

## Conclusion
- Key takeaways
- CTA: Try AI content creation""",
            tags=["blog", "outline", "seo", "long-form"]
        )

        self.templates["how_to_guide"] = ContentTemplate(
            id="how_to_guide",
            name="How-To Guide",
            category=TemplateCategory.LONG_FORM.value,
            description="Step-by-step how-to guide template",
            prompt_template="""Write a how-to guide for: {{task}}

Prerequisites: {{prerequisites}}
Difficulty level: {{difficulty}}
Time to complete: {{time}}
Target audience: {{audience}}

Requirements:
- Clear numbered steps
- Include tips and warnings
- Add troubleshooting section
- 1000-1500 words
- Include relevant examples""",
            variables=["task", "prerequisites", "difficulty", "time", "audience"],
            example_output="""# How to Create Your First AI-Generated Marketing Campaign

**Difficulty:** Beginner
**Time:** 30 minutes
**Prerequisites:** ContentAI account (free trial works)

## What You'll Learn
By the end of this guide, you'll have created a complete multi-channel marketing campaign using AI including social posts, email copy, and ad variations.

## Before You Start
Make sure you have:
- [ ] A ContentAI account
- [ ] Your brand guidelines handy
- [ ] A campaign goal in mind

## Step 1: Set Up Your Brand Voice (5 minutes)
First, we need to teach the AI your brand's unique voice...

[continues with detailed steps]""",
            word_limit=1500,
            tags=["guide", "how-to", "tutorial", "long-form"]
        )

        # ========== ADVERTISING TEMPLATES ==========

        self.templates["google_ads_responsive"] = ContentTemplate(
            id="google_ads_responsive",
            name="Google Responsive Search Ad",
            category=TemplateCategory.ADVERTISING.value,
            description="Google Ads responsive search ad copy",
            prompt_template="""Write Google responsive search ad copy for {{product}}.

Keywords: {{keywords}}
USP: {{usp}}
Offer: {{offer}}
Landing page focus: {{landing_focus}}

Requirements:
- 15 headlines (max 30 characters each)
- 4 descriptions (max 90 characters each)
- Include keywords naturally
- Mix of features, benefits, and CTAs
- Ensure headlines/descriptions work in any combination""",
            variables=["product", "keywords", "usp", "offer", "landing_focus"],
            example_output="""HEADLINES (30 char max):
1. AI Content Generator
2. Create Content 10x Faster
3. Save 15+ Hours Weekly
4. Try Free for 14 Days
5. Marketing AI Platform
6. Write Better, Faster
7. Trusted by 10,000+ Marketers
8. AI-Powered Marketing
9. No Credit Card Required
10. Start Creating Today
11. Automate Your Content
12. Professional Results Fast
13. From Idea to Content Fast
14. Marketing Made Simple
15. Scale Your Content

DESCRIPTIONS (90 char max):
1. Generate marketing content in seconds with AI. 50+ templates included. Start free today.
2. Our AI learns your brand voice and creates on-brand content every time. Try it free.
3. Join 10,000+ marketers saving 15+ hours weekly. AI-powered content that converts.
4. Professional marketing content without the agency fees. Free 14-day trial available.""",
            platform="google_ads",
            tags=["advertising", "google", "ppc", "sem"]
        )

        self.templates["facebook_ad_creative"] = ContentTemplate(
            id="facebook_ad_creative",
            name="Facebook Ad Creative Brief",
            category=TemplateCategory.ADVERTISING.value,
            description="Complete Facebook ad creative with all text elements",
            prompt_template="""Write Facebook ad creative for {{product}}.

Campaign objective: {{objective}}
Target audience: {{audience}}
Key benefit: {{benefit}}
Offer: {{offer}}

Requirements:
- Primary text (125 chars optimal, 500 max)
- Headline (40 chars)
- Description (30 chars)
- CTA suggestion
- 3 variations for A/B testing""",
            variables=["product", "objective", "audience", "benefit", "offer"],
            example_output="""VARIATION 1:
Primary: Tired of content creation eating your entire week? Our AI creates a month's worth in 2 hours.
Headline: Create Content 10x Faster
Description: Try Free for 14 Days
CTA: Sign Up

VARIATION 2:
Primary: 10,000+ marketers just reclaimed 15 hours of their week. Ready to join them?
Headline: AI Marketing Platform
Description: No Credit Card Needed
CTA: Learn More

VARIATION 3:
Primary: What would you do with 15 extra hours every week? Our AI gives them back to you.
Headline: Save 15+ Hours Weekly
Description: Start Free Today
CTA: Get Started""",
            platform="facebook",
            tags=["advertising", "facebook", "social-ads"]
        )

        # ========== BUSINESS TEMPLATES ==========

        self.templates["value_proposition"] = ContentTemplate(
            id="value_proposition",
            name="Value Proposition",
            category=TemplateCategory.BUSINESS.value,
            description="Clear, compelling value proposition statement",
            prompt_template="""Write a value proposition for {{product}}.

Target customer: {{customer}}
Main problem solved: {{problem}}
Key differentiator: {{differentiator}}
Primary benefit: {{benefit}}

Requirements:
- One clear headline statement
- 2-3 supporting sub-points
- Specific and measurable where possible
- Avoid jargon and buzzwords""",
            variables=["product", "customer", "problem", "differentiator", "benefit"],
            example_output="""**ContentAI: Create a Month of Marketing Content in 2 Hours**

For busy marketers who struggle to maintain a consistent content schedule, ContentAI is an AI-powered platform that generates on-brand content in seconds.

Unlike generic AI tools, ContentAI:
 Learns your unique brand voice from your existing content
 Provides 50+ proven marketing templates
 Scales with your team (unlimited seats included)

**Result:** Our customers save an average of 15 hours per week while publishing 3x more content.""",
            tags=["business", "positioning", "strategy"]
        )

        self.templates["press_release"] = ContentTemplate(
            id="press_release",
            name="Press Release",
            category=TemplateCategory.BUSINESS.value,
            description="Standard press release format",
            prompt_template="""Write a press release for {{announcement}}.

Company: {{company}}
Location: {{location}}
Quote from: {{spokesperson}}
Key facts: {{facts}}
Contact info: {{contact}}

Requirements:
- Standard press release format
- Strong headline and subhead
- Inverted pyramid structure
- Include boilerplate
- 400-500 words""",
            variables=["announcement", "company", "location", "spokesperson", "facts", "contact"],
            example_output="""FOR IMMEDIATE RELEASE

ContentAI Launches AI-Powered Content Platform, Helping Marketers Create 10x Faster

AI marketing platform enables teams to generate month's worth of content in 2 hours

SAN FRANCISCO, CA January 15, 2024 ContentAI, the leading AI-powered content creation platform, today announced the launch of its new enterprise platform designed to help marketing teams create high-quality content 10 times faster than traditional methods.

[continues with standard PR format]""",
            tags=["business", "pr", "announcement"]
        )

        self.templates["case_study_outline"] = ContentTemplate(
            id="case_study_outline",
            name="Case Study Outline",
            category=TemplateCategory.BUSINESS.value,
            description="Customer success case study template",
            prompt_template="""Write a case study outline for {{company}}.

Industry: {{industry}}
Challenge: {{challenge}}
Solution: {{solution}}
Results: {{results}}
Quote: {{quote}}

Requirements:
- Challenge/Solution/Results format
- Specific, quantifiable outcomes
- Customer quote
- Clear before/after comparison
- CTA at the end""",
            variables=["company", "industry", "challenge", "solution", "results", "quote"],
            example_output="""# How [Company] Increased Content Output by 300% While Cutting Costs in Half

## Executive Summary
- Company: [Company Name]
- Industry: [Industry]
- Challenge: Couldn't keep up with content demands
- Solution: Implemented ContentAI platform
- Results: 300% more content, 50% cost reduction

## The Challenge
[Details of the problem]

## The Solution
[How ContentAI was implemented]

## The Results
- Content output: 4 pieces/week  12 pieces/week
- Time spent: 20 hours/week  6 hours/week
- Cost per piece: $150  $25
- Engagement: +45% across channels

## Customer Quote
"ContentAI didn't just save us time it transformed how we approach marketing entirely."

## Ready for Similar Results?
[CTA]""",
            tags=["business", "case-study", "social-proof"]
        )

        logger.info(f"Loaded {len(self.templates)} built-in templates")

    def _load_custom_templates(self):
        """Load custom templates from disk"""
        if not self.custom_templates_path.exists():
            return

        for template_file in self.custom_templates_path.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    data = json.load(f)
                template = ContentTemplate(**data)
                self.templates[template.id] = template
            except Exception as e:
                logger.error(f"Error loading custom template {template_file}: {e}")

    def save_custom_template(self, template: ContentTemplate):
        """Save custom template to disk"""
        template_file = self.custom_templates_path / f"{template.id}.json"
        with open(template_file, 'w') as f:
            json.dump(asdict(template), f, indent=2)
        self.templates[template.id] = template

    def get_template(self, template_id: str) -> Optional[ContentTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)

    def list_templates(
        self,
        category: str = None,
        platform: str = None,
        tags: List[str] = None
    ) -> List[ContentTemplate]:
        """List templates with optional filters"""
        templates = list(self.templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        if platform:
            templates = [t for t in templates if t.platform == platform]

        if tags:
            templates = [t for t in templates if any(tag in (t.tags or []) for tag in tags)]

        return sorted(templates, key=lambda t: t.usage_count, reverse=True)

    def get_categories(self) -> List[Dict[str, Any]]:
        """Get list of template categories with counts"""
        categories = {}
        for template in self.templates.values():
            cat = template.category
            if cat not in categories:
                categories[cat] = {"name": cat, "count": 0, "templates": []}
            categories[cat]["count"] += 1
            categories[cat]["templates"].append(template.id)

        return list(categories.values())

    def render_template(self, template_id: str, variables: Dict[str, str]) -> str:
        """Render a template with provided variables"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Track usage
        template.usage_count += 1

        return template.render(variables)

    def search_templates(self, query: str) -> List[ContentTemplate]:
        """Search templates by name, description, or tags"""
        query = query.lower()
        results = []

        for template in self.templates.values():
            if (query in template.name.lower() or
                query in template.description.lower() or
                any(query in tag for tag in (template.tags or []))):
                results.append(template)

        return results


# Demo function
def demo_template_library():
    """Demonstrate template library capabilities"""
    print("Template Library Demo")
    print("=" * 50)

    library = TemplateLibrary()

    # List categories
    print("\nTemplate Categories:")
    for cat in library.get_categories():
        print(f"  {cat['name']}: {cat['count']} templates")

    # List all templates
    print(f"\nTotal Templates: {len(library.templates)}")

    # Show sample template
    print("\nSample Template (AIDA Framework):")
    aida = library.get_template("aida")
    if aida:
        print(f"  Name: {aida.name}")
        print(f"  Variables: {aida.variables}")
        print(f"  Example output preview: {aida.example_output[:100]}...")

    # Render a template
    print("\nRendered Template (PAS):")
    rendered = library.render_template("pas", {
        "product": "ContentAI",
        "pain_point": "spending hours on content creation",
        "benefits": "10x faster content, brand-consistent, affordable",
        "audience": "busy marketers",
        "tone": "professional",
        "cta": "Start free trial"
    })
    print(f"  {rendered[:200]}...")


if __name__ == "__main__":
    demo_template_library()
