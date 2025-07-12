import os
import urllib
import time
import requests
from bs4 import BeautifulSoup
import re
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict
from backend.llm.llms import llm, llm_creative
from backend.agents.prompts import (
    SEARCH_QUERY_PLANNER_PROMPT,
    SEARCH_QUERY_PLANNER_CREATIVE_PROMPT,
    SEARCH_SUMMARIZER_PROMPT,
    VALIDATION_PROMPT
)
import pymupdf as fitz
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from backend.agents.constants import MIN_VALIDATED_ARTICLES, MAX_SEARCH_CYCLES, MAX_ARTICLES_COUNT
from backend.agents.classes import SearchRequest, GraphState
from backend.token_count import token_count


def download_arxiv_html_article(article_id: str) -> Optional[str]:
    """Скачивает и парсит HTML-версию статьи с arXiv в Markdown."""
    print(f"    [*] Пытаюсь скачать HTML-версию статьи {article_id}...")
    url = f"https://arxiv.org/html/{article_id}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        article_body = soup.find('div', class_='ltx_document')
        if not article_body:
            print("    [!] Не найден основной контент статьи в HTML.")
            return None
        for math in article_body.find_all('math'):
            if 'alttext' in math.attrs: math.replace_with(f"`{math['alttext'].strip()}`")
        for unwanted in article_body.find_all(['figure', 'table', 'aside', 'button', 'nav']): unwanted.decompose()
        for h_level in range(1, 4):
            for header in article_body.find_all(f'h{h_level}'): header.replace_with(
                f"\n{'#' * h_level} {header.get_text().strip()}\n")
        abstract = article_body.find('div', class_='ltx_abstract')
        if abstract: abstract.replace_with(f"\n## Abstract\n{abstract.get_text().strip()}\n")
        for p in article_body.find_all('p'): p.replace_with(f"{p.get_text().strip()}\n\n")
        clean_text = article_body.get_text()
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text).strip()
        print("    [+] HTML-версия успешно скачана и преобразована в Markdown.")
        return clean_text
    except requests.RequestException as e:
        print(f"    [!] Ошибка сети при скачивании HTML: {e}")
        return None
    except Exception as e:
        print(f"    [!] Ошибка при парсинге HTML: {e}")
        return None


# ========================= ПЛАНИРОВЩИК ЗАПРОСОВ (ЦИКЛИЧЕСКИЙ) =========================
class SearchQueryPlanner(BaseModel):
    queries: List[str] = Field(description="A list of 3-4 very short and concise search queries in English.")


def plan_search_queries_node(state: GraphState) -> GraphState:
    global token_count
    cycle_count = state['search_cycles'] + 1
    print(f"\n--- 🧠 АГЕНТ-ПЛАНИРОВЩИК (ЦИКЛ {cycle_count}/{MAX_SEARCH_CYCLES}) ---")
    parser = JsonOutputParser(pydantic_object=SearchQueryPlanner)

    state['papers'] = []
    previous_queries = []
    for search_req in state['search_history']:
        previous_queries.extend(search_req.search_queries)

    if not previous_queries:
        prompt = ChatPromptTemplate.from_template(SEARCH_QUERY_PLANNER_PROMPT)
        llm_chain = prompt | llm
    else:
        print(f"  [i] Предыдущие запросы не дали достаточно результатов: {previous_queries}")
        print("  [*] Генерирую новые, альтернативные запросы...")
        prompt = ChatPromptTemplate.from_template(SEARCH_QUERY_PLANNER_CREATIVE_PROMPT)
        llm_chain = prompt | llm_creative


    chain_input = {
        "query": state['current_search_request'].input_query,
        "previous_queries_str": "\n- ".join(previous_queries),
        "format_instructions": parser.get_format_instructions()
    }

    try:
        llm_response = llm_chain.invoke(chain_input)
        if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
            token_count += llm_response.usage_metadata.get('total_tokens', 0)
        plan = parser.parse(llm_response.content)
    except Exception as e:
        print(f"  [!] Ошибка при генерации нового плана поиска: {e}")
        time.sleep(20)
        llm_response = llm_chain.invoke(chain_input)
        if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
            token_count += llm_response.usage_metadata.get('total_tokens', 0)
        plan = parser.parse(llm_response.content)

    new_queries = plan['queries']
    print(f"  [+] Сгенерирован новый план поиска:")
    for q in new_queries: print(f"    - {q}")

    state['current_search_request'].search_queries = new_queries
    state['search_cycles'] = cycle_count

    return state




