const initialEdges = [
    {id: 'of', source: 'prompt', target: 'formulator'},
    {id: 'fs', source: 'formulator', target: 'critics'},
    {id: 'ss', source: 'critics', target: 'searcher'},
    {id: 'oe', source: 'critics', target: 'end'},
    // ...[...Array(5).keys()].map(e => (
    //     {id: `sr${e}`, source: 'search', target: `read${e}`}))
]

export default initialEdges