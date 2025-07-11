/* eslint-disable react-hooks/exhaustive-deps */
'use client'

import {Background, Controls, Edge, MarkerType, Node, ReactFlow, useEdgesState, useNodesState} from '@xyflow/react';

import '@xyflow/react/dist/style.css';
import {getLayoutedElements} from "@/app/dagre";
import {createContext, useEffect} from "react";
import {PromptField} from "@/app/components/PromptField";
import initialNodes from "@/app/chartElements/nodes";
import DefaultNode from "@/app/components/DefaultNode";
import useSSE from "@/app/useSSE";
import initialEdges from "@/app/chartElements/edges";

export const FlowContext = createContext<{
    nodes: Node[],
    edges: Edge[],
    setNodes: (nodes: Node[]) => void,
    setEdges: (edges: Edge[]) => void,
    isConnected: boolean,
    connect: (prompt: string) => void,
}>({
    nodes: [],
    edges: [],
    setNodes: () => {
    },
    setEdges: () => {
    },
    isConnected: false,
    connect: () => {
    },
})

export default function FlowChart() {
    const [nodes, setNodes] = useNodesState<Node>([]);
    const [edges, setEdges] = useEdgesState<Edge>([]);

    const {connect, data, isConnected} = useSSE();

    useEffect(() => {
        console.log(data);
        if (!data) {
            setNodes(getLayoutedElements([{...initialNodes[0], type: 'prompt'}], []).nodes);
            return;
        }

        const nodeToInsert = initialNodes.find(inode => inode.id === data.agent);
        const edgeToInsert = initialEdges.find(iedge => iedge.target === data.agent);

        if (!nodeToInsert || !edgeToInsert) return;

        const timestamp = Date.now();
        const newNode = {
            ...nodeToInsert,
            id: `${nodeToInsert.id}_${timestamp}`,
            type: data.agent,
        };

        // Find the most recent node of the source type to connect from
        const sourceType = edgeToInsert.source;
        const sourceNode = [...nodes].reverse().find(n => n.type === sourceType) || nodes[0];

        const newEdge = {
            ...edgeToInsert,
            id: `${edgeToInsert.id}_${timestamp}`,
            source: sourceNode.id,
            target: newNode.id
        };

        const currentNodes = nodes.map(e => ({
            id: e.id,
            type: e.type!,
            title: e.data.title as string,
            description: e.data.description as string,
        }));

        const {nodes: insertNodes, edges: insertEdges} = getLayoutedElements(
            [...currentNodes, newNode],
            [...edges, newEdge]
        );

        console.log(insertNodes, insertEdges);

        setNodes(insertNodes);
        setEdges(insertEdges);
    }, [data, setEdges, setNodes]);

    return (
        <FlowContext.Provider value={{
            nodes, edges, setNodes, setEdges, isConnected, connect
        }}>
            <ReactFlow 
                proOptions={{hideAttribution: true}} 
                nodes={nodes.map(e => ({
                    style: {width: 250},
                    ...e,
                }))} 
                edges={edges.map(e => ({
                    type: "smoothstep",
                    markerEnd: {type: MarkerType.Arrow},
                    ...e,
                }))}
                nodeTypes={{
                    ...Object.fromEntries(initialNodes.map(e => [e.id, DefaultNode])),
                    prompt: PromptField,
                }}
                fitView>
                <Background/>
                <Controls/>
            </ReactFlow>
        </FlowContext.Provider>
    );
}