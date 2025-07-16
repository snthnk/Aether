## UNCHANGED (Correct from previous response) ##

from backend.llm.llms import llm
from backend.agents.prompts import FORMULATOR_INITIAL_PROMPT
from langchain_core.output_parsers import PydanticOutputParser
# Import the simplified HypothesesList class
from backend.agents.classes import Hypothesis, GraphState, format_hypotheses_and_critics, format_search_history, \
    HypothesesList
from langchain_core.prompts import ChatPromptTemplate
import time


def formulator_node(state: GraphState) -> dict:
    print("--- NODE: Hypothesis Formulation ---")
    parser = PydanticOutputParser(pydantic_object=HypothesesList)

    # The search history now contains the most recent search results.
    # We pass the last search result to give the agent fresh context.
    search_history = format_search_history(state['search_history'])

    if state['hypotheses_and_critics']:
        hypotheses_and_critics = format_hypotheses_and_critics(state['hypotheses_and_critics'])
    else:
        hypotheses_and_critics = "No critiques yet. This is the first iteration."

    prompt = ChatPromptTemplate.from_template(FORMULATOR_INITIAL_PROMPT).partial(
        format_instructions=parser.get_format_instructions())

    llm_chain = prompt | llm

    chain_input = {
        "user_question": state['user_question'],
        "search_history": search_history,
        "hypotheses_and_critics": hypotheses_and_critics
    }

    try:
        llm_response = llm_chain.invoke(chain_input)
        res = parser.parse(llm_response.content)

    except Exception as e:
        print("\n--- ERROR: Failed to parse LLM response in Formulator ---")
        print(f"Exception Type: {type(e)}")
        print(f"Exception Details: {e}")
        raw_output = llm_response.content if 'llm_response' in locals() else "LLM response not available"
        print(f"Problematic LLM Output:\n---\n{raw_output}\n---")
        print("Retrying after a 20-second delay...")
        time.sleep(20)
        llm_response = llm_chain.invoke(chain_input)
        res = parser.parse(llm_response.content)

    # Simplified logic. Always formulate hypotheses.
    print(f"-> Formulator generated {len(res.hypotheses)} new hypotheses.")
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

    # Clear the current_search_request as it has been fulfilled.
    return {
        'hypotheses_and_critics': hypotheses_versions,
        'current_search_request': None
    }