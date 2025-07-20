## MODIFIED ##

import asyncio
import requests
from backend.llm.llms import llm
from typing import Dict, List, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from backend.agents.prompts import (
    INNOVATOR_PROMPT_TEMPLATE, PRAGMATIST_PROMPT_TEMPLATE, STRATEGIST_PROMPT_TEMPLATE,
    NITPICKER_PROMPT_TEMPLATE, SYNTHESIZER_PROMPT_TEMPLATE, SURGICAL_SEARCH_SELECTOR_PROMPT)
from backend.agents.classes import GraphState
from backend.agents.constants import SURGICAL_SEARCH_FETCH_COUNT, SURGICAL_SEARCH_SELECT_COUNT, \
    HUMAN_IN_THE_LOOP_ENABLED
from backend.websocket_manager import manager


# --- Pydantic models for structured output ---
class SurgicalSelectionOutput(BaseModel):
    selected_ids: List[str] = Field(description="A list of paper IDs that are most relevant to the hypothesis.")


class CritiquePanel:
    # Store prompts as class attributes
    _INNOVATOR_PROMPT_TEMPLATE = INNOVATOR_PROMPT_TEMPLATE
    _PRAGMATIST_PROMPT_TEMPLATE = PRAGMATIST_PROMPT_TEMPLATE
    _STRATEGIST_PROMPT_TEMPLATE = STRATEGIST_PROMPT_TEMPLATE
    _NITPICKER_PROMPT_TEMPLATE = NITPICKER_PROMPT_TEMPLATE
    _SYNTHESIZER_PROMPT_TEMPLATE = SYNTHESIZER_PROMPT_TEMPLATE
    _SURGICAL_SEARCH_SELECTOR_PROMPT = SURGICAL_SEARCH_SELECTOR_PROMPT

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def _run_critic(self, critic_name: str, prompt_template: str, **kwargs) -> str:
        """Helper to run a single critic's LLM chain."""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm
        try:
            await asyncio.sleep(2.5)
            response = await chain.ainvoke(kwargs)
            return response.content
        except Exception as e:
            # MODIFIED: More informative error logging
            print(f"\n--- ERROR in {critic_name} Critic ---\n{e}\n--------------------")
            await asyncio.sleep(20)  # Wait before retry
            try:
                response = await chain.ainvoke(kwargs)
                return response.content
            except Exception as e2:
                print(f"\n--- RETRY FAILED in {critic_name} Critic ---\n{e2}\n--------------------")
                return f"Error: Could not get a response from the {critic_name} critic."

    async def _run_surgical_search(self, hypothesis: str) -> List[Dict[str, str]]:
        """
        Performs a focused, multi-step search to find prior art for a hypothesis.
        """
        # This part of the logic remains unchanged, as it was working well.
        print("    -> [Surgical Search] Starting process...")
        query_gen_prompt = "Analyze the following hypothesis and formulate an ideal, concise search query (3-5 keywords in English) to find articles that could disprove its novelty. Do not add any explanations, only provide the query itself.\n\nHypothesis: {hypothesis_text}"
        query_chain = ChatPromptTemplate.from_template(query_gen_prompt) | self.llm
        try:
            query_response = await query_chain.ainvoke({"hypothesis_text": hypothesis})
            query = query_response.content.strip()
            print(f"    -> [Surgical Search] Generated query: '{query}'")
        except Exception as e:
            print(f"    -> [Surgical Search] Failed to generate query: {e}. Aborting search.")
            return []

        print(f"    -> [Surgical Search] Fetching {SURGICAL_SEARCH_FETCH_COUNT} papers from OpenAlex...")
        url = "https://api.openalex.org/works"
        params = {
            'search': query, 'mailto': "senya.novozhilov@gmail.com",
            'per_page': SURGICAL_SEARCH_FETCH_COUNT, 'filter': 'has_abstract:true,language:en'
        }
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                print("    -> [Surgical Search] OpenAlex returned no results.")
                return []
        except requests.RequestException as e:
            print(f"    -> [Surgical Search] OpenAlex API error: {e}")
            return []

        candidate_papers = {}
        for i, paper in enumerate(results):
            paper_id = f"p{i + 1}"
            abstract = paper.get('abstract', 'No abstract available.')
            if isinstance(abstract, dict):
                abstract_text = ' '.join(
                    ' '.join(abstract['index'][key]) for key in sorted(abstract['index'].keys(), key=int)
                )
            else:
                abstract_text = str(abstract)
            candidate_papers[paper_id] = {"title": paper.get('title', 'No title'), "summary": abstract_text}

        candidate_papers_text = "\n\n".join(
            f"ID: {pid}\nTitle: {pdata['title']}\nAbstract: {pdata['summary'][:500]}..."
            for pid, pdata in candidate_papers.items()
        )

        print(f"    -> [Surgical Search] Using LLM to select top {SURGICAL_SEARCH_SELECT_COUNT} papers...")
        parser = PydanticOutputParser(pydantic_object=SurgicalSelectionOutput)
        selector_prompt = ChatPromptTemplate.from_template(self._SURGICAL_SEARCH_SELECTOR_PROMPT).partial(
            format_instructions=parser.get_format_instructions()
        )
        selector_chain = selector_prompt | self.llm | parser
        try:
            selection_result = await selector_chain.ainvoke({
                "hypothesis_text": hypothesis, "candidate_papers_text": candidate_papers_text,
                "select_count": SURGICAL_SEARCH_SELECT_COUNT
            })
            selected_ids = selection_result.selected_ids
            print(f"    -> [Surgical Search] LLM selected IDs: {selected_ids}")
        except Exception as e:
            print(f"    -> [Surgical Search] Failed to parse selection from LLM: {e}. Returning top papers by default.")
            selected_ids = list(candidate_papers.keys())[:SURGICAL_SEARCH_SELECT_COUNT]

        final_results = [candidate_papers[pid] for pid in selected_ids if pid in candidate_papers]
        print(f"    -> [Surgical Search] Process complete. Returning {len(final_results)} papers.")
        return final_results

    async def _run_innovator(self, hypothesis: str, source_materials_text: str) -> str:
        """Runs the Innovator critic, including its specialized search."""
        search_results_list = await self._run_surgical_search(hypothesis)
        search_results_text = "\n\n".join(
            f"- {res['title']}:\n  {res.get('summary', 'N/A')}"
            for res in search_results_list
        ) if search_results_list else "Внешний поиск не дал релевантных результатов."
        return await self._run_critic(
            "Innovator", self._INNOVATOR_PROMPT_TEMPLATE, hypothesis_text=hypothesis,
            source_materials=source_materials_text, search_results=search_results_text
        )

    async def _run_pragmatist(self, hypothesis: str) -> str:
        return await self._run_critic("Pragmatist", self._PRAGMATIST_PROMPT_TEMPLATE, hypothesis_text=hypothesis)

    async def _run_strategist(self, hypothesis: str) -> str:
        return await self._run_critic("Strategist", self._STRATEGIST_PROMPT_TEMPLATE, hypothesis_text=hypothesis)

    async def _run_nitpicker(self, hypothesis: str) -> str:
        return await self._run_critic("Nitpicker", self._NITPICKER_PROMPT_TEMPLATE, hypothesis_text=hypothesis)

    async def run_full_analysis(self, hypothesis_index: int, hypothesis: str, source_materials: List[Dict[str, Any]]) -> \
            Dict[str, str]:
        """Runs the entire panel of critics for a single hypothesis."""
        print(f"\n===== [HYPOTHESIS #{hypothesis_index + 1}] STARTING ANALYSIS =====\n\"{hypothesis[:100]}...\"")
        source_materials_text = "\n\n".join(
            f"- {s['title']}:\n  {s.get('summary', 'N/A')}"
            for s in source_materials
        ) if source_materials else "Исходные материалы не предоставлены."

        # Create concurrent tasks for all critics
        tasks = {
            "Innovator": self._run_innovator(hypothesis, source_materials_text),
            "Pragmatist": self._run_pragmatist(hypothesis),
            "Strategist": self._run_strategist(hypothesis),
            "Nitpicker": self._run_nitpicker(hypothesis)
        }

        results = await asyncio.gather(*tasks.values())
        critique_results = dict(zip(tasks.keys(), results))

        # MODIFIED: Structured logging to prevent interleaved output
        print(f"\n--- [HYPOTHESIS #{hypothesis_index + 1}] CRITIQUE RESULTS ---")
        for critic, result in critique_results.items():
            print(f"\n--- {critic}'s Verdict ---")
            print(result)
            print("-" * (len(critic) + 18))

        print(f"--- [HYPOTHESIS #{hypothesis_index + 1}] Running Synthesizer ---")
        final_synthesis = await self._run_critic(
            "Synthesizer", self._SYNTHESIZER_PROMPT_TEMPLATE,
            hypothesis_text=hypothesis,
            innovator_critique=critique_results["Innovator"],
            pragmatist_critique=critique_results["Pragmatist"],
            strategist_critique=critique_results["Strategist"],
            nitpicker_critique=critique_results["Nitpicker"]  # MODIFIED: Pass Nitpicker critique
        )
        print(f"--- [HYPOTHESIS #{hypothesis_index + 1}] Synthesizer Finished ---")
        print("===== ANALYSIS COMPLETE =====\n")

        critique_results["final"] = final_synthesis
        return critique_results


