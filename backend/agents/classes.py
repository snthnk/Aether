from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from langgraph.graph import MessagesState

class SearchRequest(BaseModel):
    input_query: str = Field(description="Короткий запрос на поиск, который подается в начале этого модуля")
    search_queries: List[str] = Field(default_factory=list, description="Запросы в браузер, которые генерирует агент")
    results: List[Dict] = Field(default_factory=list, description="Список из нескольких валидированных резюме")

class Hypothesis(BaseModel):
    formulation: str
    critique: str
    is_approved: bool

class GraphState(MessagesState):
    user_question: str
    last_reasoning: str
    search_history: List[SearchRequest]
    hypotheses_and_critics: List[List[Hypothesis]]
    last_goto: str

    # Дополнительные поля для работы поисковика
    search_system_input: Optional[str]
    current_search_request: Optional[SearchRequest]
    papers: List[Dict]
    summaries: List[Dict]
    validated_summaries: List[Dict]
    final_report: Optional[str]
    error: Optional[str]
    search_cycles: int

class SearchQueryPlannerOutput(BaseModel):
    """
    Pydantic-модель для вывода планировщика поисковых запросов.
    Описывает структуру JSON, которую должен сгенерировать LLM.
    """
    queries: List[str] = Field(description="Список из 3-5 альтернативных и разнообразных поисковых запросов для нахождения статей.")


def format_search_history(search_history: list[SearchRequest], limit: int = 5) -> str:
    search_history = search_history[-limit:]
    
    res = ""
    for i, search in enumerate(search_history):
        res += f"Search {i + 1}:\n"
        res += f"- User query: {search.input_query}\n"
        res += f"- Search queries: {', '.join(search.search_queries)}\n"
        res += f"- Result: {search.results}\n"
        res += "\n"
    
    return res


def format_hypotheses_and_critics(hypotheses_and_critics: list[list[Hypothesis]], limit: int = 5) -> str:
    hypotheses_and_critics = hypotheses_and_critics[-limit:]
    
    res = ""
    for i, ver in enumerate(hypotheses_and_critics):
        res += f"Hypotheses version {i + 1}:\n"
        
        for hyp in ver:
            if hyp.is_approved: continue

            res += f"- Hypothesis: {hyp.formulation}\n"
            if hyp.critique:
                res += f"  Critique: {hyp.critique}\n"
            # res += f"  Approved: {'Yes' if hyp.is_approved else 'No'}\n"
        res += "\n"
    
    return res


if __name__ == '__main__':
    hyp = Hypothesis(
        formulation="Test hypothesis",
        critique="Test critique",
        is_approved=False
    )
    print(hyp.is_approved)
