const initialEdges = [
    {id: 'po', source: 'prompt', target: 'orchestrator'},
    {id: 'of', source: 'orchestrator', target: 'formulator'},
    {id: 'fs', source: 'formulator', target: 'searcher'},
    {id: 'ss', source: 'searcher', target: 'critics'},
    {id: 'oe', source: 'orchestrator', target: 'end'},
    // ...[...Array(5).keys()].map(e => (
    //     {id: `sr${e}`, source: 'search', target: `read${e}`}))
]

export default initialEdges