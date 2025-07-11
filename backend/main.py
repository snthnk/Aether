# Тестовый запуск LangGraph для проверки формулировщика гипотез

import asyncio
from langgraph.graph import StateGraph, END
from agents.classes import GraphState
from agents.nodes.orchestrator import orchestrator_node
from agents.nodes.formulator import formulator_node
from agents.nodes.critics import _critique_logic as critics_node
from agents.nodes.searcher import node_make_research as searcher_node


def end_node(state: GraphState) -> dict:
    print("--- NODE: End ---")
    return {}


workflow = StateGraph(GraphState)

workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("formulator", formulator_node)
workflow.add_node("critics", critics_node)
workflow.add_node("searcher", searcher_node)
workflow.add_node("end", end_node)

workflow.set_entry_point("orchestrator")
workflow.add_edge("end", END)

app = workflow.compile()

async def main():
    
    inputs = {
        "user_question": "Increasing the speed of LLM token creation",
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
    
    async for event in app.astream_events(inputs, version="v2"):
        event_type = event.get('event', None)
        agent = event.get('name', '')
        if agent in ["_write", "RunnableSequence", "__start__", "__end__", "LangGraph"]:
            continue
        if event_type == 'on_chat_model_stream':
            print(event['data']['chunk'].content, end='')
        elif event_type == 'on_chain_start':
            print(f"<{agent}>")
        elif event_type == 'on_chain_end':
            print(f"</{agent}>")


if __name__ == "__main__":
    asyncio.run(main())
