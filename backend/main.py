import asyncio
import json
from pathlib import Path
from pprint import pprint
from uuid import uuid4

import aiofiles
import uvicorn
from fastapi import FastAPI, WebSocket, Request, UploadFile, HTTPException, File, WebSocketDisconnect
from starlette.websockets import WebSocketState
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

from backend.agents.classes import GraphState, Hypothesis, SearchRequest
from backend.agents.nodes.formulator import formulator_node
from backend.agents.nodes.critics import _critique_logic as critics_node
from backend.agents.nodes.searcher import node_make_research as searcher_node
from backend.llm.llms import llm
from backend.agents.constants import MAX_REFINEMENT_CYCLES
from backend.agents.prompts import REFINE_SEARCH_PROMPT
from langchain_core.prompts import ChatPromptTemplate
import re

from backend.websocket_manager import manager


# --- Вспомогательная функция для форматирования критики ---
def format_rejected_hypotheses(hypotheses_and_critics: list[list[Hypothesis]]) -> str:
    """Форматирует только отвергнутые гипотезы и их критику для нового промпта."""
    if not hypotheses_and_critics:
        return "No rejected hypotheses yet."

    last_version = hypotheses_and_critics[-1]
    rejected_info = []

    for hyp in last_version:
        if not hyp.is_approved:
            critique_summary = "No specific critique available."
            if hyp.critique:
                # Извлекаем краткое содержание из критики для лаконичности
                summary_match = re.search(r"Executive Summary:(.*?)\n", hyp.critique, re.DOTALL | re.IGNORECASE)
                weakness_match = re.search(r"Critical Weaknesses:(.*?)\n", hyp.critique, re.DOTALL | re.IGNORECASE)
                if summary_match:
                    critique_summary = summary_match.group(1).strip()
                elif weakness_match:
                    critique_summary = weakness_match.group(1).strip()

            rejected_info.append(
                f"- Hypothesis: {hyp.formulation}\n  Critique Summary: {critique_summary}"
            )

    if not rejected_info:
        return "No hypotheses were rejected in the last round."

    return "\n".join(rejected_info)


# --- Узлы ---

def prepare_search_node(state: GraphState) -> dict:
    """
    Готовит ввод для узла-поисковика.
    Используется ТОЛЬКО для первого, самого первого запуска.
    """
    print("\n--- NODE: Prepare Initial Search ---")
    query = state['user_question']
    print(f"-> Preparing initial broad search for query: '{query}'")
    return {
        "current_search_request": SearchRequest(input_query=query),
        "search_cycles": 0,
    }


def refine_search_query_node(state: GraphState) -> dict:
    """
    Анализирует критику и генерирует новый, более точный поисковый запрос.
    """
    print("\n--- NODE: Refine Search Query Based on Critique ---")

    rejected_hypotheses_text = format_rejected_hypotheses(state['hypotheses_and_critics'])

    prompt = ChatPromptTemplate.from_template(REFINE_SEARCH_PROMPT)
    chain = prompt | llm

    llm_response = chain.invoke({
        "user_question": state['user_question'],
        "rejected_hypotheses_and_critics": rejected_hypotheses_text
    })

    new_query = llm_response.content.strip()
    print(f"-> Generated a new, refined search query: '{new_query}'")

    return {
        "current_search_request": SearchRequest(input_query=new_query),
        # Сбрасываем счетчик циклов поиска внутри sub-графа searcher'а
        "search_cycles": 0,
    }


