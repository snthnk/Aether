from llm.llms import llm
from ..prompts import formulator_initial_prompt
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain_core.output_parsers import PydanticOutputParser
from agents.classes import Hypothesis, GraphState, format_hypotheses_and_critics, format_search_history
from langgraph.types import Command
from langchain_core.prompts import ChatPromptTemplate
from ..classes import SearchRequest


class HypothesesList(BaseModel):
    is_search_required: bool = Field(description="If you have not enough information, set it to true to activate search, otherwise false.")
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
    
    prompt = ChatPromptTemplate.from_template(formulator_initial_prompt).partial(format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser

    res = chain.invoke({
        "user_question": state['user_question'],
        "last_reasoning": state['last_reasoning'],
        "search_history": search_history,
        "hypotheses_and_critics": hypotheses_and_critics
    })
    
    if not res.is_search_required:
        hypotheses = res.hypotheses

        hypotheses_versions = state['hypotheses_and_critics']

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

        return Command(
            update={'hypotheses_and_critics': hypotheses_versions},
            goto='orchestrator'
        )
    else:
        req = SearchRequest(
            input_query=res.search_query
        )
        return Command(
            update={"current_search_request": req},
            goto='searcher'
        )