# ========================= УЗЛЫ ПОИСКА =========================
def search_openalex_node(state: GraphState) -> GraphState:
    print("\n--- 🔍 ИЩУ СТАТЬИ В OPENALEX ---")
    search_queries = state['current_search_request'].search_queries if state['current_search_request'] else []
    all_results = state['papers']
    seen_ids = {p.get("id") for p in all_results if p.get("id")}

    for query in search_queries:
        print(f"  [*] Запрос в OpenAlex: '{query}'")
        your_email = "senya.novozhilov@gmail.com"
        url = "https://api.openalex.org/works"
        params = {
            'search': query,
            'mailto': your_email,
            'per_page': 10  # Можно указать, сколько результатов на странице (макс. 200)
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
            new_papers_count = 0
            for paper in results:
                if paper.get("id") not in seen_ids:
                    all_results.append(paper)
                    seen_ids.add(paper.get("id"))
                    new_papers_count += 1
            print(f"    [+] Найдено {new_papers_count} новых статей.")
        except Exception as e:
            print(f"    [!] Ошибка: {e}")

    state['papers'] = all_results
    return state


def search_arxiv_node(state: GraphState) -> GraphState:
    print("\n--- 📚 ИЩУ СТАТЬИ В ARXIV ---")
    search_queries = state['current_search_request'].search_queries if state['current_search_request'] else []
    all_results = state['papers']
    seen_titles = set()
    if all_results:
        for p in all_results:
            if p is None or p.get("title", "") is None:
                continue
            seen_titles.add(p.get("title", "").lower().strip())

    for query in search_queries:
        print(f"  [*] Запрос в arXiv: '{query}'")
        try:
            url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote_plus(f'\"{query}\"')}&start=0&max_results=3&sortBy=relevance"
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            atom_ns = '{http://www.w3.org/2005/Atom}'
            new_papers_count = 0
            for entry in root.findall(f'{atom_ns}entry'):
                title = entry.find(f'{atom_ns}title').text.strip().replace('\n', ' ')
                if title.lower() in seen_titles: continue
                authors = [a.find(f'{atom_ns}name').text for a in entry.findall(f'{atom_ns}author')]
                abstract = entry.find(f'{atom_ns}summary').text.strip()
                pdf_link = next((l.get('href') for l in entry.findall(f'{atom_ns}link') if l.get('title') == 'pdf'),
                                None)
                if not pdf_link: continue
                arxiv_paper = {'id': entry.find(f'{atom_ns}id').text, 'title': title, 'abstract': abstract,
                               'authorships': [{'author': {'display_name': name}} for name in authors],
                               'best_oa_location': {'is_oa': True, 'pdf_url': pdf_link,
                                                    'source': {'display_name': 'arXiv'}},
                               'locations': [{'is_oa': True, 'pdf_url': pdf_link, 'source': {'display_name': 'arXiv'}}]}
                all_results.append(arxiv_paper)
                seen_titles.add(title.lower())
                new_papers_count += 1
            print(f"    [+] Найдено {new_papers_count} новых статей.")
        except Exception as e:
            print(f"    [!] Ошибка: {e}")

    state['papers'] = all_results
    return state


