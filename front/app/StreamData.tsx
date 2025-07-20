/* eslint-disable react-hooks/exhaustive-deps */
import {ComponentType, useContext, useEffect, useRef, useState} from "react";
import {FlowContext} from "@/app/FlowChart";
import {getLayoutedElements} from "@/app/dagre";
import initialNodes from "@/app/chartElements/nodes";
import initialEdges from "@/app/chartElements/edges";
import {useReactFlow} from "@xyflow/react";

export default function StreamData() {
    const {lastMessage, setNodes, setEdges, nodes, edges, isConnected} = useContext(FlowContext)
    const {fitView} = useReactFlow()
    const formulatorIdRef = useRef<string | null>(null)
    const criticsIdRef = useRef<string | null>(null)

    useEffect(() => {
        if (!lastMessage) {
            setNodes(getLayoutedElements([{
                ...initialNodes[0],
                streamedData: null,
                type: 'prompt',
                isRunning: false
            }], []).nodes);
            return;
        }

        if (lastMessage.type === "critics_approval" && nodes[nodes.length - 1].type === "critics") {
            setNodes(nds => nds.map((node, i) => i === nodes.length - 1 ? {
                ...node,
                data: {...node.data, streamedData: lastMessage}
            } : node))
        }

        if (lastMessage.type === "agent_start") {
            const nodeToInsert = initialNodes.find(inode => inode.id === lastMessage.agent);

            if (!nodeToInsert) return;

            // Check if we already have a node of this type and remove it
            let filteredNodes = nodes;
            let filteredEdges = edges;

            if (lastMessage.agent === 'formulator') {
                if (formulatorIdRef.current) {
                    // Remove existing formulator node and its edges
                    filteredNodes = nodes.filter(node => node.id !== formulatorIdRef.current);
                    filteredEdges = edges.filter(edge =>
                        edge.source !== formulatorIdRef.current && edge.target !== formulatorIdRef.current
                    );
                }
                formulatorIdRef.current = lastMessage.id;
            } else if (lastMessage.agent === 'critics') {
                if (criticsIdRef.current) {
                    // Remove existing critics node and its edges
                    filteredNodes = nodes.filter(node => node.id !== criticsIdRef.current);
                    filteredEdges = edges.filter(edge =>
                        edge.source !== criticsIdRef.current && edge.target !== criticsIdRef.current
                    );
                }
                criticsIdRef.current = lastMessage.id;
            }

            const timestamp = Date.now();
            const newNode = {
                ...nodeToInsert,
                id: lastMessage.id,
                type: lastMessage.agent,
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
                .filter(edge => edge.target === lastMessage.agent)
                .map(edge => {
                    // Find the most recent node ID that corresponds to the source type
                    const sourceNode = findMostRecentNodeByType(edge.source);
                    return sourceNode ? {
                        id: `${edge.id}_${lastMessage.id}_${timestamp}`,
                        source: sourceNode.id,
                        target: lastMessage.id,
                        animated: true
                    } : null;
                })
                .filter(edge => edge !== null);
            if (lastMessage.agent === 'end') {
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

            fitView({duration: 500, nodes: [nodes[nodes.length - 1]], padding: 1.5});
        }

        if (lastMessage.type === "agent_end") {
            setNodes(nodes =>
                nodes.map((node) =>
                    node.id === lastMessage.id
                        ? {...node, data: {...node.data, streamedData: lastMessage.result, isRunning: false}}
                        : node
                )
            );
            setEdges(e => e.map(edge => ({...edge, animated: false})));
            fitView({duration: 500, nodes: [nodes[nodes.length - 1]], padding: 1.5});
        }
    }, [lastMessage, setEdges, setNodes]);

    const [first, setFirst] = useState(false);
    useEffect(() => {
        if (!first) {
            setFirst(true)
            return;
        }
        fitView({duration: 500, nodes: [nodes[nodes.length - 1]], padding: 2});
    }, [fitView, isConnected]);

    return null
}