import asyncio
from langgraph.graph import StateGraph, END
from agents.classes import GraphState, Hypothesis
from agents.nodes.formulator import formulator_node
from agents.nodes.critics import _critique_logic as critics_node
from agents.nodes.searcher import node_make_research as searcher_node
from typing import List
from backend.llm.llms import llm


# --- Узлы и логика маршрутизации ---

def end_node(state: GraphState) -> dict:
    """Финальный узел, который завершает работу и выводит результат."""
    print("\n--- NODE: End ---")
    final_hypotheses: List[Hypothesis] = []
    if state.get('hypotheses_and_critics'):
        # Собираем все одобренные гипотезы из последней итерации
        latest_hypotheses = state['hypotheses_and_critics'][-1]
        final_hypotheses = [h for h in latest_hypotheses if h.is_approved]

    if final_hypotheses:
        print("\n✅ Итоговые перспективные гипотезы:")
        for i, hyp in enumerate(final_hypotheses):
            answer = hyp.formulation
            translated_answer = llm.invoke(f"Translate the following text into Russian while keeping the key terms and names in English. Don't write anything else, just the translation."
                                           f"Here is the text: {answer}")
            print(f"\n--- Гипотеза #{i + 1} ---")
            print(f"Формулировка: {translated_answer}")
            print("\nКритика:")
            print(hyp.critique)
    else:
        print("\n❌ Не удалось выработать перспективную гипотезу после всех итераций.")

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

    latest_hypotheses = state['hypotheses_and_critics'][-1]
    # Проверяем, была ли хоть одна гипотеза одобрена критиками
    is_any_approved = any(h.is_approved for h in latest_hypotheses)

    if is_any_approved:
        print(f"-> Найдена одобренная гипотеза. Завершение работы.")
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

    query = llm.invoke(f"You have been given a user request. Translate it into English. If it is already in English, simply duplicate the request. Don't write anything else, just the translation."
               f"\n\nUser request: {query}")

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
            print(event['data']['chunk'].content)
        elif event_type == 'on_chain_start':
            print(f"\n<{agent}>")
        elif event_type == 'on_chain_end':
            print(f"</{agent}>")


if __name__ == "__main__":
    asyncio.run(main())