# ========================= УЗЕЛ СКАЧИВАНИЯ И СУММАРИЗАЦИИ =========================
# ========================= УЗЕЛ СКАЧИВАНИЯ И СУММАРИЗАЦИИ =========================
def fetch_and_summarize_node(state: GraphState) -> GraphState:
    global token_count
    print("\n--- 📥✍️ АГЕНТ-СУММАРИЗАТОР: СКАЧИВАЮ И ДЕЛАЮ РЕЗЮМЕ ---")
    papers = state['papers']
    existing_summaries = state['summaries']
    summarized_titles = {s['title'] for s in existing_summaries}
    new_papers = [p for p in papers if p.get('title') not in summarized_titles]

    if not new_papers:
        print("  [i] Нет новых статей для обработки в этом цикле.")
        return state

    print(f"  [*] Найдено {len(new_papers)} новых статей для суммризации.")
    # ИСПРАВЛЕНИЕ: Убираем StrOutputParser() из цепочки, чтобы получить полный объект ответа от LLM
    summarizer_chain = ChatPromptTemplate.from_template(SEARCH_SUMMARIZER_PROMPT) | llm
    new_summaries = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for i, paper in enumerate(new_papers):
        if len(new_summaries) == MAX_ARTICLES_COUNT:
            break
        title = paper.get('title', 'Без названия')
        authors = ", ".join([a.get("author", {}).get("display_name", "N/A") for a in paper.get("authorships", [])])
        print(f"\n  [{i + 1}/{len(new_papers)}] Обрабатываю: '{title[:70]}...'")
        pdf_url, source_display_name = None, "N/A"
        best_location = paper.get('best_oa_location')

        if best_location:
            source_dict = best_location.get('source')
            if source_dict:
                source_display_name = source_dict.get('display_name', 'N/A')

            pdf_url = best_location.get('pdf_url')
            if not pdf_url:
                landing_page_url = best_location.get('landing_page_url', '')
                if 'arxiv.org/abs' in landing_page_url: pdf_url = landing_page_url.replace('/abs/', '/pdf/')

        if not pdf_url:
            for loc in paper.get('locations', []):
                if loc and loc.get('pdf_url'):
                    pdf_url = loc['pdf_url']
                    source_display_name = loc.get('source', {}).get('display_name', 'N/A')
                    break
        text_content = None
        if pdf_url:
            print(f"    [*] Пытаюсь скачать PDF по URL: {pdf_url}")
            try:
                response = requests.get(pdf_url, headers=headers, timeout=45)
                response.raise_for_status()
                with fitz.open(stream=response.content, filetype="pdf") as doc:
                    pdf_text = "".join(page.get_text() for page in doc)
                if len(pdf_text.strip()) > 100:
                    text_content = pdf_text
                    print(f"    [+] PDF успешно извлечен.")
                else:
                    print(f"    [!] PDF скачан, но в нем мало текста.")
            except Exception as e:
                print(f"    [!] Не удалось обработать PDF {pdf_url}: {e}")
        is_arxiv_source = 'arxiv' in source_display_name.lower() or ('arxiv.org' in str(paper.get('id', '')))
        if not text_content and is_arxiv_source:
            arxiv_id_match = re.search(r'(\d{4}\.\d{4,5}(v\d+)?)', str(paper.get('id', '')))
            if arxiv_id_match:
                html_text = download_arxiv_html_article(arxiv_id_match.group(1))
                if html_text: text_content = html_text
            else:
                print(f"    [!] Не удалось извлечь arXiv ID для HTML-загрузки.")
        if not text_content and paper.get('abstract'):
            print("    [i] Не удалось скачать полный текст, использую аннотацию.")
            text_content = paper.get('abstract')
        if text_content:
            print("    [*] Создаю резюме...")
            try:
                # Теперь llm_response будет объектом AIMessage
                llm_response = summarizer_chain.invoke({"paper_text": text_content})
                if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
                    token_count += llm_response.usage_metadata.get('total_tokens', 0)
                # ИСПРАВЛЕНИЕ: Извлекаем текст из .content
                summary_text = llm_response.content
            except Exception as e:
                print(f"    [!] Ошибка при создании резюме: {e}")
                time.sleep(20)
                # Повторяем ту же логику
                llm_response = summarizer_chain.invoke({"paper_text": text_content})
                if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
                    token_count += llm_response.usage_metadata.get('total_tokens', 0)
                summary_text = llm_response.content

            new_summaries.append({"title": title, "authors": authors, "source": pdf_url or paper.get('id'),
                                  "summary": summary_text})
            print("    [+] Резюме успешно создано.")
        else:
            print(f"    [!] Не удалось получить текст статьи. Пропускаю.")

    state['summaries'] = existing_summaries + new_summaries
    return state