def end_node(state: GraphState) -> dict:
    """Финальный узел, который завершает работу и выводит итоговый отчет по гипотезам."""
    print("\n\n" + "=" * 40 + " FINAL REPORT " + "=" * 40)

    # --- START: LOGIC TO MAP CITATIONS TO PAPERS ---
    # 1. Создаем словарь для быстрого поиска статей по тегу цитирования
    all_papers_by_tag = {}
    search_history = state.get('search_history', [])
    for search in search_history:
        # 2. Воссоздаем тег цитирования точно так же, как в format_search_history
        # ИСПРАВЛЕНИЕ: Используем search.results вместо search.get('results', [])
        for paper in search.results:
            authors_list = paper.get('authors', 'Unknown Author').split(',')
            first_author = authors_list[0].strip().split()[-1] if authors_list[0].strip() else "N/A"
            source_link = paper.get('source', '')
            year = 'N/A'
            if source_link and 'arxiv' in source_link:
                match = re.search(r'/abs/(\d{2})', source_link)
                if match:
                    year = f"20{match.group(1)}"

            citation_tag = f"[{first_author} et al., {year}]"
            all_papers_by_tag[citation_tag] = paper  # Сохраняем всю информацию о статье
    # --- END: LOGIC ---

    hypotheses_and_critics = state.get('hypotheses_and_critics')
    if not hypotheses_and_critics:
        print("\n❌ No hypotheses were generated during the process.")
        print("=" * 94)
        return {}

    final_hypotheses_version = hypotheses_and_critics[-1]

    print(f"\nSummary of the final iteration (Version {len(hypotheses_and_critics)}):")
    print("-" * 30)

    for i, hyp in enumerate(final_hypotheses_version):
        status = "✅ Approved" if hyp.is_approved else "❌ Rejected"
        print(f"\n--- Hypothesis #{i + 1}: {status} ---")

        formulation_text = hyp.formulation.content if hasattr(hyp.formulation, 'content') else hyp.formulation
        try:
            translated_formulation = llm.invoke(
                f"Translate the following hypothesis formulation into Russian, keeping key technical terms and names in English. Provide only the translation.\n\nText: {formulation_text}"
            ).content
        except Exception as e:
            print(f"[Translation Error: {e}]")
            translated_formulation = formulation_text

        print(f"Formulation: {translated_formulation}")

        # --- START: LOGIC TO PRINT CITED SOURCES ---
        # 3. Находим все теги цитирования в тексте формулировки гипотезы
        cited_tags = re.findall(r'(\[.*?et al\.,.*?\])', formulation_text)
        if cited_tags:
            print("\nCited Sources:")
            unique_tags = sorted(list(set(cited_tags)))  # Удаляем дубликаты
            for tag in unique_tags:
                paper_data = all_papers_by_tag.get(tag)
                if paper_data:
                    title = paper_data.get('title', 'Unknown Title')
                    link = paper_data.get('source', '#')
                    print(f"  - {tag}: {title}\n    Link: {link}")
                else:
                    print(f"  - {tag}: (Source information not found in history)")
        # --- END: LOGIC ---

        if hyp.critique:
            print("\nCritique Summary:")
            critique_text = hyp.critique.content if hasattr(hyp.critique, 'content') else hyp.critique

            summary_match = re.search(r"General Summary:(.*?)Key Strengths:", critique_text, re.DOTALL | re.IGNORECASE)
            recommendations_match = re.search(r"Recommendations for Implementation:(.*?)Final Verdict:",
                                              critique_text, re.DOTALL | re.IGNORECASE)

            # Fallback to older format if new one fails
            if not summary_match:
                summary_match = re.search(r"Executive Summary:(.*?)Strengths:", critique_text,
                                          re.DOTALL | re.IGNORECASE)

            if summary_match:
                summary = summary_match.group(1).strip()
                try:
                    translated_summary = llm.invoke(
                        f"Translate the following executive summary into Russian, keeping key technical terms and names in English. Provide only the translation.\n\nText: {summary}"
                    ).content
                    print(f"  - Summary: {translated_summary}")
                except Exception:
                    print(f"  - Summary: {summary}")

            if recommendations_match:
                recommendations = recommendations_match.group(1).strip()
                try:
                    translated_recommendations = llm.invoke(
                        f"Translate the following actionable recommendations into Russian, keeping key technical terms and names in English. Provide only the translation.\n\nText: {recommendations}"
                    ).content
                    print(f"  - Recommendations: {translated_recommendations}")
                except Exception:
                    print(f"  - Recommendations: {recommendations}")

    print("\n\n" + "=" * 94)
    return {}


# --- Логика маршрутизации ---

def should_continue(state: GraphState) -> str:
    """
    Определяет, продолжать ли цикл доработки или завершить процесс.
    """
    print("--- DECISION: After Critique ---")
    if not state['hypotheses_and_critics']:
        print("-> Error: No hypotheses to analyze. Ending.")
        return "end"

    num_critique_cycles = len(state['hypotheses_and_critics'])
    latest_hypotheses = state['hypotheses_and_critics'][-1]
    is_all_approved = all(h.is_approved for h in latest_hypotheses)

    print(f"  [i] Refinement cycle: {num_critique_cycles}/{MAX_REFINEMENT_CYCLES}")
    if is_all_approved:
        print("-> All hypotheses approved. Ending process.")
        return "end"

    if num_critique_cycles >= MAX_REFINEMENT_CYCLES:
        print(f"-> Refinement cycle limit reached ({MAX_REFINEMENT_CYCLES}). Ending with the current results.")
        return "end"
    else:
        print("-> Not all hypotheses are approved. Generating a refined search query based on critique.")
        return "refine_and_search"


