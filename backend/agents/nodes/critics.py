import asyncio
import os
import re
from llm.llms import llm
from typing import Dict, List, Any, Callable, Awaitable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from agents.prompts import (
    INNOVATOR_PROMPT_TEMPLATE, PRAGMATIST_PROMPT_TEMPLATE, STRATEGIST_PROMPT_TEMPLATE,
    SYNTHESIZER_PROMPT_TEMPLATE, SEARCH_QUERY_GENERATOR_PROMPT)
from agents.classes import Hypothesis
from agents.classes import GraphState
from agents.nodes.searcher import make_research


SearchToolFunc = Callable[[str], Awaitable[List[Dict[str, Any]]]]

def _parse_searcher_report(report_text: str) -> List[Dict[str, str]]:
        if not report_text or "не удалось найти статьи" in report_text:
            return []
        articles_raw = report_text.split("\n---\n")
        parsed_articles = []
        for article_block in articles_raw:
            if "### 📖 Статья:" not in article_block:
                continue
            title_match = re.search(r"### 📖 Статья:\s*(.*)", article_block)
            summary_match = re.search(r"\*\*Резюме:\*\*\n(.*)", article_block, re.DOTALL)
            title = title_match.group(1).strip() if title_match else "Без названия"
            summary = summary_match.group(1).strip() if summary_match else "Резюме отсутствует"
            parsed_articles.append({"title": title, "summary": summary})
        return parsed_articles


async def run_search_agent_as_tool(query: str) -> List[Dict[str, Any]]:

    searcher_initial_state = GraphState(
        user_question=query,
        last_reasoning="",
        search_history=[],
        hypotheses_and_critics=[],
        last_goto="",
        search_system_input="",
        current_search_request=None,
        papers=[],
        summaries=[],
        validated_summaries=[],
        final_report=None,
        error=None,
        search_cycles=0
    )

    report_text, _ = await asyncio.to_thread(
        make_research,
        query,
        searcher_initial_state
    )

    print("--- [TOOL: Search Agent] Агент-поисковик завершил работу. Парсинг отчета... ---")
    structured_results = _parse_searcher_report(report_text)
    print(f"--- [TOOL: Search Agent] Отчет успешно распарсен. Найдено статей: {len(structured_results)}. ---")
    return structured_results


