"""
Browser Extension API Module

Provides backend API for Chrome/Edge browser extension integration.
Enables content generation and editing directly from any webpage.
"""

import os
import json
import hashlib
import secrets
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps

# Optional imports
try:
    from flask import Flask, request, jsonify, g
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

try:
    from fastapi import FastAPI, HTTPException, Depends, Header
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of extension actions."""
    GENERATE = "generate"
    REWRITE = "rewrite"
    SUMMARIZE = "summarize"
    EXPAND = "expand"
    SIMPLIFY = "simplify"
    FIX_GRAMMAR = "fix_grammar"
    CHANGE_TONE = "change_tone"
    TRANSLATE = "translate"
    CHECK_PLAGIARISM = "check_plagiarism"
    SEO_OPTIMIZE = "seo_optimize"


@dataclass
class ExtensionUser:
    """Browser extension user."""
    user_id: str
    api_key: str
    email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_active: Optional[datetime] = None
    request_count: int = 0
    rate_limit: int = 100  # requests per hour
    features_enabled: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "request_count": self.request_count,
            "rate_limit": self.rate_limit,
            "features_enabled": self.features_enabled
        }


@dataclass
class ExtensionRequest:
    """Request from browser extension."""
    request_id: str
    action: ActionType
    content: str
    context: Dict[str, Any]
    options: Dict[str, Any]
    user_id: str
    source_url: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "action": self.action.value,
            "content": self.content,
            "context": self.context,
            "options": self.options,
            "user_id": self.user_id,
            "source_url": self.source_url,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ExtensionResponse:
    """Response to browser extension."""
    request_id: str
    success: bool
    result: Optional[str]
    alternatives: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    processing_time_ms: float = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "success": self.success,
            "result": self.result,
            "alternatives": self.alternatives,
            "metadata": self.metadata,
            "error": self.error,
            "processing_time_ms": self.processing_time_ms
        }


class UserManager:
    """Manage extension users and API keys."""

    def __init__(self):
        self.users: Dict[str, ExtensionUser] = {}
        self.api_key_to_user: Dict[str, str] = {}

    def create_user(self, email: Optional[str] = None,
                    rate_limit: int = 100) -> ExtensionUser:
        """Create new extension user."""
        user_id = secrets.token_hex(16)
        api_key = f"ext_{secrets.token_hex(32)}"

        user = ExtensionUser(
            user_id=user_id,
            api_key=api_key,
            email=email,
            rate_limit=rate_limit,
            features_enabled=["generate", "rewrite", "summarize", "fix_grammar"]
        )

        self.users[user_id] = user
        self.api_key_to_user[api_key] = user_id

        logger.info(f"Created extension user: {user_id}")
        return user

    def get_user_by_api_key(self, api_key: str) -> Optional[ExtensionUser]:
        """Get user by API key."""
        user_id = self.api_key_to_user.get(api_key)
        if user_id:
            return self.users.get(user_id)
        return None

    def get_user(self, user_id: str) -> Optional[ExtensionUser]:
        """Get user by ID."""
        return self.users.get(user_id)

    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key."""
        return api_key in self.api_key_to_user

    def update_activity(self, user_id: str):
        """Update user's last activity."""
        if user_id in self.users:
            self.users[user_id].last_active = datetime.now()
            self.users[user_id].request_count += 1

    def regenerate_api_key(self, user_id: str) -> Optional[str]:
        """Regenerate user's API key."""
        if user_id not in self.users:
            return None

        user = self.users[user_id]
        old_key = user.api_key

        # Remove old key mapping
        del self.api_key_to_user[old_key]

        # Generate new key
        new_key = f"ext_{secrets.token_hex(32)}"
        user.api_key = new_key
        self.api_key_to_user[new_key] = user_id

        return new_key


