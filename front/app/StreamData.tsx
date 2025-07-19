/* eslint-disable react-hooks/exhaustive-deps */
import {ComponentType, useContext, useEffect, useRef, useState} from "react";
import {FlowContext} from "@/app/FlowChart";
import {getLayoutedElements} from "@/app/dagre";
import initialNodes from "@/app/chartElements/nodes";
import initialEdges from "@/app/chartElements/edges";
import {useReactFlow} from "@xyflow/react";

export default function StreamData() {
    const {data, setNodes, setEdges, nodes, edges, isConnected} = useContext(FlowContext)
    const {fitView} = useReactFlow()
    const formulatorIdRef = useRef<string|null>(null)
    const criticsIdRef = useRef<string|null>(null)

    useEffect(() => {
        if (!data) {
            setNodes(getLayoutedElements([{
                ...initialNodes[0],
                streamedData: null,
                type: 'prompt',
                isRunning: false
            }], []).nodes);
            return;
        }

        if (data.type === "agent_start") {
            const nodeToInsert = initialNodes.find(inode => inode.id === data.agent);

            if (!nodeToInsert) return;

            // Check if we already have a node of this type and remove it
            let filteredNodes = nodes;
            let filteredEdges = edges;

            if (data.agent === 'formulator') {
                if (formulatorIdRef.current) {
                    // Remove existing formulator node and its edges
                    filteredNodes = nodes.filter(node => node.id !== formulatorIdRef.current);
                    filteredEdges = edges.filter(edge =>
                        edge.source !== formulatorIdRef.current && edge.target !== formulatorIdRef.current
                    );
                }
                formulatorIdRef.current = data.id;
            } else if (data.agent === 'critics') {
                if (criticsIdRef.current) {
                    // Remove existing critics node and its edges
                    filteredNodes = nodes.filter(node => node.id !== criticsIdRef.current);
                    filteredEdges = edges.filter(edge =>
                        edge.source !== criticsIdRef.current && edge.target !== criticsIdRef.current
                    );
                }
                criticsIdRef.current = data.id;
            }

            const timestamp = Date.now();
            const newNode = {
                ...nodeToInsert,
                id: data.id,
                type: data.agent,
                isRunning: true,
                dataComponent: (nodeToInsert.dataComponent) as ComponentType<{ data: any }>,
                streamedData: null,
            };

            // Helper function to find the most recent node of a given type
            const findMostRecentNodeByType = (nodeType: string) => {
                const nodesOfType = filteredNodes.filter(node => node.type === nodeType);
                if (nodesOfType.length === 0) return null;

                // Sort by creation time (assuming node IDs contain timestamps or are chronologically ordered)
                // If nodes don't have timestamps, we can use the order they appear in the array
                return nodesOfType[nodesOfType.length - 1]; // Get the last one (most recent)
            };

            // Find edges that should connect to this new node based on initialEdges
            // Special case for 'end' node - connect from most recent critics node
            let newEdges = initialEdges
                .filter(edge => edge.target === data.agent)
                .map(edge => {
                    // Find the most recent node ID that corresponds to the source type
                    const sourceNode = findMostRecentNodeByType(edge.source);
                    return sourceNode ? {
                        id: `${edge.id}_${data.id}_${timestamp}`,
                        source: sourceNode.id,
                        target: data.id,
                        animated: true
                    } : null;
                })
                .filter(edge => edge !== null);
            if (data.agent === 'end') {
                const mostRecentCriticsNode = findMostRecentNodeByType('critics');
                if (mostRecentCriticsNode) {
                    newEdges = [{
                        id: `critics-end_${mostRecentCriticsNode.id}_${timestamp}`,
                        source: mostRecentCriticsNode.id,
                        target: newNode.id,
                        animated: true
                    }];
                }
            }

            const currentNodes = filteredNodes.map(e => ({
                id: e.id,
                type: e.type!,
                title: e.data.title as string,
                description: e.data.description as string,
                isRunning: e.data.isRunning as boolean,
                dataComponent: ((e.data.dataComponent)) as ComponentType<{ data: any }>,
                streamedData: e.data.streamedData
            }));

            const {nodes: insertNodes, edges: insertEdges} = getLayoutedElements(
                [...currentNodes, newNode],
                [...filteredEdges, ...newEdges]
            );

            setNodes(insertNodes);
            setEdges(insertEdges);

            fitView({duration: 500, nodes: insertNodes.slice(insertNodes.length - 2, insertNodes.length)});
        }

        if (data.type === "agent_end") {
            setNodes(nodes =>
                nodes.map((node) =>
                    node.id === data.id
                        ? {...node, data: {...node.data, streamedData: data.result, isRunning: false}}
                        : node
                )
            );
            setEdges(e => e.map(edge => ({...edge, animated: false})));
            fitView({duration: 500, nodes: nodes.slice(nodes.length - 2, nodes.length)});
        }
    }, [data, setEdges, setNodes]);

    const [first, setFirst] = useState(false);
    useEffect(() => {
        if (!first) {
            setFirst(true)
            return;
        }
        fitView({duration: 500, nodes})
    }, [fitView, isConnected]);

    return null
}