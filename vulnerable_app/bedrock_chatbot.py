#!/usr/bin/env python3
"""
Bedrock Chatbot — AWS Bedrock Integration for Red Teaming Demos

Provides the same interface as VulnerableChatbot and AnthropicChatbot
(.chat(), .reset(), .conversation_history) but sends requests to
AWS Bedrock via the Converse API.

Primary use: running attacks against DeepSeek R1 on Bedrock — faster
and more reliable than local Ollama, uses your existing AWS credentials.

Requires: boto3, valid AWS credentials (aws login)
"""

import time
import warnings

warnings.filterwarnings("ignore", message=".*Boto3 will no longer support.*")

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from anthropic_chatbot import SYSTEM_PROMPTS, Message


class BedrockChatbot:
    """
    AWS Bedrock chatbot using the Converse API.

    Same interface as AnthropicChatbot and OllamaChatbot.
    Default model: DeepSeek R1 via cross-region inference profile.
    """

    MAX_RETRIES = 5
    RETRY_BASE_DELAY = 2.0  # seconds

    def __init__(
        self,
        model: str = "us.deepseek.r1-v1:0",
        region: str = "us-west-2",
        system_prompt_mode: str = "weak",
    ):
        if not HAS_BOTO3:
            raise ImportError(
                "boto3 package not installed. Run: pip3 install boto3"
            )

        self.model = model
        self.region = region
        self.system_prompt_mode = system_prompt_mode
        self.system_prompt = SYSTEM_PROMPTS.get(system_prompt_mode, "")
        self.conversation_history: list[Message] = []

        self.client = boto3.client("bedrock-runtime", region_name=region)

    def chat(self, user_input: str) -> str:
        """Send a message and get a response. Same interface as AnthropicChatbot."""
        self.conversation_history.append(Message("user", user_input))

        # Build messages for Converse API
        messages = []
        for m in self.conversation_history:
            messages.append({
                "role": m.role,
                "content": [{"text": m.content}],
            })

        kwargs = {
            "modelId": self.model,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": 4096,
                "temperature": 0.7,
                "topP": 0.9,
            },
        }

        if self.system_prompt:
            kwargs["system"] = [{"text": self.system_prompt}]

        response = self._call_with_retry(**kwargs)

        # Extract text from response, combining text + reasoning content
        content_blocks = response.get("output", {}).get("message", {}).get("content", [])
        text_parts = []
        for block in content_blocks:
            if "text" in block:
                text_parts.append(block["text"])
            elif "reasoningContent" in block:
                # Include chain-of-thought in the response — it often leaks secrets
                reasoning = block["reasoningContent"]
                if isinstance(reasoning, dict):
                    rt = reasoning.get("reasoningText", {})
                    if isinstance(rt, dict):
                        text_parts.append(f"<think>{rt.get('text', '')}</think>")
                    elif isinstance(rt, str):
                        text_parts.append(f"<think>{rt}</think>")

        assistant_text = "\n".join(text_parts).strip()
        self.conversation_history.append(Message("assistant", assistant_text))
        return assistant_text

    def _call_with_retry(self, **kwargs):
        """Call Bedrock Converse with exponential backoff on throttling."""
        for attempt in range(self.MAX_RETRIES):
            try:
                return self.client.converse(**kwargs)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code == "ThrottlingException" and attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_BASE_DELAY * (2 ** attempt)
                    print(f"  [Rate limited, retrying in {delay:.0f}s...]")
                    time.sleep(delay)
                else:
                    raise ConnectionError(f"Bedrock request failed: {e}")
            except Exception as e:
                # Catches credential errors, missing CRT, etc.
                raise ConnectionError(
                    f"Bedrock request failed: {e}\n"
                    "If this is a credential issue, run: aws login\n"
                    "If missing CRT: pip3 install --break-system-packages 'botocore[crt]'"
                )

    def reset(self):
        """Reset conversation history."""
        self.conversation_history = []
