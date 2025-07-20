interface SearchRequest {
    input_query: string; // Короткий запрос на поиск
    search_queries: string[]; // Запросы в браузер, которые генерирует агент
    results: Record<string, any>[]; // Список из нескольких валидированных резюме
}

export interface Hypothesis {
    formulation: string;
    critique: string;
    is_approved: boolean;
}

interface GraphState {
    user_question: string;
    last_reasoning: string;
    search_history: SearchRequest[];
    hypotheses_and_critics: Hypothesis[][];
    last_goto: string;

    search_system_input?: string;
    current_search_request?: SearchRequest;
    papers: Record<string, any>[];
    summaries: Record<string, any>[];
    validated_summaries: Record<string, any>[];
    final_report?: string;
    error?: string;
    search_cycles: number;
    client_id: string;
}

export type DataType = {
    input: GraphState;
    output: GraphState;
}