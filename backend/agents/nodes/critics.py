import asyncio
import re
from backend.llm.llms import llm
from typing import Dict, List, Any, Callable, Awaitable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from backend.agents.prompts import (
    INNOVATOR_PROMPT_TEMPLATE, PRAGMATIST_PROMPT_TEMPLATE, STRATEGIST_PROMPT_TEMPLATE,
    SYNTHESIZER_PROMPT_TEMPLATE, SEARCH_QUERY_GENERATOR_PROMPT)
from backend.agents.classes import GraphState
from backend.agents.nodes.searcher import make_research
from backend.token_count import token_count

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
        search_history=[],
        hypotheses_and_critics=[],
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
        global token_count
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm
        try:
            response = await chain.ainvoke(kwargs)
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                token_count += response.usage_metadata.get('total_tokens', 0)
        except Exception as e:
            print(f"Возникла ошибка во время работы критика {e}")
            await asyncio.sleep(20)
            response = await chain.ainvoke(kwargs)
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                token_count += response.usage_metadata.get('total_tokens', 0)

        return response.content

    async def _run_innovator(self, hypothesis: str, source_materials_text: str) -> str:
        global token_count
        print("-> [Новатор] Запущен.")
        query_gen_prompt = self._SEARCH_QUERY_GENERATOR_PROMPT.format(hypothesis_text=hypothesis)
        try:
            llm_response = await self.llm.ainvoke(query_gen_prompt)
            if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
                token_count += llm_response.usage_metadata.get('total_tokens', 0)
            generated_query = llm_response.content.strip()

        except Exception as e:
            print(f"Возникла ошибка во время работы критика {e}")
            await asyncio.sleep(20)
            llm_response = await self.llm.ainvoke(query_gen_prompt)
            if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
                token_count += llm_response.usage_metadata.get('total_tokens', 0)
            generated_query = llm_response.content.strip()

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
        return critique

    async def _run_pragmatist(self, hypothesis: str) -> str:
        print("-> [Прагматик] Запущен.")
        critique = await self._run_critic("Прагматик", self._PRAGMATIST_PROMPT_TEMPLATE, hypothesis_text=hypothesis)
        print("-> [Прагматик] Отзыв сформирован.")
        return critique

    async def _run_strategist(self, hypothesis: str) -> str:
        print("-> [Стратег] Запущен.")
        critique = await self._run_critic("Стратег", self._STRATEGIST_PROMPT_TEMPLATE, hypothesis_text=hypothesis)
        print("-> [Стратег] Отзыв сформирован.")
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

    if not all_hypotheses_versions:
        print("--- [Critique Panel] Нет версий гипотез для критики. Пропускаю шаг. ---")
        return {}

    latest_hypotheses_list = all_hypotheses_versions[-1]

    search_history = state['search_history']
    source_materials = []
    if search_history:
        # Используем результаты последнего поиска как исходные материалы
        last_search = search_history[-1]
        source_materials = getattr(last_search, 'results', [])

    tasks, hypotheses_to_critique = [], []
    for hyp in latest_hypotheses_list:
        if not hyp.critique:  # Критикуем только новые, еще не оцененные гипотезы
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

        if "promising idea, recommended for research" in final_critique.lower():
            hyp.is_approved = True
            print(f"-> [Critique Panel] Гипотеза ОДОБРЕНА: '{hyp.formulation[:50]}...'")
        else:
            hyp.is_approved = False
            print(f"-> [Critique Panel] Гипотеза ОТКЛОНЕНА: '{hyp.formulation[:50]}...'")

    return {"hypotheses_and_critics": all_hypotheses_versions}
