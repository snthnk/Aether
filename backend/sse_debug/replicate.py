#!/usr/bin/env python3
"""
FastAPI SSE Server - Replays recorded SSE messages
"""
import json
import time
import argparse
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Query, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


class SSEServer:
    def __init__(self, recording_file: str, port: int = 8000, host: str = "localhost"):
        self.recording_file = recording_file
        self.port = port
        self.host = host
        self.app = FastAPI(title="SSE Replayer Server", version="1.0.0")
        self.recording_data = None
        self.load_recording()
        self.setup_app()

    def load_recording(self):
        """Load recorded messages from JSON file"""
        try:
            with open(self.recording_file, 'r') as f:
                self.recording_data = json.load(f)
            print(f"Loaded recording with {len(self.recording_data['messages'])} messages")
            print(f"Original URL: {self.recording_data['connection_info']['url']}")
        except Exception as e:
            print(f"Error loading recording: {e}")
            exit(1)

    def setup_app(self):
        """Setup FastAPI app with CORS and routes"""
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            """Main page with server info and options"""
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SSE Replayer Server</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .container {{ max-width: 800px; }}
                    code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
                    .endpoint {{ background-color: #e8f4f8; padding: 10px; border-radius: 5px; margin: 10px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>SSE Replayer Server</h1>
                    <p><strong>Recording file:</strong> {self.recording_file}</p>
                    <p><strong>Total messages:</strong> {len(self.recording_data['messages'])}</p>
                    <p><strong>Original URL:</strong> {self.recording_data['connection_info']['url']}</p>

                    <h2>SSE Endpoint</h2>
                    <div class="endpoint">
                        <strong>Base URL:</strong> <code>/events</code>
                    </div>

                    <h2>Options</h2>
                    <ul>
                        <li><a href="/events" target="_blank"><code>/events</code></a> - Replay with original timing</li>
                        <li><a href="/events?speed=2" target="_blank"><code>/events?speed=2</code></a> - Replay 2x faster</li>
                        <li><a href="/events?speed=0.5" target="_blank"><code>/events?speed=0.5</code></a> - Replay 2x slower</li>
                        <li><a href="/events?no_delay=true" target="_blank"><code>/events?no_delay=true</code></a> - No delays between messages</li>
                    </ul>

                    <h2>API Documentation</h2>
                    <p>Visit <a href="/docs" target="_blank">/docs</a> for interactive API documentation</p>

                    <h2>Test with curl</h2>
                    <pre><code>curl -N http://{self.host}:{self.port}/events</code></pre>
                </div>
            </body>
            </html>
            """

        @self.app.get("/events")
        async def events(
                request: Request,
                speed: Optional[float] = Query(1.0, description="Playback speed multiplier"),
                no_delay: Optional[bool] = Query(False, description="Skip delays between messages")
        ):
            """SSE endpoint that replays recorded messages"""
            return StreamingResponse(
                self.generate_events(speed, no_delay),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control"
                }
            )

        @self.app.get("/info")
        async def info():
            """Get recording information"""
            return {
                "recording_file": self.recording_file,
                "connection_info": self.recording_data['connection_info'],
                "total_messages": len(self.recording_data['messages']),
                "endpoints": {
                    "events": "/events",
                    "info": "/info",
                    "docs": "/docs"
                }
            }

    async def generate_events(self, speed: float = 1.0, no_delay: bool = False):
        """Generate SSE events based on recorded data"""
        messages = self.recording_data['messages']

        if not messages:
            yield "data: No messages in recording\n\n"
            return

        print(f"Starting replay with speed={speed}, no_delay={no_delay}")

        # Send initial connection message
        last_time = 0

        for i, message in enumerate(messages):
            # Calculate delay
            if not no_delay and i > 0:
                current_time = message['relative_time']
                delay = (current_time - last_time) / speed
                if delay > 0:
                    await asyncio.sleep(delay)

            # Format message based on type
            if message['type'] == 'data':
                yield f"data: {message['data']}\n\n"
            elif message['type'] == 'event':
                yield f"event: {message['data']}\n"
            elif message['type'] == 'id':
                yield f"id: {message['data']}\n"
            elif message['type'] == 'retry':
                yield f"retry: {message['data']}\n"
            else:
                # Raw line - handle empty lines and malformed lines
                if message['raw_line'].strip():
                    yield f"{message['raw_line']}\n"
                else:
                    yield "\n"

            last_time = message['relative_time']

        # Send completion message
        print("Replay completed")

    def run(self):
        """Start the FastAPI server"""
        print(f"Starting SSE Replayer Server on {self.host}:{self.port}")
        print(f"SSE endpoint: http://{self.host}:{self.port}/events")
        print(f"Web interface: http://{self.host}:{self.port}/")
        print(f"API docs: http://{self.host}:{self.port}/docs")

        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=True
        )


def main():
    parser = argparse.ArgumentParser(description='Replay recorded SSE messages with FastAPI')
    parser.add_argument('recording_file', help='JSON file with recorded messages')
    parser.add_argument('-p', '--port', type=int, default=8000, help='Port to run on (default: 8000)')
    parser.add_argument('-H', '--host', default='localhost', help='Host to bind to (default: localhost)')

    args = parser.parse_args()

    server = SSEServer(args.recording_file, args.port, args.host)
    server.run()


if __name__ == "__main__":
    main()