async def _critique_logic(state: GraphState) -> dict:
    print("\n--- NODE: Critique Panel ---")
    panel = CritiquePanel(llm=llm)
    all_hypotheses_versions = state['hypotheses_and_critics']

    if not all_hypotheses_versions:
        print("--- [Critique Panel] No hypotheses to critique. Skipping. ---")
        return {}

    latest_hypotheses_list = all_hypotheses_versions[-1]
    search_history = state['search_history']
    source_materials = search_history[-1].results if search_history else []

    tasks, hypotheses_to_critique = [], []
    for i, hyp in enumerate(latest_hypotheses_list):
        if not hyp.critique:  # Only critique new hypotheses
            # MODIFIED: Pass index for better logging
            tasks.append(panel.run_full_analysis(i, hyp.formulation, source_materials))
            hypotheses_to_critique.append(hyp)

    if not tasks:
        print("--- [Critique Panel] No new hypotheses to critique in this version. Skipping. ---")
        return {}

    print(f"--- [Critique Panel] Sending {len(tasks)} hypothesis/hypotheses for analysis... ---")
    critique_results = await asyncio.gather(*tasks)

    for hyp, critique_dict in zip(hypotheses_to_critique, critique_results):
        final_critique = critique_dict.get('final', 'Error: Could not generate final critique.')
        hyp.critique = final_critique

        if "promising idea, recommended for research" in final_critique.lower():
            hyp.is_approved = True
            print(f"-> [Critique Panel Verdict] Hypothesis APPROVED: '{hyp.formulation[:50]}...'")
        else:
            hyp.is_approved = False
            print(f"-> [Critique Panel Verdict] Hypothesis REJECTED: '{hyp.formulation[:50]}...'")

    # --- NEW: HUMAN-IN-THE-LOOP FEEDBACK STAGE ---
    if HUMAN_IN_THE_LOOP_ENABLED and hypotheses_to_critique:
        print("\n\n" + "=" * 40 + " HUMAN-IN-THE-LOOP FEEDBACK " + "=" * 40)
        print("Вы можете добавить свои комментарии к каждой гипотезе.")
        print("Ваши комментарии будут иметь НАИВЫСШИЙ приоритет для следующего шага доработки.")

        for i, hyp in enumerate(latest_hypotheses_list):
            print("\n" + "-" * 35 + f" Гипотеза #{i + 1} " + "-" * 35)

            # Показываем формулировку и уже сгенерированную критику
            formulation_text = hyp.formulation.content if hasattr(hyp.formulation, 'content') else hyp.formulation
            critique_text = hyp.critique.content if hasattr(hyp.critique, 'content') else hyp.critique

            print(f"\n[Формулировка]:\n{formulation_text}")
            print(f"\n[Сводная критика от ИИ]:\n{critique_text}")

            websocket = manager.get_ws(state['client_id'])
            await websocket.send_json({
                "type": "critics_approval",
                "hyp_index": i,
                "formulation": formulation_text,
                "critique": critique_text
            })

            # Запрашиваем комментарий пользователя
            # user_comment = input(
            #     f"\n> Ваш комментарий для гипотезы #{i + 1} (нажмите Enter, чтобы пропустить): ").strip()

            user_comment = await websocket.receive_text()

            if user_comment:
                # Добавляем комментарий пользователя в специальном формате, который поймет Формулятор
                user_feedback_block = f"\n\n<USER_COMMENT>\n{user_comment}\n</USER_COMMENT>"
                hyp.critique += user_feedback_block
                print("  [+] Ваш комментарий добавлен.")
        print("\n" + "=" * 96)

    return {"hypotheses_and_critics": all_hypotheses_versions}