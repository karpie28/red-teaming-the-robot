#!/usr/bin/env python3
"""
Vulnerable API Server - REST Endpoint for Garak Testing

This creates a REST API that Garak can target using its REST generator.
The API wraps the vulnerable chatbot for automated testing.

Run with: python api_server.py
Then target with: garak --model_type rest --model_name http://localhost:8080/chat
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from chatbot import VulnerableChatbot


class VulnerableAPIHandler(BaseHTTPRequestHandler):
    """HTTP handler for the vulnerable chatbot API."""

    chatbot = None  # Shared instance

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
                "endpoints": {
                    "/chat": "POST - Send a message",
                    "/generate": "POST - Generate text (Garak compatible)",
                    "/health": "GET - Health check",
                    "/reset": "POST - Reset conversation",
                }
            })

        elif parsed.path == "/health":
            self._send_json_response({"status": "healthy"})

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

    def log_message(self, format, *args):
        """Custom logging."""
        print(f"[API] {args[0]}")


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the API server."""
    api_key = os.environ.get("OPENAI_API_KEY")
    VulnerableAPIHandler.chatbot = VulnerableChatbot(api_key=api_key)

    server = HTTPServer((host, port), VulnerableAPIHandler)

    print("=" * 60)
    print("VULNERABLE API SERVER - FOR TESTING ONLY")
    print("=" * 60)
    print(f"Server running at http://{host}:{port}")
    print()
    print("Garak usage:")
    print(f"  garak --model_type rest.RestGenerator \\")
    print(f"        --model_name http://localhost:{port}/generate \\")
    print(f"        --probes dan")
    print()
    print("Or with curl:")
    print(f"  curl -X POST http://localhost:{port}/chat \\")
    print(f"       -H 'Content-Type: application/json' \\")
    print(f"       -d '{{\"prompt\": \"Hello!\"}}'")
    print("-" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vulnerable API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")

    args = parser.parse_args()
    run_server(args.host, args.port)
