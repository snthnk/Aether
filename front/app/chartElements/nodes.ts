import Orchestrator from "@/app/components/agents/Orchestrator";
import Formulator from "@/app/components/agents/Formulator";
import Critic from "@/app/components/agents/Critic";
import Searcher from "@/app/components/agents/Searcher";
import Hypotheses from "@/app/components/agents/Hypotheses";

const initialNodes = [
    {
        id: "prompt",
        title: "Ввод запроса",
        description: "Начальная точка — пользовательский запрос или задача, которую нужно решить.",
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
]

export default initialNodes;