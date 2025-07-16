import asyncio
import json
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from sse_starlette import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

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

nodes = [
    {"agent": "formulator", "result": "Основная идея: Инференс LLM может быть "
                                      "значительно ускорен путем динамической настройки точности (Quantization "
                                      "bit-width) и Sparsity (обрезка весов/активаций/Attention heads) различных "
                                      "компонентов модели (слои, Attention heads, Feed-forward networks) на основе "
                                      "текущего входного контекста, статистики промежуточных активаций и "
                                      "прогнозируемой вычислительной сложности оставшейся последовательности. Это "
                                      "выходит за рамки статической пост-тренировочной Quantization (такой как AWQ) "
                                      "или фиксированных Sparsity-паттернов, используя присущую избыточность и "
                                      "изменяющуюся плотность информации внутри вычислений LLM во время Runtime."},
    {"agent": "critics", "result": False},
    {"agent": "searcher", "result": 6},
    {"agent": "formulator",
     "result": "Задержка инференса LLM может быть значительно сокращена "
               "путем сочетания многогранулярного параллельного предсказания токенов (расширяющего концепцию Medusa) "
               "с адаптивным, предиктивным механизмом обрезки Key-Value (KV) cache. Вместо простого предсказания "
               "нескольких следующих токенов, модель пытается предсказывать последовательности токенов или "
               "семантические единицы (например, фразы, придаточные предложения) параллельно. Одновременно, "
               "KV cache не просто сжимается (как SnapKV), а динамически обрезается или суммируется на основе "
               "предсказанных будущих паттернов внимания и оценочной релевантности прошлых ключей/значений для "
               "предстоящих вычислений."},
    {"agent": "critics", "result": True},
    {"agent": "end", "result": [
        """Динамическая, контекстно-адаптивная активация подсетей для инференса LLM
Основная идея: Значительно ускорить работу LLM, динамически включая только самые нужные части нейросети (например, конкретные головы внимания или нейроны) для каждого токена, основываясь на текущем контексте. Это более гибкий подход, чем статическая "обрезка" модели или фиксированный выбор "экспертов" (MoE).
Оценка (5/5): Очень сильная и актуальная гипотеза. Она нацелена на решение одной из самых фундаментальных проблем современных LLM — избыточности вычислений. Идея "условных вычислений" (conditional computation) на таком гранулярном уровне — это передний край исследований. Предложенный план проверки очень надежен и включает все необходимые шаги: создание базовой модели, имплементация, оценка скорости и точности, и сравнение с существующими методами.""",
        """Иерархическое семантическое "чанкирование" и адаптивное параллельное декодирование для генерации LLM
Основная идея: Преодолеть "бутылочное горлышко" последовательной генерации токенов. Вместо генерации по одному токену, модель сначала предсказывает общую "смысловую идею" для следующего блока текста ("чанка"), а затем генерирует весь этот блок параллельно. Если модель не уверена в качестве сгенерированного блока, она "откатывается" к безопасной последовательной генерации.
Оценка (4.5/5): Также очень сильная гипотеза, описывающая вариацию на тему спекулятивного декодирования. Это одно из самых горячих направлений в оптимизации инференса. Гипотеза очень хорошо проработана: она предлагает конкретную архитектуру (голова предсказания чанков, параллельный декодер, оценщик уверенности) и четкий план верификации. Она чуть менее "фундаментальна", чем первая, так как является развитием существующей идеи, но ее техническая проработка на очень высоком уровне."""
    ]},
]


async def mock_astream_events(input_data, version="v2") -> AsyncGenerator[dict, None]:
    # Simulate each node emitting a start and end event
    for node in nodes:
        await asyncio.sleep(1)  # simulate async delay
        yield {"event": "on_chain_start", "name": node["agent"]}
        await asyncio.sleep(0.2)
        yield {"event": "on_chat_model_stream", "data": "some llm output"}
        await asyncio.sleep(1)
        yield {"event": "on_chain_end", "name": node["agent"], "result": node["result"]}


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
            yield json.dumps({"type": "agent_end", "agent": agent, "result": event['result']})


@app.get("/generate")
async def generate(req: Request):
    prompt = req.query_params["prompt"]
    return EventSourceResponse(stream(prompt))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
