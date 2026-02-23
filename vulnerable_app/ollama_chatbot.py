#!/usr/bin/env python3
"""
Ollama Chatbot — Local LLM Integration for Red Teaming Demos

Provides the same interface as VulnerableChatbot and AnthropicChatbot
(.chat(), .reset(), .conversation_history) but sends requests to a
local Ollama instance via its REST API.

Primary use: running attacks against DeepSeek R1 and other local models
to demonstrate vulnerability differences vs. frontier models like Claude.

Requires Ollama running locally:
  brew install ollama
  ollama serve
  ollama pull deepseek-r1:8b
"""

import json
import urllib.request
import urllib.error

from anthropic_chatbot import SYSTEM_PROMPTS, Message


def check_ollama(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama is running and reachable."""
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def list_ollama_models(base_url: str = "http://localhost:11434") -> list[str]:
    """List available models in Ollama."""
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return [m["name"] for m in data.get("models", [])]
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return []


class OllamaChatbot:
    """
    Local Ollama chatbot with the same interface as AnthropicChatbot.

    Supports configurable system prompt modes (same as AnthropicChatbot):
      - "none": no system prompt
      - "weak": same prompt as VulnerableChatbot (includes secrets)
      - "hardened": production-quality with trust boundaries
    """

    def __init__(
        self,
        model: str = "deepseek-r1:8b",
        base_url: str = "http://localhost:11434",
        system_prompt_mode: str = "weak",
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.system_prompt_mode = system_prompt_mode
        self.system_prompt = SYSTEM_PROMPTS.get(system_prompt_mode, "")
        self.conversation_history: list[Message] = []

        if not check_ollama(self.base_url):
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}.\n"
                "Make sure Ollama is running:\n"
                "  brew install ollama\n"
                "  ollama serve\n"
                f"  ollama pull {self.model}"
            )

    def chat(self, user_input: str) -> str:
        """Send a message and get a response. Same interface as AnthropicChatbot."""
        self.conversation_history.append(Message("user", user_input))

        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        for m in self.conversation_history:
            messages.append({"role": m.role, "content": m.content})

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": False,
        }).encode()

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        # DeepSeek R1 is a reasoning model — first request loads the model
        # into memory and chain-of-thought can take minutes on 8B
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read().decode())
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ConnectionError(f"Ollama request failed: {e}")

        assistant_text = data.get("message", {}).get("content", "")
        self.conversation_history.append(Message("assistant", assistant_text))
        return assistant_text

    def reset(self):
        """Reset conversation history."""
        self.conversation_history = []
