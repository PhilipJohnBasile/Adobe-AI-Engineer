#!/usr/bin/env python3
"""
Chat Assistant for Content Refinement

A conversational interface similar to ChatGPT that allows for back-and-forth
dialogue to refine content outputs, which can then be converted into documents.

Features:
- Conversational AI interface
- Context-aware responses
- Content refinement through dialogue
- Export conversations to documents
- Voice profile integration
- Multi-turn conversation memory
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class MessageRole(Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMode(Enum):
    """Conversation modes"""
    GENERAL = "general"
    CONTENT_CREATION = "content_creation"
    EDITING = "editing"
    BRAINSTORMING = "brainstorming"
    SEO_OPTIMIZATION = "seo_optimization"
    SOCIAL_MEDIA = "social_media"
    EMAIL_WRITING = "email_writing"
    COPYWRITING = "copywriting"


@dataclass
class Message:
    """Represents a message in a conversation"""
    id: str
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_api_format(self) -> Dict[str, str]:
        """Convert to OpenAI API format"""
        return {"role": self.role, "content": self.content}


@dataclass
class Conversation:
    """Represents a conversation thread"""
    id: str
    title: str
    messages: List[Message]
    mode: str = ConversationMode.GENERAL.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    user_id: str = "default"
    voice_profile_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_message_count(self) -> int:
        return len([m for m in self.messages if m.role != MessageRole.SYSTEM.value])


class ConversationStore:
    """Persistent storage for conversations"""

    def __init__(self, storage_path: str = "data/conversations"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.conversations: Dict[str, Conversation] = {}
        self._load_conversations()

    def _load_conversations(self):
        """Load conversations from disk"""
        for conv_file in self.storage_path.glob("*.json"):
            try:
                with open(conv_file, 'r') as f:
                    data = json.load(f)
                messages = [Message(**m) for m in data.get("messages", [])]
                data["messages"] = messages
                conv = Conversation(**data)
                self.conversations[conv.id] = conv
            except Exception as e:
                logger.error(f"Error loading conversation {conv_file}: {e}")

    def save_conversation(self, conv: Conversation):
        """Save conversation to disk"""
        conv_file = self.storage_path / f"{conv.id}.json"
        data = asdict(conv)
        with open(conv_file, 'w') as f:
            json.dump(data, f, indent=2)
        self.conversations[conv.id] = conv

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.conversations.get(conv_id)

    def delete_conversation(self, conv_id: str) -> bool:
        """Delete conversation"""
        if conv_id in self.conversations:
            conv_file = self.storage_path / f"{conv_id}.json"
            if conv_file.exists():
                conv_file.unlink()
            del self.conversations[conv_id]
            return True
        return False

    def list_conversations(self, user_id: str = None) -> List[Conversation]:
        """List all conversations"""
        convs = list(self.conversations.values())
        if user_id:
            convs = [c for c in convs if c.user_id == user_id]
        return sorted(convs, key=lambda c: c.updated_at, reverse=True)


class ChatAssistant:
    """
    Conversational AI assistant for content refinement.

    Features:
    - Multi-turn conversations with memory
    - Context-aware responses
    - Content generation and refinement
    - Export to documents
    - Voice profile integration
    """

    # System prompts for different modes
    MODE_PROMPTS = {
        ConversationMode.GENERAL.value: """You are a helpful AI assistant specializing in content creation and marketing.
Help users with their content needs, answer questions, and provide guidance.
Be conversational, helpful, and proactive in offering suggestions.""",

        ConversationMode.CONTENT_CREATION.value: """You are an expert content creator and copywriter.
Help users create compelling content including:
- Blog posts and articles
- Social media content
- Marketing copy
- Product descriptions
Guide users through the content creation process, ask clarifying questions, and iterate based on feedback.""",

        ConversationMode.EDITING.value: """You are an expert editor and writing coach.
Help users improve their existing content by:
- Suggesting improvements to clarity and flow
- Fixing grammar and style issues
- Strengthening arguments and messaging
- Enhancing readability
Always explain your suggestions and offer alternatives.""",

        ConversationMode.BRAINSTORMING.value: """You are a creative brainstorming partner.
Help users generate ideas by:
- Asking thought-provoking questions
- Offering multiple perspectives
- Building on their ideas
- Suggesting unexpected connections
Be enthusiastic and encourage creative thinking.""",

        ConversationMode.SEO_OPTIMIZATION.value: """You are an SEO expert.