# ========================= УЗЕЛ ВАЛИДАЦИИ РЕЗЮМЕ =========================
def validate_summaries_node(state: GraphState) -> GraphState:
    global token_count
    print("\n--- ✅ АГЕНТ-ВАЛИДАТОР: ПРОВЕРЯЮ РЕЛЕВАНТНОСТЬ НОВЫХ РЕЗЮМЕ ---")
    original_query = state['current_search_request'].input_query if state['current_search_request'] else ""

    all_summaries = state['summaries']
    previously_validated = state['validated_summaries']

    validated_titles = {s['title'] for s in previously_validated}
    summaries_to_validate = [s for s in all_summaries if s['title'] not in validated_titles]

    if not summaries_to_validate:
        print("  [i] Нет новых резюме для валидации в этом цикле.")
        return state

    prompt = ChatPromptTemplate.from_template(VALIDATION_PROMPT)
    validation_chain = prompt | llm
    newly_validated_summaries = []
    print(
        f"  [*] Валидирую {len(summaries_to_validate)} новых резюме...")

    for summary_data in summaries_to_validate:
        chain_input = {"original_query": original_query, "summary_text": summary_data['summary']}
        try:
            llm_response = validation_chain.invoke(chain_input)
            if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
                token_count += llm_response.usage_metadata.get('total_tokens', 0)
            result = llm_response.content.strip().lower()

        except Exception as e:
            print(f"  [!] Ошибка при валидации резюме: {e}")
            time.sleep(20)
            llm_response = validation_chain.invoke(chain_input)
            if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
                token_count += llm_response.usage_metadata.get('total_tokens', 0)
            result = llm_response.content.strip().lower()

        if "yes" in result:
            newly_validated_summaries.append(summary_data)

    state['validated_summaries'] = previously_validated + newly_validated_summaries

    print(
        f"\n  [+] Итог валидации этого цикла: {len(newly_validated_summaries)} из {len(summaries_to_validate)} резюме прошли проверку.")
    print(f"  [i] Всего релевантных резюме: {len(state['validated_summaries'])}")

    if state['current_search_request']:
        state['current_search_request'].results = state['validated_summaries']

    return state


# ========================= УЗЕЛ ПРИНЯТИЯ РЕШЕНИЙ =========================
def decide_to_continue_node(state: GraphState) -> str:
    print("\n--- 🤔 АГЕНТ-РЕШАТЕЛЬ: АНАЛИЗИРУЮ РЕЗУЛЬТАТЫ ---")
    validated_count = len(state['validated_summaries'])
    cycle_count = state['search_cycles']
    print(f"  [i] Найдено релевантных статей: {validated_count} (цель: {MIN_VALIDATED_ARTICLES})")
    print(f"  [i] Прошло циклов поиска: {cycle_count} (лимит: {MAX_SEARCH_CYCLES})")

    if validated_count >= MIN_VALIDATED_ARTICLES:
        print("  [+] Достаточно статей найдено. Перехожу к формированию отчета.")
        return "prepare_report"
    if cycle_count >= MAX_SEARCH_CYCLES:
        print("  [!] Достигнут лимит циклов поиска. Перехожу к формированию отчета с тем, что есть.")
        return "prepare_report"
    else:
        print("  [!] Найдено мало релевантных статей. Запускаю новый цикл поиска.")
        return "continue_search"


