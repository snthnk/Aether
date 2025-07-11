'use client'

import {Background, Controls, Edge, MarkerType, Node, ReactFlow, useEdgesState, useNodesState} from '@xyflow/react';

import '@xyflow/react/dist/style.css';
import {getLayoutedElements} from "@/app/dagre";
import {useEffect} from "react";
import {PromptField} from "@/app/components/PromptField";
import initialEdges from "@/app/chartElements/edges";
import initialNodes from "@/app/chartElements/nodes";
import useFlowStore from "@/app/store";
import DefaultNode from "@/app/components/DefaultNode";


export default function FlowChart() {
    const [nodes, setNodes] = useNodesState<Node>([]);
    const [edges, setEdges] = useEdgesState<Edge>([]);

    const {currentStep} = useFlowStore();

    useEffect(() => {
        const {
            nodes: layoutedNodes,
            edges: layoutedEdges
        } = getLayoutedElements(
            initialNodes.slice(0, currentStep + 1),
            initialEdges
        )
        setNodes(layoutedNodes);
        setEdges(layoutedEdges);
    }, [currentStep, setEdges, setNodes]);
    return (
        <ReactFlow proOptions={{hideAttribution: true}} nodes={nodes.map(e => ({
                style: {width: 250},
                ...e,
            })
        )} edges={edges.map((e, i) => ({
                type: "smoothstep",
                markerEnd: {type: MarkerType.Arrow},
                animated: i >= currentStep - 1,
                ...e,
            })
        )}
                   nodeTypes={{
                       ...Object.fromEntries(initialNodes.map(e => [e.id, DefaultNode])),
                       prompt: PromptField,
                   }}
                   fitView>
            <Background/>
            <Controls/>
        </ReactFlow>
    );
}