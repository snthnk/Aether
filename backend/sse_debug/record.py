#!/usr/bin/env python3
"""
SSE Client - Records messages and timestamps from an SSE endpoint
"""
import requests
import json
import time
from datetime import datetime
import sys
import argparse


class SSERecorder:
    def __init__(self, url, output_file="sse_recording.json"):
        self.url = url
        self.output_file = output_file
        self.messages = []
        self.start_time = None

    def record(self, headers=None):
        """Connect to SSE endpoint and record all messages"""
        if headers is None:
            headers = {
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache'
            }

        print(f"Connecting to {self.url}")
        print(f"Recording to {self.output_file}")
        print("Press Ctrl+C to stop recording\n")

        try:
            response = requests.get(self.url, headers=headers, stream=True)
            response.raise_for_status()

            self.start_time = time.time()
            connection_time = datetime.now().isoformat()

            print(f"Connected at {connection_time}")
            print("-" * 50)

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    current_time = time.time()
                    relative_time = current_time - self.start_time
                    timestamp = datetime.now().isoformat()

                    # Parse SSE format
                    if line.startswith('data: '):
                        data = line[6:]  # Remove 'data: ' prefix
                        message_type = 'data'
                    elif line.startswith('event: '):
                        data = line[7:]  # Remove 'event: ' prefix
                        message_type = 'event'
                    elif line.startswith('id: '):
                        data = line[4:]  # Remove 'id: ' prefix
                        message_type = 'id'
                    elif line.startswith('retry: '):
                        data = line[7:]  # Remove 'retry: ' prefix
                        message_type = 'retry'
                    else:
                        data = line
                        message_type = 'raw'

                    message_record = {
                        'timestamp': timestamp,
                        'relative_time': relative_time,
                        'type': message_type,
                        'data': data,
                        'raw_line': line
                    }

                    self.messages.append(message_record)

                    # Display the message
                    print(f"[{relative_time:.3f}s] {message_type}: {data}")

        except KeyboardInterrupt:
            print("\n\nRecording stopped by user")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.save_recording()

    def save_recording(self):
        """Save recorded messages to JSON file"""
        recording_data = {
            'connection_info': {
                'url': self.url,
                'start_time': self.start_time,
                'connection_timestamp': datetime.fromtimestamp(
                    self.start_time).isoformat() if self.start_time else None,
                'total_messages': len(self.messages)
            },
            'messages': self.messages
        }

        with open(self.output_file, 'w') as f:
            json.dump(recording_data, f, indent=2)

        print(f"\nRecording saved to {self.output_file}")
        print(f"Total messages recorded: {len(self.messages)}")


def main():
    parser = argparse.ArgumentParser(description='Record SSE messages')
    parser.add_argument('url', help='SSE endpoint URL')
    parser.add_argument('-o', '--output', default='sse_recording.json',
                        help='Output file (default: sse_recording.json)')
    parser.add_argument('-H', '--header', action='append', help='Custom headers (format: "Header: Value")')

    args = parser.parse_args()

    # Parse custom headers
    headers = {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
    }

    if args.header:
        for header in args.header:
            key, value = header.split(':', 1)
            headers[key.strip()] = value.strip()

    recorder = SSERecorder(args.url, args.output)
    recorder.record(headers)


if __name__ == "__main__":
    main()