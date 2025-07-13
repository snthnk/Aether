import asyncio
from langgraph.graph import StateGraph, END
from agents.classes import GraphState, Hypothesis
from agents.nodes.formulator import formulator_node
from agents.nodes.critics import _critique_logic as critics_node
from agents.nodes.searcher import node_make_research as searcher_node
from typing import List
from backend.llm.llms import llm
import time
from backend.agents.constants import MAX_REFINEMENT_CYCLES
import token_count
import re

# --- Узлы и логика маршрутизации ---

def end_node(state: GraphState) -> dict:
    """Финальный узел, который завершает работу и выводит итоговый отчет по гипотезам."""
    print("\n\n" + "=" * 40 + " FINAL REPORT " + "=" * 40)

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

        try:
            # Пытаемся получить content из объекта сообщения, если он есть
            formulation_text = hyp.formulation.content if hasattr(hyp.formulation, 'content') else hyp.formulation
            translated_formulation = llm.invoke(
                f"Translate the following hypothesis formulation into Russian, keeping key technical terms and names in English. Provide only the translation.\n\nText: {formulation_text}"
            ).content
        except Exception as e:
            print(f"[Translation Error: {e}]")
            translated_formulation = hyp.formulation

        print(f"Formulation: {translated_formulation}")

        if not hyp.is_approved and hyp.critique:
            print("\nCritique Summary:")
            critique_text = hyp.critique.content if hasattr(hyp.critique, 'content') else hyp.critique

            # Извлекаем ключевые части из критики для краткого отчета
            summary_match = re.search(r"Executive Summary:(.*?)Strengths:", critique_text, re.DOTALL | re.IGNORECASE)
            recommendations_match = re.search(r"Actionable Recommendations for Refinement:(.*?)Final Verdict:",
                                              critique_text, re.DOTALL | re.IGNORECASE)

            if summary_match:
                summary = summary_match.group(1).strip()
                translated_summary = llm.invoke(
                    f"Translate the following executive summary into Russian, keeping key technical terms and names in English. Provide only the translation.\n\nText: {summary}"
                ).content
                print(f"  - Summary: {translated_summary}")
            if recommendations_match:
                recommendations = recommendations_match.group(1).strip()
                translated_recommendations = llm.invoke(
                    f"Translate the following actionable recommendations into Russian, keeping key technical terms and names in English. Provide only the translation.\n\nText: {recommendations}"
                ).content
                print(f"  - Recommendations: {translated_recommendations}")

    print("\n\n" + "=" * 94)
    return {}


def route_from_formulator(state: GraphState) -> str:
    """Принимает решение после формулировщика: искать информацию или критиковать."""
    print("--- DECISION: After Formulation ---")
    if state.get("current_search_request"):
        print("-> Запрос на поиск обнаружен. Перенаправление в 'searcher'.")
        return "searcher"
    else:
        print("-> Гипотезы сформированы. Перенаправление в 'critics'.")
        return "critics"


def route_from_critics(state: GraphState) -> str:
    """Принимает решение после критики: закончить или вернуться к формулировщику."""
    print("--- DECISION: After Critique ---")
    if not state['hypotheses_and_critics']:
        print("-> Ошибка: нет гипотез для анализа. Завершение работы.")
        return "end"

    # Считаем, сколько уже было полных циклов критики
    num_critique_cycles = len(state['hypotheses_and_critics'])

    latest_hypotheses = state['hypotheses_and_critics'][-1]
    is_any_approved = any(h.is_approved for h in latest_hypotheses)

    print(f"  [i] Цикл доработки: {num_critique_cycles}/{MAX_REFINEMENT_CYCLES}")
    print(f"  [i] Одобренные гипотезы в этом раунде: {'Да' if is_any_approved else 'Нет'}")

    if is_any_approved:
        print(f"-> Найдена одобренная гипотеза. Завершение работы.")
        return "end"

    if num_critique_cycles >= MAX_REFINEMENT_CYCLES:
        print(f"-> Достигнут лимит циклов доработки ({MAX_REFINEMENT_CYCLES}). Завершение работы с тем, что есть.")
        # Даже если ничего не одобрено, мы завершаем работу, чтобы не зацикливаться.
        # В узле end можно добавить логику, чтобы показать лучшие из последних, даже если они не "approved".
        return "end"
    else:
        print("-> Нет одобренных гипотез. Возврат к формулировщику для доработки.")
        return "formulator"


# --- Сборка графа ---

workflow = StateGraph(GraphState)

workflow.add_node("formulator", formulator_node)
workflow.add_node("searcher", searcher_node)
workflow.add_node("critics", critics_node)
workflow.add_node("end", end_node)

# Входная точка - формулировщик
workflow.set_entry_point("formulator")

# Условный переход от формулировщика
workflow.add_conditional_edges(
    "formulator",
    route_from_formulator,
    {
        "searcher": "searcher",
        "critics": "critics",
    }
)

# Поисковик всегда возвращает данные обратно формулировщику
workflow.add_edge("searcher", "formulator")

# Условный переход от критиков
workflow.add_conditional_edges(
    "critics",
    route_from_critics,
    {
        "formulator": "formulator",
        "end": "end"
    }
)

# Конечный узел
workflow.add_edge("end", END)

app = workflow.compile()


# --- Запуск ---

async def main():
    query = input("Введите ваш вопрос: ")
    prompt = f"You have been given a user request. Translate it into English. If it is already in English, simply duplicate the request. Don't write anything else, just the translation.\n\nUser request: {query}"
    translation = llm.invoke(prompt)

    query = str(translation)  # если это object, вытягиваем текст

    inputs = {
        "user_question": query,
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
            print(f"\n<{agent}>")
        elif event_type == 'on_chain_end':
            print(f"</{agent}>")


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(f"Total time: {end - start}")