from backend.llm.llms import llm
from backend.agents.prompts import FORMULATOR_INITIAL_PROMPT
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.output_parsers import PydanticOutputParser
from backend.agents.classes import Hypothesis, GraphState, format_hypotheses_and_critics, format_search_history
from langchain_core.prompts import ChatPromptTemplate
from ..classes import SearchRequest
import time


class HypothesesList(BaseModel):
    is_search_required: bool = Field(
        description="If you have not enough information, set it to true to activate search, otherwise false.")
    search_query: Optional[str] = Field(description="Search query to use if search is required.")
    hypotheses: Optional[List[str]] = Field(
        description="List of hypotheses based on the user question."
    )


def formulator_node(state: GraphState) -> dict:
    print("--- NODE: Hypothesis Formulation ---")

    parser = PydanticOutputParser(pydantic_object=HypothesesList)

    search_history = format_search_history(state['search_history'])
    if state['hypotheses_and_critics']:
        hypotheses_and_critics = format_hypotheses_and_critics(state['hypotheses_and_critics'])
    else:
        hypotheses_and_critics = "No hypotheses and critics available yet."

    prompt = ChatPromptTemplate.from_template(FORMULATOR_INITIAL_PROMPT).partial(
        format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser

    time.sleep(5)
    try:
        res = chain.invoke({
            "user_question": state['user_question'],
            "search_history": search_history,
            "hypotheses_and_critics": hypotheses_and_critics
        })
    except Exception as e:
        time.sleep(20)
        res = chain.invoke({
            "user_question": state['user_question'],
            "search_history": search_history,
            "hypotheses_and_critics": hypotheses_and_critics
        })

    if res.is_search_required:
        print(f"-> Formulator requires a search with query: '{res.search_query}'")
        req = SearchRequest(
            input_query=res.search_query
        )
        # Устанавливаем current_search_request, чтобы маршрутизатор отправил нас в 'searcher'
        return {"current_search_request": req}
    else:
        print(f"-> Formulator generated {len(res.hypotheses)} hypotheses.")
        hypotheses = res.hypotheses
        hypotheses_versions = state.get('hypotheses_and_critics', [])

        new_hypotheses = []
        for hyp in hypotheses:
            new_hypotheses.append(
                Hypothesis(
                    formulation=hyp,
                    critique="",
                    is_approved=False
                )
            )

        hypotheses_versions.append(new_hypotheses)

        # Обновляем гипотезы и сбрасываем current_search_request, чтобы маршрутизатор отправил нас в 'critics'
        return {
            'hypotheses_and_critics': hypotheses_versions,
            'current_search_request': None
        }
