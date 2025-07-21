import dagre from '@dagrejs/dagre';
import {Edge, Node, Position} from "@xyflow/react";
import {ComponentType} from "react";

const nodeWidth = 350;
const nodeHeight = 225;

export const getLayoutedElements = (nodes: {
    id: string
    type: string
    title: string
    description: string
    isRunning: boolean
    streamedData?: any
    dataComponent?: ComponentType<{ data: any }>
}[], edges: Edge[]) => {
    const dagreGraph = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
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
            type: node.type,
            targetPosition: Position.Top,
            sourcePosition: Position.Bottom,
            data: {
                isRunning: node.isRunning,
                title: node.title,
                description: node.description,
                dataComponent: node.dataComponent,
                streamedData: node.streamedData
            },
            position: {
                x: nodeWithPosition.x - nodeWidth / 2,
                y: nodeWithPosition.y - nodeHeight / 2,
            },
        };
    });

    return {nodes: newNodes, edges};
};