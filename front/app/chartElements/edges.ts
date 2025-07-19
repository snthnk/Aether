const initialEdges = [
    {id: 'of', source: 'prompt', target: 'formulator'},
    {id: 'fs', source: 'formulator', target: 'critics'},
    {id: 'ss', source: 'critics', target: 'searcher'},
    {id: "psq-so", source: "plan_search_queries", target: "search_openalex"},
    {id: "so-sa", source: "search_openalex", target: "search_arxiv"},
    {id: "sa-fs", source: "search_arxiv", target: "fetch_and_summarize"},
    {id: "fs-vs", source: "fetch_and_summarize", target: "validate_summaries"},
    {id: "vs-psq", source: "validate_summaries", target: "plan_search_queries"}, // условный путь "continue_search"
    {id: "vs-pfr", source: "validate_summaries", target: "prepare_final_report"}, // условный путь "prepare_report"
    
    {id: "prs-sr", source: "prepare_search", target: "searcher"},
    {id: "sr-fm", source: "searcher", target: "formulator"},
    {id: "fm-ct", source: "formulator", target: "critics"},
    {id: "rsq-sr", source: "refine_search_query", target: "searcher"},
    {id: "ct-rsq", source: "critics", target: "refine_search_query"}, // условный путь "refine_and_search"
    {id: "ct-end", source: "critics", target: "end"}, // условный путь "end"
    // ...[...Array(5).keys()].map(e => (
    //     {id: `sr${e}`, source: 'search', target: `read${e}`}))
]

export default initialEdges