class CritiquePanel:
        _SEARCH_QUERY_GENERATOR_PROMPT = SEARCH_QUERY_GENERATOR_PROMPT
        _INNOVATOR_PROMPT_TEMPLATE = INNOVATOR_PROMPT_TEMPLATE
        _PRAGMATIST_PROMPT_TEMPLATE = PRAGMATIST_PROMPT_TEMPLATE
        _STRATEGIST_PROMPT_TEMPLATE = STRATEGIST_PROMPT_TEMPLATE
        _SYNTHESIZER_PROMPT_TEMPLATE = SYNTHESIZER_PROMPT_TEMPLATE

        def __init__(self, llm: BaseChatModel, search_tool: SearchToolFunc):
            self.llm = llm
            self.search_tool = search_tool

        async def _run_critic(self, critic_name: str, prompt_template: str, **kwargs) -> str:
            prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = prompt | self.llm
            response = await chain.ainvoke(kwargs)
            return response.content

        async def _run_innovator(self, hypothesis: str, source_materials_text: str) -> str:
            print("-> [Новатор] Запущен.")
            query_gen_prompt = self._SEARCH_QUERY_GENERATOR_PROMPT.format(hypothesis_text=hypothesis)
            generated_query = (await self.llm.ainvoke(query_gen_prompt)).content.strip()

            search_results_list = await self.search_tool(generated_query)

            search_results_text = "\n\n".join([f"- {res['title']}:\n  {res.get('summary', 'N/A')}" for res in
                                               search_results_list]) if search_results_list else "Внешний поиск не дал релевантных результатов."

            critique = await self._run_critic(
                "Новатор",
                self._INNOVATOR_PROMPT_TEMPLATE,
                hypothesis_text=hypothesis,
                source_materials=source_materials_text,
                search_results=search_results_text
            )

            print("-> [Новатор] Отзыв сформирован.")
            asyncio.sleep(4)
            return critique

        async def _run_pragmatist(self, hypothesis: str) -> str:
            print("-> [Прагматик] Запущен.")
            critique = await self._run_critic("Прагматик", self._PRAGMATIST_PROMPT_TEMPLATE, hypothesis_text=hypothesis)
            print("-> [Прагматик] Отзыв сформирован.")
            asyncio.sleep(4)
            return critique

        async def _run_strategist(self, hypothesis: str) -> str:
            print("-> [Стратег] Запущен.")
            critique = await self._run_critic("Стратег", self._STRATEGIST_PROMPT_TEMPLATE, hypothesis_text=hypothesis)
            print("-> [Стратег] Отзыв сформирован.")
            asyncio.sleep(4)
            return critique

        async def run_full_analysis(self, hypothesis: str, source_materials: List[Dict[str, Any]]) -> Dict[str, str]:
            print(f"\n===== НАЧАЛО АНАЛИЗА ГИПОТЕЗЫ =====\nГипотеза: \"{hypothesis[:100]}...\"")
            source_materials_text = "\n\n".join([f"- {s['title']}:\n  {s.get('summary', 'N/A')}" for s in
                                                 source_materials]) if source_materials else "Исходные материалы не предоставлены."
            innovator_task = self._run_innovator(hypothesis, source_materials_text)
            pragmatist_task = self._run_pragmatist(hypothesis)
            strategist_task = self._run_strategist(hypothesis)
            innovator_result, pragmatist_result, strategist_result = await asyncio.gather(
                innovator_task, pragmatist_task, strategist_task
            )
            print("-> [Синтезатор] Запущен.")
            final_synthesis = await self._run_critic(
                "Синтезатор", self._SYNTHESIZER_PROMPT_TEMPLATE,
                hypothesis_text=hypothesis, innovator_critique=innovator_result,
                pragmatist_critique=pragmatist_result, strategist_critique=strategist_result
            )
            print("-> [Синтезатор] Итоговое заключение готово.")
            print("===== АНАЛИЗ ГИПОТЕЗЫ ЗАВЕРШЕН =====\n")
            return {
                "innovator": innovator_result, "pragmatist": pragmatist_result,
                "strategist": strategist_result, "final": final_synthesis
            }


async def _critique_logic(state: GraphState) -> dict:
        print("--- NODE: Critique Panel ---")

        panel = CritiquePanel(llm=llm, search_tool=run_search_agent_as_tool)

        all_hypotheses_versions = state['hypotheses_and_critics']
        print(len(all_hypotheses_versions))

        if not all_hypotheses_versions:
            print("--- [Critique Panel] Нет версий гипотез для критики. Пропускаю шаг. ---")
            return {}

        latest_hypotheses_list = all_hypotheses_versions[-1]

        search_history = state['search_history']
        source_materials = []
        if search_history:
            last_search = search_history[-1]
            source_materials = getattr(last_search, 'results', [])

        tasks, hypotheses_to_critique = [], []
        for hyp in latest_hypotheses_list:
            if not hyp.critique:
                tasks.append(panel.run_full_analysis(hyp.formulation, source_materials))
                hypotheses_to_critique.append(hyp)

        if not tasks:
            print("--- [Critique Panel] В последней версии нет новых гипотез для критики. Пропускаю шаг. ---")
            return {}

        print(f"--- [Critique Panel] Отправляю {len(tasks)} гипотез(ы) на анализ... ---")
        critique_results = await asyncio.gather(*tasks)

        for hyp, critique_dict in zip(hypotheses_to_critique, critique_results):
            final_critique = critique_dict.get('final', 'Ошибка: не удалось сгенерировать итоговую критику.')
            hyp.critique = final_critique
            print(f"-> [Critique Panel] Добавлен отзыв для гипотезы: '{hyp.formulation[:50]}...'")

        state['hypotheses_and_critics'] = all_hypotheses_versions
        return {"hypotheses_and_critics": all_hypotheses_versions}


