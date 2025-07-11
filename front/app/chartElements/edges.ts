const initialEdges = [
    {id: 'pc', source: 'prompt', target: 'commander'},
    {id: 'ct', source: 'commander', target: 'teller'},
    {id: 'ts', source: 'teller', target: 'search'},
    {id: 'ss', source: 'search', target: 'summary'},
    {id: 'sn', source: 'summary', target: 'novator'},
    {id: 'nr', source: 'novator', target: 'result'},
    {id: 'sp', source: 'summary', target: 'pedant'},
    {id: 'pr', source: 'pedant', target: 'result'},
    {id: 'sst', source: 'summary', target: 'strategy'},
    {id: 'sr', source: 'strategy', target: 'result'},
    // ...[...Array(5).keys()].map(e => (
    //     {id: `sr${e}`, source: 'search', target: `read${e}`}))
]

export default initialEdges