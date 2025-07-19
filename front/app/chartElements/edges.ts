const initialEdges = [
    // Main flow from user request
    {id: 'prompt-formulator', source: 'prompt', target: 'formulator'},
    {id: 'formulator-critics', source: 'formulator', target: 'critics'},

    // Critics to search block
    {id: 'critics-searcher', source: 'critics', target: 'searcher'},

    // Search block connections (using your existing node names)
    {id: "searcher-psq", source: "searcher", target: "plan_search_queries"},
    {id: "psq-so", source: "plan_search_queries", target: "search_openalex"},
    {id: "psq-sa", source: "plan_search_queries", target: "search_arxiv"},
    {id: "so-fs", source: "search_openalex", target: "fetch_and_summarize"},
    {id: "sa-fs", source: "search_arxiv", target: "fetch_and_summarize"},
    {id: "fs-vs", source: "fetch_and_summarize", target: "validate_summaries"},

    // Loop back for continued search
    {id: "vs-psq", source: "validate_summaries", target: "plan_search_queries"},

    // When search is complete - go to report preparation
    {id: "vs-pfr", source: "validate_summaries", target: "prepare_final_report"},

    // Report back to formulator with approved hypotheses
    {id: "pfr-formulator", source: "prepare_final_report", target: "formulator"},

    // Alternative path through refine_search_query
    {id: "critics-rsq", source: "critics", target: "refine_search_query"},
    {id: "rsq-searcher", source: "refine_search_query", target: "searcher"},

    // Final output to user
    {id: "critics-end", source: "critics", target: "end"}
]

export default initialEdges