def critique_node(state: GraphState) -> dict:
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        return asyncio.run(_critique_logic(state))


if __name__ == '__main__':
        from backend.agents.classes import SearchRequest

        print("--- [TEST RUN] Запускаю автономную проверку узла критики... ---")

        # 1. Создаем тестовые гипотезы, имитируя структуру List[List[...]]
        # Первая версия, уже полностью проанализированная
        version_1 = [
            Hypothesis(
                formulation="Старая гипотеза, которая уже проверена.",
                critique="Это уже было сделано в 2020 году.",
                is_approved=False
            )
        ]
        # Вторая, актуальная версия. Здесь есть над чем поработать.
        version_2 = [
            Hypothesis(
                formulation="RL-агент, вознаграждаемый за создание состояний среды, из которых сложно вернуться в исходное, будет исследовать мир эффективнее, чем агент, управляемый только любопытством.",
                critique="",  # <-- Критики нет, нужно сделать
                is_approved=False
            ),
            Hypothesis(
                formulation="Эта гипотеза уже имеет критику и ее трогать не надо.",
                critique="Краткий отзыв.",  # <-- Критика есть, игнорируем
                is_approved=False
            )
        ]

        # 2. Создаем тестовую историю поиска
        test_search_request = SearchRequest(
            input_query="RL agent exploration",
            search_queries=["RL irreversible states"],
            results=[{"title": "Empowerment - An Introduction", "summary": "Обсуждается концепция empowerment."}]
        )

        # 3. Собираем начальное состояние, СООТВЕТСТВУЮЩЕЕ ТРЕБОВАНИЯМ
        test_state = GraphState(
            user_question="RL agents for exploration",
            last_reasoning="Formulator created a new version of hypotheses.",
            # Вкладываем нашу структуру "список списков"
            hypotheses_and_critics=[version_1, version_2],
            search_history=[test_search_request],
            last_goto="critique"
        )

        print("\n--- [TEST RUN] НАЧАЛЬНОЕ СОСТОЯНИЕ (ПОСЛЕДНЯЯ ВЕРСИЯ): ---")
        for hyp in test_state['hypotheses_and_critics'][-1]:
            print(f"-> {hyp.formulation[:30]}... | Критика: '{hyp.critique}'")

        # 4. Запускаем узел критики
        print("\n--- [TEST RUN] >>> ЗАПУСК critique_node() <<< ---")
        final_update = critique_node(test_state)
        print("--- [TEST RUN] >>> ЗАВЕРШЕНИЕ critique_node() <<< ---\n")

        # 5. Выводим результат
        updated_versions = final_update.get('hypotheses_and_critics', [])
        print("\n--- [TEST RUN] ИТОГОВОЕ СОСТОЯНИЕ (ПОСЛЕДНЯЯ ВЕРСИЯ): ---")
        if updated_versions:
            for hyp in updated_versions[-1]:
                print(f"-> {hyp.formulation[:30]}... | Критика: '{hyp.critique}'")
        else:
            print("Ошибка: узел не вернул обновленные данные.")

        query = 'Rl agents'
        hyp = Hypothesis(
                formulation="RL-агент, вознаграждаемый за создание состояний среды, из которых сложно вернуться в исходное, будет исследовать мир эффективнее, чем агент, управляемый только любопытством.",
                critique="",
                is_approved=False
            )

        inputs = GraphState(
                user_question=query,
                last_reasoning="",
                last_goto="",
                current_search_request=None,
                hypotheses_and_critics=[]
            )

        inputs.hypotheses_and_critics.append([hyp])