Help users optimize their content for search engines by:
- Suggesting keywords and phrases
- Improving meta descriptions and titles
- Enhancing content structure
- Providing readability recommendations
Balance SEO best practices with natural, engaging writing.""",

        ConversationMode.SOCIAL_MEDIA.value: """You are a social media expert.
Help users create engaging social content by:
- Crafting platform-specific posts
- Suggesting hashtags and trends
- Optimizing for engagement
- Planning content calendars
Understand each platform's unique requirements and audience expectations.""",

        ConversationMode.EMAIL_WRITING.value: """You are an email marketing expert.
Help users create effective emails by:
- Writing compelling subject lines
- Structuring persuasive email bodies
- Crafting strong CTAs
- Optimizing for deliverability
Focus on conversion and engagement while maintaining authenticity.""",

        ConversationMode.COPYWRITING.value: """You are a master copywriter.
Help users create persuasive copy using proven frameworks:
- AIDA, PAS, FAB, and other frameworks
- Emotional triggers and persuasion techniques
- Benefit-focused messaging
- Strong calls to action
Guide users through the copywriting process with expertise."""
    }

    def __init__(self, text_generator=None):
        """Initialize the chat assistant"""
        self.store = ConversationStore()

        # Import text generator
        if text_generator:
            self.text_generator = text_generator
        else:
            try:
                from src.text_generator import TextGenerationEngine
                self.text_generator = TextGenerationEngine()
            except ImportError:
                self.text_generator = None
                logger.warning("Text generator not available")

    async def create_conversation(
        self,
        title: str = None,
        mode: str = ConversationMode.GENERAL.value,
        user_id: str = "default",
        voice_profile_id: str = None,
        initial_context: Dict[str, Any] = None
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            title: Conversation title (auto-generated if not provided)
            mode: Conversation mode (general, content_creation, editing, etc.)
            user_id: User ID
            voice_profile_id: Voice profile for consistent tone
            initial_context: Initial context (product info, brand guidelines, etc.)

        Returns:
            Created Conversation
        """
        conv_id = str(uuid.uuid4())[:8]
        title = title or f"Conversation {conv_id}"

        # Create system message based on mode
        system_prompt = self.MODE_PROMPTS.get(mode, self.MODE_PROMPTS[ConversationMode.GENERAL.value])

        # Add context to system prompt if provided
        if initial_context:
            context_str = "\n\nContext provided by user:\n"
            for key, value in initial_context.items():
                context_str += f"- {key}: {value}\n"
            system_prompt += context_str

        # Add voice profile context
        if voice_profile_id and self.text_generator:
            profile = self.text_generator.get_voice_profile(voice_profile_id)
            if profile:
                system_prompt += f"\n\nBrand Voice Guidelines:\n{profile.to_prompt_context()}"

        system_message = Message(
            id=str(uuid.uuid4())[:8],
            role=MessageRole.SYSTEM.value,
            content=system_prompt
        )

        conv = Conversation(
            id=conv_id,
            title=title,
            messages=[system_message],
            mode=mode,
            user_id=user_id,
            voice_profile_id=voice_profile_id,
            context=initial_context or {}
        )

        self.store.save_conversation(conv)
        logger.info(f"Created conversation: {conv_id} - {title}")

        return conv

    async def chat(
        self,
        conv_id: str,
        message: str,
        attachments: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send a message and get a response.

        Args:
            conv_id: Conversation ID
            message: User message
            attachments: Optional attachments (content to refine, etc.)

        Returns:
            Dict with response and metadata
        """
        conv = self.store.get_conversation(conv_id)
        if not conv:
            return {"error": "Conversation not found", "success": False}

        # Add user message
        user_msg = Message(
            id=str(uuid.uuid4())[:8],
            role=MessageRole.USER.value,
            content=message,
            metadata={"attachments": attachments} if attachments else {}
        )
        conv.messages.append(user_msg)

        # Prepare messages for API
        api_messages = [m.to_api_format() for m in conv.messages]

        # Add attachment context if provided
        if attachments:
            attachment_context = "\n\n[User provided the following content for reference/refinement]:\n"
            for att in attachments:
                attachment_context += f"\n---\n{att.get('content', '')}\n---\n"
            api_messages[-1]["content"] += attachment_context

        # Generate response
        if not self.text_generator or not self.text_generator.available:
            response_content = self._fallback_response(message, conv.mode)
            tokens_used = 0
        else:
            try:
                # Build messages string for generation
                messages_for_gen = api_messages

                result = await self.text_generator.async_client.chat.completions.create(
                    model=self.text_generator.DEFAULT_MODEL,
                    messages=messages_for_gen,
                    temperature=0.7,
                    max_tokens=2000
                )

                response_content = result.choices[0].message.content
                tokens_used = result.usage.total_tokens

                # Track costs
                self.text_generator.total_tokens_used += tokens_used

            except Exception as e:
                logger.error(f"Chat error: {e}")
                response_content = self._fallback_response(message, conv.mode)
                tokens_used = 0

        # Add assistant message
        assistant_msg = Message(
            id=str(uuid.uuid4())[:8],
            role=MessageRole.ASSISTANT.value,
            content=response_content,
            metadata={"tokens_used": tokens_used}
        )
        conv.messages.append(assistant_msg)

        # Update conversation
        conv.updated_at = datetime.now().isoformat()

        # Auto-update title based on first user message
        if conv.get_message_count() == 2:  # First exchange
            conv.title = self._generate_title(message)

        self.store.save_conversation(conv)

        return {
            "success": True,
            "message_id": assistant_msg.id,
            "content": response_content,
            "tokens_used": tokens_used,
            "conversation_id": conv_id,
            "message_count": conv.get_message_count()
        }

    def _fallback_response(self, message: str, mode: str) -> str:
        """Generate fallback response when API unavailable"""
        fallbacks = {
            ConversationMode.GENERAL.value: "I understand you're asking about '{}'. While I'm currently in limited mode, I'd be happy to help once full capabilities are restored.",
            ConversationMode.CONTENT_CREATION.value: "I see you want to create content about '{}'. Let me help you with that once full capabilities are available.",
            ConversationMode.EDITING.value: "I'd be glad to help edit your content about '{}'. Please try again shortly.",
            ConversationMode.BRAINSTORMING.value: "Great topic for brainstorming: '{}'. Let's explore this together when full capabilities are restored.",
        }
        template = fallbacks.get(mode, fallbacks[ConversationMode.GENERAL.value])
        topic = message[:50] + "..." if len(message) > 50 else message
        return template.format(topic)

    def _generate_title(self, first_message: str) -> str:
        """Generate conversation title from first message"""
        # Simple title generation - take first few words
        words = first_message.split()[:6]
        title = " ".join(words)
        if len(first_message.split()) > 6:
            title += "..."
        return title

    async def refine_output(
        self,
        conv_id: str,
        content: str,
        feedback: str
    ) -> Dict[str, Any]:
        """
        Refine generated content based on feedback.

        Args:
            conv_id: Conversation ID
            content: Content to refine
            feedback: User feedback/instructions

        Returns:
            Dict with refined content
        """
        refinement_prompt = f"""Please refine the following content based on my feedback:

CURRENT CONTENT:
{content}

MY FEEDBACK:
{feedback}

Please provide the refined version that addresses my feedback."""

        return await self.chat(conv_id, refinement_prompt)

    async def convert_to_document(
        self,
        conv_id: str,
        include_all: bool = False
    ) -> Dict[str, Any]:
        """
        Convert conversation to a document.

        Args:
            conv_id: Conversation ID
            include_all: Include all messages or just final content

        Returns:
            Dict with document content
        """
        conv = self.store.get_conversation(conv_id)
        if not conv:
            return {"error": "Conversation not found", "success": False}

        # Extract content from conversation
        if include_all:
            # Include full conversation
            content_parts = []
            content_parts.append(f"# {conv.title}\n")
            content_parts.append(f"*Conversation from {conv.created_at}*\n\n")

            for msg in conv.messages:
                if msg.role == MessageRole.SYSTEM.value:
                    continue
                elif msg.role == MessageRole.USER.value:
                    content_parts.append(f"**User:** {msg.content}\n\n")
                else:
                    content_parts.append(f"**Assistant:** {msg.content}\n\n")

            content = "\n".join(content_parts)
        else:
            # Extract just the final generated content
            # Look for the last substantial assistant message
            assistant_messages = [m for m in conv.messages if m.role == MessageRole.ASSISTANT.value]
            if assistant_messages:
                content = assistant_messages[-1].content
            else:
                content = ""

        # Create document using long-form editor if available
        try:
            from src.long_form_editor import LongFormEditor
            editor = LongFormEditor()
            doc = await editor.create_document(
                title=conv.title,
                owner_id=conv.user_id,
                voice_profile_id=conv.voice_profile_id
            )

            # Add content as a section
            from src.long_form_editor import Section, SectionType
            doc.sections.append(Section(
                id=str(uuid.uuid4())[:8],
                type=SectionType.PARAGRAPH.value,
                content=content
            ))

            editor.store.save_document(doc)

            return {
                "success": True,
                "document_id": doc.id,
                "title": doc.title,
                "content": content,
                "word_count": len(content.split())
            }

        except ImportError:
            # Return content without document creation
            return {
                "success": True,
                "document_id": None,
                "title": conv.title,
                "content": content,
                "word_count": len(content.split())
            }

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.store.get_conversation(conv_id)

    def list_conversations(self, user_id: str = None) -> List[Dict[str, Any]]:
        """List all conversations"""
        convs = self.store.list_conversations(user_id)
        return [
            {
                "id": c.id,
                "title": c.title,
                "mode": c.mode,
                "message_count": c.get_message_count(),
                "updated_at": c.updated_at,
                "created_at": c.created_at
            }
            for c in convs
        ]

    def delete_conversation(self, conv_id: str) -> bool:
        """Delete a conversation"""
        return self.store.delete_conversation(conv_id)

    def clear_conversation(self, conv_id: str) -> bool:
        """Clear messages but keep conversation"""
        conv = self.store.get_conversation(conv_id)
        if not conv:
            return False

        # Keep only system message
        conv.messages = [m for m in conv.messages if m.role == MessageRole.SYSTEM.value]
        conv.updated_at = datetime.now().isoformat()
        self.store.save_conversation(conv)
        return True

    def get_available_modes(self) -> List[Dict[str, str]]:
        """Get available conversation modes"""
        return [
            {"id": mode.value, "name": mode.value.replace("_", " ").title()}
            for mode in ConversationMode
        ]

    async def suggest_next_steps(self, conv_id: str) -> List[str]:
        """Suggest next steps based on conversation"""
        conv = self.store.get_conversation(conv_id)
        if not conv:
            return []

        # Mode-specific suggestions
        suggestions = {
            ConversationMode.CONTENT_CREATION.value: [
                "Would you like me to expand on any section?",
                "Should I add more examples or statistics?",
                "Would you like alternative versions?",
                "Should I optimize this for SEO?",
                "Ready to export this as a document?"
            ],
            ConversationMode.EDITING.value: [
                "Should I simplify the language?",
                "Would you like me to make it more concise?",
                "Should I change the tone?",
                "Would you like me to check for consistency?",
                "Ready to finalize the edits?"
            ],
            ConversationMode.BRAINSTORMING.value: [
                "Want to explore any of these ideas further?",
                "Should I generate more variations?",
                "Would you like me to combine ideas?",
                "Ready to develop one of these into content?",
                "Should I create an outline from these ideas?"
            ],
            ConversationMode.SEO_OPTIMIZATION.value: [
                "Should I suggest more keywords?",
                "Would you like me to improve the meta description?",
                "Should I restructure for better readability?",
                "Would you like competitor keyword analysis?",
                "Ready to implement the SEO recommendations?"
            ]
        }

        return suggestions.get(conv.mode, [
            "What would you like to do next?",
            "Should I help with something else?",
            "Ready to export this content?"
        ])


# Demo function
async def demo_chat_assistant():
    """Demonstrate chat assistant capabilities"""
    print("Chat Assistant Demo")
    print("=" * 50)

    assistant = ChatAssistant()

    # Show available modes
    print("\n1. Available conversation modes:")
    for mode in assistant.get_available_modes():
        print(f"   - {mode['name']}")

    # Create a conversation
    print("\n2. Creating content creation conversation...")
    conv = await assistant.create_conversation(
        title="Blog Post Brainstorm",
        mode=ConversationMode.CONTENT_CREATION.value,
        initial_context={
            "topic": "AI in Marketing",
            "audience": "Marketing professionals",
            "goal": "Educational blog post"
        }
    )
    print(f"   Created: {conv.id} - {conv.title}")

    # Simulate a chat
    print("\n3. Starting conversation...")
    print("   User: Help me write a blog post about AI tools for content creation")

    if assistant.text_generator and assistant.text_generator.available:
        response = await assistant.chat(
            conv.id,
            "Help me write a blog post about AI tools for content creation"
        )
        print(f"   Assistant: {response['content'][:200]}...")
    else:
        print("   (Text generator not available for full demo)")

    # List conversations
    print("\n4. Conversations in system:")
    for c in assistant.list_conversations():
        print(f"   - {c['id']}: {c['title']} ({c['mode']})")

    print("\n Demo complete!")


if __name__ == "__main__":
    asyncio.run(demo_chat_assistant())
