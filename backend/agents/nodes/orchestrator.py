#WIP
from ..classes import GraphState
from llm.llms import llm
from pydantic import BaseModel, Field
from ..prompts import orchestrator_init_promt
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
from langchain_core.output_parsers import PydanticOutputParser
from ..classes import format_hypotheses_and_critics


class OrchestratorData(BaseModel):
    reasoning: str = Field(description="Your reasoning about the current topic, based on the user question and hypotheses.")
    goto: str = Field(description="Next step to take: critics, formulator or end.")


def orchestrator_node(state: GraphState) -> dict:
    print("--- NODE: Orchestrator ---")

    parser = PydanticOutputParser(pydantic_object=OrchestratorData)
    
    if state['hypotheses_and_critics']:
        hypotheses_and_critics = format_hypotheses_and_critics([state['hypotheses_and_critics'][-1]])
    else:
        hypotheses_and_critics = ""
    
    # prompt = ChatPromptTemplate.from_messages([
    #     ("system", orchestrator_init_promt)
    # ]).partial(format_instructions=parser.get_format_instructions())
    prompt = ChatPromptTemplate.from_template(orchestrator_init_promt).partial(format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser
    
    result = chain.invoke({
        "user_question": state['user_question'],
        #"last_reasoning": state['last_reasoning'],
        "last_goto": state['last_goto'],
        "hypotheses_and_critics": hypotheses_and_critics
    })

    goto = result.goto

    update = {
        "last_goto": goto,
        "last_reasoning": result.reasoning,
    }

    return Command(
        update=update,
        goto=goto
    )