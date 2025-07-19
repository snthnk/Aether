'use client'

import {Background, Controls, Edge, MarkerType, Node, ReactFlow, useEdgesState, useNodesState} from '@xyflow/react';

import '@xyflow/react/dist/style.css';
import {createContext, Dispatch, SetStateAction} from "react";
import {PromptField} from "@/app/components/PromptField";
import initialNodes from "@/app/chartElements/nodes";
import DefaultNode from "@/app/components/DefaultNode";
import {toast} from "sonner";
import StreamData from "@/app/StreamData";
import useWebSocket from "@/app/useWebSocket";

export const FlowContext = createContext<{
    nodes: Node[],
    edges: Edge[],
    lastMessage: Record<string, string> | null,
    setNodes: Dispatch<SetStateAction<Node[]>>,
    setEdges: Dispatch<SetStateAction<Edge[]>>,
    isConnected: boolean,
    connect: (prompt: string) => void,
    sendMessage: (data: string) => void,
}>({
    nodes: [],
    edges: [],
    lastMessage: null,
    setNodes: () => {
    },
    setEdges: () => {
    },
    isConnected: false,
    connect: () => {
    },
    sendMessage: () => {
    }
})

export default function FlowChart() {
    const [nodes, setNodes] = useNodesState<Node>([]);
    const [edges, setEdges] = useEdgesState<Edge>([]);

    const {connect, lastMessage, isConnected, sendMessage} = useWebSocket({
        onError: () => nodes.length === 1 && toast.error("Ошибка подключения к серверу.", {richColors: true})
    });

    return (
        <FlowContext.Provider value={{
            nodes, edges, lastMessage, setNodes, setEdges, isConnected, connect, sendMessage
        }}>
            <ReactFlow
                proOptions={{hideAttribution: true}}
                nodes={nodes.map(e => ({
                    style: {width: 350},
                    ...e,
                }))}
                edges={edges.map(e => ({
                    type: "smoothstep",
                    markerEnd: {type: MarkerType.Arrow},
                    ...e,
                    animated: isConnected && e.animated
                }))}
                nodeTypes={{
                    ...Object.fromEntries(initialNodes.map(e => [e.id, DefaultNode])),
                    prompt: PromptField,
                }}
                fitView>
                <Background/>
                <Controls/>
                <StreamData/>
            </ReactFlow>
        </FlowContext.Provider>
    );
}