# --- Сборка графа ---
workflow = StateGraph(GraphState)

# Добавляем все узлы, включая новый
workflow.add_node("prepare_search", prepare_search_node)
workflow.add_node("refine_search_query", refine_search_query_node)
workflow.add_node("searcher", searcher_node)
workflow.add_node("formulator", formulator_node)
workflow.add_node("critics", critics_node)
workflow.add_node("end", end_node)

# Входная точка - начальный поиск
workflow.set_entry_point("prepare_search")

# Основная последовательность
workflow.add_edge("prepare_search", "searcher")
workflow.add_edge("searcher", "formulator")
workflow.add_edge("formulator", "critics")

# Новый край от уточняющего узла обратно к поисковику
workflow.add_edge("refine_search_query", "searcher")

# Условные переходы после критики
workflow.add_conditional_edges(
    "critics",
    should_continue,
    {
        "refine_and_search": "refine_search_query",
        "end": "end"
    }
)

workflow.add_edge("end", END)

app = workflow.compile()


class PydanticEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)


# --- Запуск ---

async def main(query, websocket: WebSocket, client_id: str):
    prompt = f"You have been given a user request. Translate it into English. If it is already in English, simply duplicate the request. Don't write anything else, just the translation.\n\nUser request: {query}"
    translation = llm.invoke(prompt)

    user_question = str(translation.content).strip()

    inputs = {
        "user_question": user_question,
        "client_id": client_id,
        "search_history": [],
        "hypotheses_and_critics": [],
        "papers": [],
        "summaries": [],
        "validated_summaries": [],
        "search_cycles": 0
    }

    try:
        async for event in app.astream_events(inputs, version="v2"):
            # Early exit if WebSocket disconnected
            if websocket.client_state != WebSocketState.CONNECTED:
                print("WebSocket disconnected, stopping stream")
                break

            event_type = event.get('event', None)
            agent = event.get('name', '')
            if agent in ["_write", "RunnableSequence", "__start__", "__end__", "LangGraph"]:
                continue
            if event_type == 'on_chat_model_stream':
                print(event['data']['chunk'].content, end='')
            elif event_type == 'on_chain_start':
                await websocket.send_json(
                    {'type': 'agent_start', 'id': event['run_id'], 'parent_ids': event['parent_ids'], 'agent': agent})
                print(f"\n<{agent} {event['run_id']}>\n")
                await asyncio.sleep(0.2)
            elif event_type == 'on_chain_end':
                pprint(event)
                await websocket.send_text(json.dumps(
                    {'type': 'agent_end', 'agent': agent, 'id': event['run_id'], 'parent_ids': event['parent_ids'],
                     'result': event['data']}, cls=PydanticEncoder))
                print(f"\n</{agent} {event['run_id']}>")
                await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        print("WebSocket disconnected during streaming")
    except Exception as e:
        print(f"Error during streaming: {e}")


fastapi = FastAPI()

fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@fastapi.websocket("/generate")
async def generate(websocket: WebSocket):
    client_id = uuid4().hex
    await manager.connect(websocket, client_id)
    try:
        data = await websocket.receive_json()
        await main(data["prompt"], websocket, client_id)
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print(f"{' closing ':=^75}")
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close()
            except Exception as e:
                print(f"Error closing WebSocket: {e}")


@fastapi.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")

        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="File type not allowed")

        max_size = 100 * 1024 * 1024
        contents = await file.read()
        if len(contents) > max_size:
            raise HTTPException(status_code=400, detail="File too large")

        await file.seek(0)

        unique_filename = f"{uuid4()}"

        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        file_path = upload_dir / f"{unique_filename}.pdf"
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(contents)

        return {
            "uuid": unique_filename,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        await file.close()


if __name__ == "__main__":
    uvicorn.run(fastapi, host="0.0.0.0", port=8000)
