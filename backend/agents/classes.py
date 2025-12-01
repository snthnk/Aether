from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from langgraph.graph import MessagesState
import re


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

    search_system_input: Optional[str]
    current_search_request: Optional[SearchRequest]
    papers: List[Dict]
    summaries: List[Dict]
    validated_summaries: List[Dict]
    final_report: Optional[str]
    error: Optional[str]
    search_cycles: int
    client_id: str


class SearchQueryPlannerOutput(BaseModel):
    """
    Pydantic-модель для вывода планировщика поисковых запросов.
    Описывает структуру JSON, которую должен сгенерировать LLM.
    """
    queries: List[str] = Field(
        description="Список из 3-5 альтернативных и разнообразных поисковых запросов для нахождения статей.")


class HypothesesList(BaseModel):
    """Pydantic model for the output of the hypothesis formulator."""
    hypotheses: List[str] = Field(
        description="List of 2-3 innovative hypotheses with potential implementations based on the user question and provided search results."
    )


def format_search_history(search_history: list[SearchRequest], limit: int = 5) -> str:
    """
    Форматирует историю поиска, предоставляя детальную информацию о каждой
    статье, включая уникальный citation_tag и прямую ссылку для LLM.
    """
    if not search_history:
        return "No search history available."

    res_parts = []
    seen_titles = set()

    for i, search in enumerate(reversed(search_history[-limit:])):
        res_parts.append(f"## Search Cycle Result (Query: '{search.input_query}')\n")

        papers_in_cycle = []
        for paper in search.results:
            title = paper.get('title', 'N/A').strip()
            if title in seen_titles:
                continue
            seen_titles.add(title)

            authors_list = paper.get('authors', 'Unknown Author').split(',')
            first_author = authors_list[0].split()[-1]
            source_link = paper.get('source', '')
            year = 'N/A'
            if 'arxiv' in source_link:
                match = re.search(r'/abs/(\d{2})', source_link)
                if match:
                    year = f"20{match.group(1)}"

            citation_tag = f"[{first_author} et al., {year}]"

            papers_in_cycle.append(
                f"### Source Article: {citation_tag}\n"
                f"- Title: {title}\n"
                f"- Link: {source_link}\n"
                f"- Summary: {paper.get('summary', 'No summary available.').replace(chr(10), ' ')}\n"
            )

        if not papers_in_cycle:
            res_parts.append("  - No new relevant articles found in this cycle.\n")
        else:
            res_parts.extend(papers_in_cycle)

    return "\n".join(res_parts)


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
        res += "\n"

    return res


if __name__ == '__main__':
    hyp = Hypothesis(
        formulation="Test hypothesis",
        critique="Test critique",
        is_approved=False
    )
    print(hyp.is_approved)
