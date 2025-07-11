import dagre from '@dagrejs/dagre';
import {Edge, Node, Position} from "@xyflow/react";

const dagreGraph = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));

const nodeWidth = 250;
const nodeHeight = 125;

export const getLayoutedElements = (nodes: {
    id: string
    title: string
    description: string
}[], edges: Edge[]) => {
    dagreGraph.setGraph({rankdir: 'TB'});

    nodes.forEach((node) => {
        dagreGraph.setNode(node.id, {width: nodeWidth, height: node.id !== "prompt" ? nodeHeight : 300});
    });

    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    const newNodes: Node[] = nodes.map((node) => {
        const nodeWithPosition = dagreGraph.node(node.id);
        return {
            id: node.id,
            type: node.id,
            targetPosition: Position.Top,
            sourcePosition: Position.Bottom,
            data: {
                title: node.title,
                description: node.description,
            },
            position: {
                x: nodeWithPosition.x - nodeWidth / 2,
                y: nodeWithPosition.y - nodeHeight / 2,
            },
        } ;
    });

    return {nodes: newNodes, edges};
};