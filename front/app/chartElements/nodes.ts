import Orchestrator from "@/app/components/agents/Orchestrator";
import Formulator from "@/app/components/agents/Formulator";
import Critic from "@/app/components/agents/Critic";
import Searcher from "@/app/components/agents/Searcher";
import Hypotheses from "@/app/components/agents/Hypotheses";
import PlanSearch from "@/app/components/agents/PlanSearch";
import OpenAlexSearcher from "@/app/components/agents/OpenAlexSearcher";
import ArxivSearcher from "@/app/components/agents/ArxivSearcher";
import Summaries from "@/app/components/agents/Summaries";
import ValidatedSummaries from "@/app/components/agents/ValidatedSummaries";
import SearchReport from "@/app/components/agents/SearchReport";
import PrepareSearch from "@/app/components/agents/PrepareSearch";

const Empty = ()=>null

const initialNodes = [
    {
        id: "prompt",
        title: "Ввод запроса",
        description: "Начальная точка — пользовательский запрос или задача, которую нужно решить.",
        dataComponent: Empty
    },
    {
        id: "orchestrator",
        title: "Командир",
        description: "Управляет маршрутом выполнения, распределяя задачи между агентами.",
        dataComponent: Orchestrator
    },
    {
        id: "formulator",
        title: "Формулировщик",
        description: "Генерирует нестандартные идеи или оригинальные решения.",
        dataComponent: Formulator
    },
    {
        id: "searcher",
        title: "Поисковик",
        description: "Ищет актуальную информацию в интернете или базе данных.",
        dataComponent: Searcher
    },
    {
        id: "critics",
        title: "Критик",
        description: "Сжимает и обобщает длинные тексты или списки данных.",
        dataComponent: Critic
    },
    {
        id: "end",
        title: "Гипотезы",
        description: "Окончательный вывод гипотез.",
        dataComponent: Hypotheses
    },
    {
        id: "plan_search_queries",
        title: "Планирование запросов",
        description: "Создаёт стратегию поиска по научным базам.",
        dataComponent: PlanSearch
    },
    {
        id: "search_openalex",
        title: "Поиск OpenAlex",
        description: "Выполняет поиск по базе данных OpenAlex.",
        dataComponent: OpenAlexSearcher
    },
    {
        id: "search_arxiv",
        title: "Поиск arXiv",
        description: "Выполняет поиск научных статей на arXiv.",
        dataComponent: ArxivSearcher
    },
    {
        id: "fetch_and_summarize",
        title: "Резюмирование",
        description: "Извлекает и кратко резюмирует статьи.",
        dataComponent: Summaries
    },
    {
        id: "validate_summaries",
        title: "Валидация резюме",
        description: "Оценивает качество и релевантность резюме.",
        dataComponent: ValidatedSummaries
    },
    {
        id: "decide_to_continue",
        title: "Решение о продолжении",
        description: "Решает, продолжать ли поиск или завершить.",
        dataComponent: Empty
    },
    {
        id: "prepare_final_report",
        title: "Итоговый отчёт",
        description: "Готовит финальный отчёт по результатам.",
        dataComponent: SearchReport
    },
    {
        id: "prepare_search",
        title: "Подготовка к поиску",
        description: "Инициализация параметров начального поиска.",
        dataComponent: PrepareSearch
    },
    {
        id: "refine_search_query",
        title: "Уточнение запроса",
        description: "Уточняет поисковый запрос на основе анализа.",
        dataComponent: Empty
    }
]

export default initialNodes;