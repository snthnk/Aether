import asyncio
import json
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from sse_starlette import EventSourceResponse
from main import app as langapp

app = FastAPI()

initial = {
    "last_reasoning": "",
    "last_goto": "",
    "search_history": [],
    "hypotheses_and_critics": [],
    "search_system_input": None,
    "current_search_request": None,
    "papers": [],
    "summaries": [],
    "validated_summaries": [],
    "final_report": None,
    "error": None,
    "search_cycles": 0
}

nodes = ["orchestrator", "formulator", "searcher", "critics", "formulator", "searcher", "critics", "end"]

async def mock_astream_events(input_data, version="v2") -> AsyncGenerator[dict, None]:
    # Simulate each node emitting a start and end event
    for node in nodes:
        await asyncio.sleep(1)  # simulate async delay
        yield {"event": "on_chain_start", "name": node}
        await asyncio.sleep(1)
        yield {"event": "on_chat_model_stream", "data": "some llm output"}
        await asyncio.sleep(1)
        yield {"event": "on_chain_end", "name": node}

async def stream(prompt):
    async for event in mock_astream_events({"user_question": prompt, **initial}, version="v2"):
        event_type = event.get('event', None)
        agent = event.get('name', '')
        # if agent in ["_write", "RunnableSequence", "__start__", "__end__", "LangGraph"]:
        #     continue
        # if event_type == 'on_chat_model_stream':
        #     print(event['data']['chunk'].content, end='')
        if agent in ["_write", "RunnableSequence", "__start__", "__end__", "LangGraph"]:
            continue
        if event_type == 'on_chat_model_stream':
            print(event['data'])
            # print(event['data']['chunk'].content, end='')
        if event_type == 'on_chain_start':
            print(f"<{agent}>")
            yield json.dumps({"type": "agent_start", "agent": agent})
        elif event_type == 'on_chain_end':
            print(f"</{agent}>")
            yield json.dumps({"type": "agent_end", "agent": agent})

@app.post("/generate")
async def generate(req: Request):
    body = await req.json()
    prompt = body["prompt"]
    return EventSourceResponse(stream(prompt))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)