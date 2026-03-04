#!/usr/bin/env python3
"""
Vulnerable API Server - REST Endpoint for Garak Testing

This creates a REST API that Garak can target using its REST generator.
The API wraps the vulnerable chatbot (or real Claude) for automated testing.

Run with: python3 api_server.py
          python3 api_server.py --backend anthropic --model claude-haiku-4-5-20251001
Then target with: garak --target_type rest.RestGenerator --config garak_rest.yaml
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from chatbot import VulnerableChatbot


class VulnerableAPIHandler(BaseHTTPRequestHandler):
    """HTTP handler for the vulnerable chatbot API."""

    chatbot = None  # Shared instance
    token_tracker = None  # Optional, set when using anthropic backend

    def _send_json_response(self, data: dict, status: int = 200):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error(self, message: str, status: int = 400):
        """Send an error response."""
        self._send_json_response({"error": message}, status)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_json_response({
                "name": "Vulnerable Chatbot API",
                "version": "1.0.0",
                "backend": "anthropic" if VulnerableAPIHandler.token_tracker else "mock",
                "endpoints": {
                    "/chat": "POST - Send a message",
                    "/generate": "POST - Generate text (Garak compatible)",
                    "/health": "GET - Health check",
                    "/reset": "POST - Reset conversation",
                    "/stats": "GET - Token usage stats (anthropic backend only)",
                }
            })

        elif parsed.path == "/health":
            self._send_json_response({"status": "healthy"})

        elif parsed.path == "/stats":
            self._handle_stats()

        else:
            self._send_error("Not found", 404)

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length else ""

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            # Try form data
            data = {"prompt": body}

        if parsed.path == "/chat":
            self._handle_chat(data)

        elif parsed.path == "/generate":
            # Garak-compatible endpoint
            self._handle_generate(data)

        elif parsed.path == "/reset":
            VulnerableAPIHandler.chatbot.reset()
            self._send_json_response({"status": "reset"})

        else:
            self._send_error("Not found", 404)

    def _handle_chat(self, data: dict):
        """Handle chat requests."""
        prompt = data.get("prompt") or data.get("message") or data.get("text")

        if not prompt:
            self._send_error("Missing 'prompt' field")
            return

        response = VulnerableAPIHandler.chatbot.chat(prompt)

        self._send_json_response({
            "response": response,
            "prompt": prompt,
        })

    def _handle_generate(self, data: dict):
        """Handle Garak-compatible generate requests."""
        # Garak sends prompts in various formats
        prompt = (
            data.get("prompt") or
            data.get("text") or
            data.get("inputs") or
            data.get("messages", [{}])[-1].get("content", "")
        )

        if isinstance(prompt, list):
            prompt = prompt[0] if prompt else ""

        if not prompt:
            self._send_error("Missing prompt")
            return

        response = VulnerableAPIHandler.chatbot.chat(prompt)

        # Return in format Garak expects
        self._send_json_response({
            "generated_text": response,
            "text": response,
            "response": response,
            "outputs": [response],
        })

    def _handle_stats(self):
        """Handle token usage stats request."""
        tracker = VulnerableAPIHandler.token_tracker
        if tracker:
            self._send_json_response({
                "backend": "anthropic",
                "model": tracker.model,
                "input_tokens": tracker.input_tokens,
                "output_tokens": tracker.output_tokens,
                "api_calls": tracker.api_calls,
                "estimated_cost_usd": tracker.estimate_cost(),
            })
        else:
            self._send_json_response({
                "backend": "mock",
                "message": "Token tracking only available with --backend anthropic",
            })

    def log_message(self, format, *args):
        """Custom logging."""
        print(f"[API] {args[0]}")


def run_server(host: str = "0.0.0.0", port: int = 8080,
               backend: str = "mock", model: str = None,
               system_prompt: str = "weak", api_key: str = None):
    """Run the API server."""

    if backend == "anthropic":
        from anthropic_chatbot import AnthropicChatbot
        bot = AnthropicChatbot(
            api_key=api_key,
            model=model or "claude-haiku-4-5-20251001",
            system_prompt_mode=system_prompt,
        )
        VulnerableAPIHandler.chatbot = bot
        VulnerableAPIHandler.token_tracker = bot.token_tracker
        backend_label = f"Anthropic ({bot.model}, prompt={system_prompt})"
    elif backend == "bedrock":
        from bedrock_chatbot import BedrockChatbot
        bot = BedrockChatbot(
            model=model or "us.anthropic.claude-3-5-haiku-20241022-v1:0",
            system_prompt_mode=system_prompt,
        )
        VulnerableAPIHandler.chatbot = bot
        VulnerableAPIHandler.token_tracker = None
        backend_label = f"Bedrock ({bot.model}, prompt={system_prompt})"
    else:
        openai_key = os.environ.get("OPENAI_API_KEY")
        VulnerableAPIHandler.chatbot = VulnerableChatbot(api_key=openai_key)
        VulnerableAPIHandler.token_tracker = None
        backend_label = "Mock (VulnerableChatbot)"

    server = HTTPServer((host, port), VulnerableAPIHandler)

    print("=" * 60)
    print("VULNERABLE API SERVER - FOR TESTING ONLY")
    print("=" * 60)
    print(f"Server running at http://{host}:{port}")
    print(f"Backend: {backend_label}")
    print()
    print("Garak usage:")
    print(f"  garak --target_type rest.RestGenerator \\")
    print(f"    --generator_options '{{\"uri\": \"http://localhost:{port}/generate\", \"response_json\": true, \"response_json_field\": \"text\"}}' \\")
    print(f"    --probes dan")
    print()
    print("Or with curl:")
    print(f"  curl -X POST http://localhost:{port}/chat \\")
    print(f"       -H 'Content-Type: application/json' \\")
    print(f"       -d '{{\"prompt\": \"Hello!\"}}'")
    if backend == "anthropic":
        print()
        print(f"Token stats: curl http://localhost:{port}/stats")
    print("-" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        if VulnerableAPIHandler.token_tracker:
            print(f"Final stats: {VulnerableAPIHandler.token_tracker.summary()}")
        server.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vulnerable API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument(
        "--backend", default="mock", choices=["mock", "anthropic", "bedrock"],
        help="Backend: mock (VulnerableChatbot), anthropic (real Claude API), or bedrock (AWS Bedrock)"
    )
    parser.add_argument(
        "--model", default=None,
        help="Claude model to use with anthropic backend"
    )
    parser.add_argument(
        "--system-prompt", default="weak",
        choices=["none", "weak", "hardened"],
        help="System prompt mode for anthropic backend"
    )
    parser.add_argument(
        "--api-key", default=None,
        help="Anthropic API key (default: ANTHROPIC_API_KEY env var)"
    )

    args = parser.parse_args()
    run_server(
        args.host, args.port,
        backend=args.backend,
        model=args.model,
        system_prompt=args.system_prompt,
        api_key=args.api_key,
    )