class RateLimiter:
    """Rate limiting for API requests."""

    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}

    def check_rate_limit(self, user_id: str, limit: int = 100) -> bool:
        """
        Check if user is within rate limit.

        Args:
            user_id: User identifier
            limit: Maximum requests per hour

        Returns:
            True if within limit, False if exceeded
        """
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        if user_id not in self.requests:
            self.requests[user_id] = []

        # Remove old requests
        self.requests[user_id] = [
            ts for ts in self.requests[user_id] if ts > hour_ago
        ]

        # Check limit
        if len(self.requests[user_id]) >= limit:
            return False

        # Record this request
        self.requests[user_id].append(now)
        return True

    def get_remaining(self, user_id: str, limit: int = 100) -> int:
        """Get remaining requests for user."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        if user_id not in self.requests:
            return limit

        recent = [ts for ts in self.requests[user_id] if ts > hour_ago]
        return max(0, limit - len(recent))


class ActionProcessor:
    """Process extension actions."""

    def __init__(self):
        # Import modules lazily to avoid circular imports
        self.text_generator = None
        self.grammar_checker = None
        self.plagiarism_checker = None
        self.seo_optimizer = None

    def _lazy_import(self):
        """Lazy import modules when first needed."""
        if self.text_generator is None:
            try:
                from src.text_generator import TextGenerationEngine
                self.text_generator = TextGenerationEngine()
            except ImportError:
                logger.warning("TextGenerationEngine not available")

        if self.grammar_checker is None:
            try:
                from src.grammar_checker import GrammarChecker
                self.grammar_checker = GrammarChecker()
            except ImportError:
                logger.warning("GrammarChecker not available")

        if self.plagiarism_checker is None:
            try:
                from src.plagiarism_checker import PlagiarismChecker
                self.plagiarism_checker = PlagiarismChecker()
            except ImportError:
                logger.warning("PlagiarismChecker not available")

        if self.seo_optimizer is None:
            try:
                from src.seo_optimizer import SEOOptimizer
                self.seo_optimizer = SEOOptimizer()
            except ImportError:
                logger.warning("SEOOptimizer not available")

    async def process(self, request: ExtensionRequest) -> ExtensionResponse:
        """Process an extension action request."""
        self._lazy_import()
        start_time = datetime.now()

        try:
            result = None
            alternatives = []
            metadata = {}

            if request.action == ActionType.GENERATE:
                result, alternatives = await self._process_generate(request)

            elif request.action == ActionType.REWRITE:
                result, alternatives = await self._process_rewrite(request)

            elif request.action == ActionType.SUMMARIZE:
                result = await self._process_summarize(request)

            elif request.action == ActionType.EXPAND:
                result = await self._process_expand(request)

            elif request.action == ActionType.SIMPLIFY:
                result = await self._process_simplify(request)

            elif request.action == ActionType.FIX_GRAMMAR:
                result, metadata = self._process_grammar(request)

            elif request.action == ActionType.CHANGE_TONE:
                result = await self._process_tone_change(request)

            elif request.action == ActionType.TRANSLATE:
                result = await self._process_translate(request)

            elif request.action == ActionType.CHECK_PLAGIARISM:
                metadata = self._process_plagiarism(request)
                result = f"Originality: {metadata.get('originality', 0):.1f}%"

            elif request.action == ActionType.SEO_OPTIMIZE:
                result, metadata = self._process_seo(request)

            else:
                raise ValueError(f"Unknown action: {request.action}")

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return ExtensionResponse(
                request_id=request.request_id,
                success=True,
                result=result,
                alternatives=alternatives,
                metadata=metadata,
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"Action processing failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return ExtensionResponse(
                request_id=request.request_id,
                success=False,
                result=None,
                error=str(e),
                processing_time_ms=processing_time
            )

    async def _process_generate(self, request: ExtensionRequest) -> tuple:
        """Process generate action."""
        if self.text_generator is None:
            return self._fallback_generate(request)

        content_type = request.options.get("type", "copy")
        tone = request.options.get("tone", "professional")

        result = await self.text_generator.generate_copy(
            product=request.content,
            purpose=content_type,
            tone=tone,
            length=request.options.get("length", "medium")
        )

        return result.content, result.alternatives if hasattr(result, 'alternatives') else []

    async def _process_rewrite(self, request: ExtensionRequest) -> tuple:
        """Process rewrite action."""
        if self.text_generator is None:
            return self._fallback_rewrite(request)

        tone = request.options.get("tone", "same")
        result = await self.text_generator.rewrite(
            text=request.content,
            target_tone=tone,
            preserve_length=request.options.get("preserve_length", True)
        )

        return result.content, []

    async def _process_summarize(self, request: ExtensionRequest) -> str:
        """Process summarize action."""
        if self.text_generator is None:
            return self._fallback_summarize(request)

        format_type = request.options.get("format", "paragraph")
        result = await self.text_generator.summarize(
            text=request.content,
            format=format_type,
            max_length=request.options.get("max_length", 200)
        )

        return result.content

    async def _process_expand(self, request: ExtensionRequest) -> str:
        """Process expand action."""
        if self.text_generator is None:
            return self._fallback_expand(request)

        # Use rewrite with expansion instructions
        result = await self.text_generator.rewrite(
            text=request.content,
            target_tone="same",
            preserve_length=False,
            additional_instructions="Expand and elaborate on this content with more detail and examples."
        )

        return result.content

    async def _process_simplify(self, request: ExtensionRequest) -> str:
        """Process simplify action."""
        if self.text_generator is None:
            return self._fallback_simplify(request)

        target_level = request.options.get("reading_level", "8th grade")
        result = await self.text_generator.rewrite(
            text=request.content,
            target_reading_level=target_level
        )

        return result.content

    def _process_grammar(self, request: ExtensionRequest) -> tuple:
        """Process grammar fix action."""
        if self.grammar_checker is None:
            # Basic fallback
            return request.content, {"issues_found": 0}

        result = self.grammar_checker.check(request.content, auto_correct=True)

        return result.corrected_text or request.content, {
            "issues_found": len(result.issues),
            "issues_by_type": result.stats.get("issues_by_type", {})
        }

    async def _process_tone_change(self, request: ExtensionRequest) -> str:
        """Process tone change action."""
        target_tone = request.options.get("target_tone", "professional")

        if self.text_generator is None:
            return self._fallback_tone_change(request, target_tone)

        result = await self.text_generator.rewrite(
            text=request.content,
            target_tone=target_tone
        )

        return result.content

    async def _process_translate(self, request: ExtensionRequest) -> str:
        """Process translation action."""
        target_language = request.options.get("target_language", "Spanish")

        # Translation would typically use a dedicated translation API
        # For now, use GPT-based translation through text generator
        if self.text_generator is None:
            return f"[Translation to {target_language} not available]"

        # Use GPT for translation
        import openai
        client = openai.OpenAI()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Translate the following text to {target_language}. Maintain the same tone and style."},
                {"role": "user", "content": request.content}
            ],
            max_tokens=len(request.content) * 2
        )

        return response.choices[0].message.content

    def _process_plagiarism(self, request: ExtensionRequest) -> Dict[str, Any]:
        """Process plagiarism check action."""
        if self.plagiarism_checker is None:
            return {"originality": 100, "matches": [], "available": False}

        report = self.plagiarism_checker.check(request.content)

        return {
            "originality": report.unique_content_percentage,
            "risk_level": report.risk_level,
            "matches": [m.to_dict() for m in report.matches[:5]],
            "available": True
        }

    def _process_seo(self, request: ExtensionRequest) -> tuple:
        """Process SEO optimization action."""
        keyword = request.options.get("keyword", "")

        if self.seo_optimizer is None:
            return request.content, {"score": 0, "available": False}

        report = self.seo_optimizer.analyze_content(
            content=request.content,
            target_keyword=keyword
        )

        # Get suggestions
        suggestions = report.get("recommendations", [])

        # Optimized content could be generated by applying suggestions
        # For now, return original with recommendations
        metadata = {
            "score": report.get("overall_score", 0),
            "keyword_score": report.get("keyword_score", 0),
            "readability_score": report.get("readability_score", 0),
            "recommendations": suggestions[:5],
            "available": True
        }

        return request.content, metadata

    # Fallback methods when modules are not available
    def _fallback_generate(self, request: ExtensionRequest) -> tuple:
        """Fallback generation using basic rules."""
        content = request.content
        content_type = request.options.get("type", "copy")

        # Basic template-based generation
        templates = {
            "headline": f"Discover {content} Today",
            "copy": f"Looking for {content}? Our solution delivers exceptional results that exceed expectations.",
            "cta": f"Get Started with {content}",
            "email_subject": f"Your Guide to {content}"
        }

        result = templates.get(content_type, templates["copy"])
        return result, []

    def _fallback_rewrite(self, request: ExtensionRequest) -> tuple:
        """Fallback rewriting."""
        # Very basic word substitutions
        text = request.content
        substitutions = {
            "good": "excellent",
            "bad": "poor",
            "big": "substantial",
            "small": "compact"
        }

        for old, new in substitutions.items():
            text = text.replace(old, new)

        return text, []

    def _fallback_summarize(self, request: ExtensionRequest) -> str:
        """Fallback summarization."""
        sentences = request.content.split('.')
        if len(sentences) <= 3:
            return request.content

        # Return first and last sentences
        summary = f"{sentences[0].strip()}. [...] {sentences[-2].strip()}."
        return summary

    def _fallback_expand(self, request: ExtensionRequest) -> str:
        """Fallback expansion."""
        return f"{request.content}\n\nFurthermore, this provides additional value and benefits worth considering."

    def _fallback_simplify(self, request: ExtensionRequest) -> str:
        """Fallback simplification."""
        # Very basic - just return the original
        return request.content

    def _fallback_tone_change(self, request: ExtensionRequest, tone: str) -> str:
        """Fallback tone change."""
        text = request.content

        if tone == "casual":
            text = text.replace(".", "! ").replace("Therefore", "So")
        elif tone == "formal":
            text = text.replace("!", ".").replace("So", "Therefore")

        return text


class ExtensionAPIServer:
    """
    Main API server for browser extension.
    Supports both Flask and FastAPI backends.
    """

    def __init__(self, framework: str = "auto"):
        self.user_manager = UserManager()
        self.rate_limiter = RateLimiter()
        self.action_processor = ActionProcessor()

        # Select framework
        if framework == "auto":
            if HAS_FASTAPI:
                self.framework = "fastapi"
            elif HAS_FLASK:
                self.framework = "flask"
            else:
                raise RuntimeError("No web framework available. Install flask or fastapi.")
        else:
            self.framework = framework

        self.app = None
        self._setup_app()

        logger.info(f"Extension API server initialized with {self.framework}")

    def _setup_app(self):
        """Set up the web application."""
        if self.framework == "fastapi":
            self._setup_fastapi()
        else:
            self._setup_flask()

    def _setup_fastapi(self):
        """Set up FastAPI application."""
        self.app = FastAPI(
            title="Content AI Browser Extension API",
            description="Backend API for Chrome/Edge browser extension",
            version="1.0.0"
        )

        # CORS for browser extension
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Extension can come from any origin
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Pydantic models for FastAPI
        class ActionRequest(BaseModel):
            action: str
            content: str
            context: dict = {}
            options: dict = {}
            source_url: str = None

        class ActionResponse(BaseModel):
            request_id: str
            success: bool
            result: str = None
            alternatives: list = []
            metadata: dict = {}
            error: str = None
            processing_time_ms: float = 0

        # Dependency for API key validation
        async def verify_api_key(x_api_key: str = Header(...)):
            user = self.user_manager.get_user_by_api_key(x_api_key)
            if not user:
                raise HTTPException(status_code=401, detail="Invalid API key")

            if not self.rate_limiter.check_rate_limit(user.user_id, user.rate_limit):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            self.user_manager.update_activity(user.user_id)
            return user

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "version": "1.0.0"}

        @self.app.post("/api/v1/action", response_model=ActionResponse)
        async def process_action(
            request_data: ActionRequest,
            user: ExtensionUser = Depends(verify_api_key)
        ):
            # Create request object
            ext_request = ExtensionRequest(
                request_id=secrets.token_hex(8),
                action=ActionType(request_data.action),
                content=request_data.content,
                context=request_data.context,
                options=request_data.options,
                user_id=user.user_id,
                source_url=request_data.source_url
            )

            # Process action
            response = await self.action_processor.process(ext_request)
            return response.to_dict()

        @self.app.get("/api/v1/user")
        async def get_user_info(user: ExtensionUser = Depends(verify_api_key)):
            remaining = self.rate_limiter.get_remaining(user.user_id, user.rate_limit)
            return {
                **user.to_dict(),
                "remaining_requests": remaining
            }

        @self.app.get("/api/v1/actions")
        async def list_actions():
            return {
                "actions": [
                    {
                        "id": action.value,
                        "name": action.name.replace("_", " ").title(),
                        "description": self._get_action_description(action)
                    }
                    for action in ActionType
                ]
            }

    def _setup_flask(self):
        """Set up Flask application."""
        self.app = Flask(__name__)
        CORS(self.app)

        def require_api_key(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                api_key = request.headers.get('X-API-Key')
                if not api_key:
                    return jsonify({"error": "API key required"}), 401

                user = self.user_manager.get_user_by_api_key(api_key)
                if not user:
                    return jsonify({"error": "Invalid API key"}), 401

                if not self.rate_limiter.check_rate_limit(user.user_id, user.rate_limit):
                    return jsonify({"error": "Rate limit exceeded"}), 429

                self.user_manager.update_activity(user.user_id)
                g.user = user
                return f(*args, **kwargs)
            return decorated

        @self.app.route("/health")
        def health_check():
            return jsonify({"status": "healthy", "version": "1.0.0"})

        @self.app.route("/api/v1/action", methods=["POST"])
        @require_api_key
        def process_action():
            import asyncio

            data = request.json

            ext_request = ExtensionRequest(
                request_id=secrets.token_hex(8),
                action=ActionType(data.get("action")),
                content=data.get("content", ""),
                context=data.get("context", {}),
                options=data.get("options", {}),
                user_id=g.user.user_id,
                source_url=data.get("source_url")
            )

            # Run async processor
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(self.action_processor.process(ext_request))
            loop.close()

            return jsonify(response.to_dict())

        @self.app.route("/api/v1/user")
        @require_api_key
        def get_user_info():
            remaining = self.rate_limiter.get_remaining(g.user.user_id, g.user.rate_limit)
            return jsonify({
                **g.user.to_dict(),
                "remaining_requests": remaining
            })

        @self.app.route("/api/v1/actions")
        def list_actions():
            return jsonify({
                "actions": [
                    {
                        "id": action.value,
                        "name": action.name.replace("_", " ").title(),
                        "description": self._get_action_description(action)
                    }
                    for action in ActionType
                ]
            })

    def _get_action_description(self, action: ActionType) -> str:
        """Get description for action type."""
        descriptions = {
            ActionType.GENERATE: "Generate new content based on input",
            ActionType.REWRITE: "Rewrite content with different wording",
            ActionType.SUMMARIZE: "Create a summary of longer content",
            ActionType.EXPAND: "Expand and elaborate on content",
            ActionType.SIMPLIFY: "Simplify content for easier reading",
            ActionType.FIX_GRAMMAR: "Fix grammar and spelling errors",
            ActionType.CHANGE_TONE: "Change the tone of the content",
            ActionType.TRANSLATE: "Translate content to another language",
            ActionType.CHECK_PLAGIARISM: "Check content for originality",
            ActionType.SEO_OPTIMIZE: "Optimize content for search engines"
        }
        return descriptions.get(action, "")

    def create_user(self, email: Optional[str] = None) -> ExtensionUser:
        """Create a new extension user."""
        return self.user_manager.create_user(email)

    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
        """Run the API server."""
        if self.framework == "fastapi":
            import uvicorn
            uvicorn.run(self.app, host=host, port=port, log_level="info")
        else:
            self.app.run(host=host, port=port, debug=debug)


class ExtensionClient:
    """
    Client library for testing extension API.
    Can also be used as a Python SDK for the extension.
    """

    def __init__(self, base_url: str = "http://localhost:5000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

        if not HAS_REQUESTS:
            raise RuntimeError("requests library required for ExtensionClient")

        import requests as req_lib
        self.session = req_lib.Session()
        if api_key:
            self.session.headers["X-API-Key"] = api_key

    def set_api_key(self, api_key: str):
        """Set API key for requests."""
        self.api_key = api_key
        self.session.headers["X-API-Key"] = api_key

    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def get_user(self) -> Dict[str, Any]:
        """Get current user info."""
        response = self.session.get(f"{self.base_url}/api/v1/user")
        response.raise_for_status()
        return response.json()

    def list_actions(self) -> List[Dict[str, Any]]:
        """List available actions."""
        response = self.session.get(f"{self.base_url}/api/v1/actions")
        response.raise_for_status()
        return response.json().get("actions", [])

    def execute_action(self, action: str, content: str,
                       options: Optional[Dict] = None,
                       context: Optional[Dict] = None,
                       source_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute an action.

        Args:
            action: Action type (generate, rewrite, summarize, etc.)
            content: Content to process
            options: Action-specific options
            context: Additional context
            source_url: Source URL where content was found

        Returns:
            Action response
        """
        payload = {
            "action": action,
            "content": content,
            "options": options or {},
            "context": context or {},
            "source_url": source_url
        }

        response = self.session.post(
            f"{self.base_url}/api/v1/action",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    # Convenience methods
    def generate(self, prompt: str, content_type: str = "copy",
                 tone: str = "professional") -> str:
        """Generate content."""
        result = self.execute_action(
            "generate",
            prompt,
            options={"type": content_type, "tone": tone}
        )
        return result.get("result", "")

    def rewrite(self, text: str, tone: Optional[str] = None) -> str:
        """Rewrite text."""
        options = {}
        if tone:
            options["tone"] = tone

        result = self.execute_action("rewrite", text, options=options)
        return result.get("result", "")

    def summarize(self, text: str, format: str = "paragraph") -> str:
        """Summarize text."""
        result = self.execute_action(
            "summarize",
            text,
            options={"format": format}
        )
        return result.get("result", "")

    def fix_grammar(self, text: str) -> str:
        """Fix grammar errors."""
        result = self.execute_action("fix_grammar", text)
        return result.get("result", "")

    def check_plagiarism(self, text: str) -> Dict[str, Any]:
        """Check for plagiarism."""
        result = self.execute_action("check_plagiarism", text)
        return result.get("metadata", {})


# Chrome Extension Manifest Generator
def generate_extension_manifest(api_url: str = "http://localhost:5000",
                                name: str = "Content AI Assistant",
                                version: str = "1.0.0") -> Dict[str, Any]:
    """
    Generate Chrome extension manifest.json

    Args:
        api_url: Backend API URL
        name: Extension name
        version: Extension version

    Returns:
        Manifest dictionary
    """
    return {
        "manifest_version": 3,
        "name": name,
        "version": version,
        "description": "AI-powered content generation and editing assistant",
        "permissions": [
            "activeTab",
            "contextMenus",
            "storage"
        ],
        "host_permissions": [
            f"{api_url}/*"
        ],
        "action": {
            "default_popup": "popup.html",
            "default_icon": {
                "16": "icons/icon16.png",
                "32": "icons/icon32.png",
                "48": "icons/icon48.png",
                "128": "icons/icon128.png"
            }
        },
        "background": {
            "service_worker": "background.js",
            "type": "module"
        },
        "content_scripts": [
            {
                "matches": ["<all_urls>"],
                "js": ["content.js"],
                "css": ["content.css"]
            }
        ],
        "icons": {
            "16": "icons/icon16.png",
            "32": "icons/icon32.png",
            "48": "icons/icon48.png",
            "128": "icons/icon128.png"
        }
    }


def generate_extension_background_js(api_url: str = "http://localhost:5000") -> str:
    """Generate background.js for Chrome extension."""
    return f'''
// Background service worker for Content AI Extension

const API_URL = "{api_url}";

// Context menu setup
chrome.runtime.onInstalled.addListener(() => {{
  chrome.contextMenus.create({{
    id: "contentai-rewrite",
    title: "Rewrite with AI",
    contexts: ["selection"]
  }});

  chrome.contextMenus.create({{
    id: "contentai-summarize",
    title: "Summarize with AI",
    contexts: ["selection"]
  }});

  chrome.contextMenus.create({{
    id: "contentai-fix-grammar",
    title: "Fix Grammar",
    contexts: ["selection"]
  }});
}});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {{
  const selectedText = info.selectionText;
  if (!selectedText) return;

  let action;
  switch (info.menuItemId) {{
    case "contentai-rewrite":
      action = "rewrite";
      break;
    case "contentai-summarize":
      action = "summarize";
      break;
    case "contentai-fix-grammar":
      action = "fix_grammar";
      break;
    default:
      return;
  }}

  // Get API key from storage
  const {{ apiKey }} = await chrome.storage.sync.get("apiKey");
  if (!apiKey) {{
    chrome.tabs.sendMessage(tab.id, {{
      type: "error",
      message: "Please configure your API key in the extension settings"
    }});
    return;
  }}

  try {{
    const response = await fetch(`${{API_URL}}/api/v1/action`, {{
      method: "POST",
      headers: {{
        "Content-Type": "application/json",
        "X-API-Key": apiKey
      }},
      body: JSON.stringify({{
        action: action,
        content: selectedText,
        source_url: tab.url
      }})
    }});

    const data = await response.json();

    chrome.tabs.sendMessage(tab.id, {{
      type: "result",
      action: action,
      result: data.result,
      metadata: data.metadata
    }});
  }} catch (error) {{
    chrome.tabs.sendMessage(tab.id, {{
      type: "error",
      message: error.message
    }});
  }}
}});
'''


if __name__ == "__main__":
    print("=" * 60)
    print("BROWSER EXTENSION API MODULE")
    print("=" * 60)

    # Check available frameworks
    print(f"\nFlask available: {HAS_FLASK}")
    print(f"FastAPI available: {HAS_FASTAPI}")

    print("\n" + "-" * 60)
    print("API Endpoints:")
    print("-" * 60)
    print("  GET  /health             - Health check")
    print("  POST /api/v1/action      - Execute action")
    print("  GET  /api/v1/user        - Get user info")
    print("  GET  /api/v1/actions     - List available actions")

    print("\n" + "-" * 60)
    print("Available Actions:")
    print("-" * 60)
    for action in ActionType:
        print(f"  - {action.value}")

    print("\n" + "-" * 60)
    print("Usage Example:")
    print("-" * 60)
    print("""
    # Start server
    from src.extension_api import ExtensionAPIServer

    server = ExtensionAPIServer()
    user = server.create_user(email="user@example.com")
    print(f"API Key: {user.api_key}")

    server.run(port=5000)

    # Client usage
    from src.extension_api import ExtensionClient

    client = ExtensionClient(api_key="ext_...")
    result = client.rewrite("This is sample text to rewrite")
    print(result)
    """)