# ========================= УЗЕЛ ПОДГОТОВКИ ФИНАЛЬНОГО ОТЧЕТА =========================
def prepare_final_report_node(state: GraphState) -> GraphState:
    print("\n--- 📋 ГОТОВЛЮ ФИНАЛЬНЫЙ ОТЧЕТ ---")
    validated_summaries = state['validated_summaries']

    if state['current_search_request'] and state['current_search_request'].results:
        state['search_history'].append(state['current_search_request'])

    if not validated_summaries:
        report = "К сожалению, после нескольких циклов поиска не удалось найти статьи, точно соответствующие вашему запросу."
        print("  [!] Нет валидированных резюме для отчета.")
        state['final_report'] = report
        return state

    query = state['current_search_request'].input_query if state['current_search_request'] else "запрос"
    report_parts = [
        f"**Итоговый отчет по вашему запросу: '{query}'**\n\nНайдено {len(validated_summaries)} релевантных статей:\n"]

    for summary_data in validated_summaries:
        report_part = (f"### 📖 Статья: {summary_data['title']}\n\n"
                       f"**Авторы:** {summary_data['authors']}\n\n"
                       f"**Источник:** {summary_data['source']}\n\n"
                       f"**Резюме:**\n{summary_data['summary']}\n")
        report_parts.append(report_part)

    final_report = "\n---\n".join(report_parts)
    print(f"  [+] Финальный отчет успешно сформирован из {len(validated_summaries)} резюме.")
    state['final_report'] = final_report
    return state


# --- 5. СБОРКА И ЗАПУСК ГРАФА ---
def compile_workflow():
    workflow = StateGraph(GraphState)
    workflow.add_node("plan_search_queries", plan_search_queries_node)
    workflow.add_node("search_openalex", search_openalex_node)
    workflow.add_node("search_arxiv", search_arxiv_node)
    workflow.add_node("fetch_and_summarize", fetch_and_summarize_node)
    workflow.add_node("validate_summaries", validate_summaries_node)
    workflow.add_node("decide_to_continue", decide_to_continue_node)
    workflow.add_node("prepare_final_report", prepare_final_report_node)

    workflow.set_entry_point("plan_search_queries")
    workflow.add_edge("plan_search_queries", "search_openalex")
    workflow.add_edge("search_openalex", "search_arxiv")
    workflow.add_edge("search_arxiv", "fetch_and_summarize")
    workflow.add_edge("fetch_and_summarize", "validate_summaries")
    workflow.add_conditional_edges(
        "validate_summaries",
        decide_to_continue_node,
        {"continue_search": "plan_search_queries", "prepare_report": "prepare_final_report"}
    )
    workflow.add_edge("prepare_final_report", END)
    app = workflow.compile()
    return app


def node_make_research(state: GraphState) -> Dict:
    """
    Основной узел-обертка для поискового модуля.
    Запускает под-граф поиска и обновляет основное состояние.
    """
    # Запускаем под-граф поиска
    final_report, request = make_research(state['current_search_request'].input_query, state)

    # Возвращаем словарь для обновления состояния основного графа
    return {
        'current_search_request': None,  # Сбрасываем текущий запрос
        'papers': [],
        'summaries': [],
        'validated_summaries': [],
        'final_report': final_report,  # Это поле сейчас не используется дальше, но оставим для консистентности
        # 'search_history' уже обновлен внутри make_research, поэтому его не трогаем
    }


def make_research(query, state: GraphState) -> tuple[str, SearchRequest]:
    # Устанавливаем начальное состояние для под-графа
    initial_search_state = state.copy()
    initial_search_state['current_search_request'] = SearchRequest(input_query=query)
    app = compile_workflow()
    state['papers'] = []
    state['summaries'] = []
    state['validated_summaries'] = []

    final_state_data = None
    recursion_limit = (MAX_SEARCH_CYCLES * 5) + 5

    for event in app.stream(initial_search_state, config={"recursion_limit": recursion_limit}):
        for node_name, state_update in event.items():
            # Обновляем состояние основного графа результатами из под-графа
            for key, value in state_update.items():
                if key in state:
                    state[key] = value
            final_state_data = state_update

    print("\n\n" + "=" * 80 + "\n✅ РАБОТА ПОИСКОВОГО АГЕНТА ЗАВЕРШЕНА ✅\n" + "=" * 80 + "\n")

    if final_state_data:
        final_report = final_state_data.get('final_report', "Отчет не был сгенерирован.")
        # `search_history` в `state` уже должен быть обновлен
        last_search_request = next((s for s in reversed(state.get('search_history', [])) if s.input_query == query),
                                   None)
        return final_report, last_search_request
    else:
        return "Не удалось получить итоговое состояние графа.", SearchRequest(input_query=query)
