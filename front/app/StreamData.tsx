/* eslint-disable react-hooks/exhaustive-deps */
import {ComponentType, useContext, useEffect, useState} from "react";
import {FlowContext} from "@/app/FlowChart";
import {getLayoutedElements} from "@/app/dagre";
import initialNodes from "@/app/chartElements/nodes";
import {useReactFlow} from "@xyflow/react";

export default function StreamData() {
    const {data, setNodes, setEdges, nodes, edges, isConnected} = useContext(FlowContext)
    const {fitView} = useReactFlow()
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
            // const edgeToInsert = initialEdges.find(iedge => iedge.target === data.agent);
            const edgeToInsert = {
                id: "asaff",
                source: nodes[nodes.length - 1].id,
                target: data.agent,
            };

            if (!nodeToInsert || !edgeToInsert) return;

            const timestamp = Date.now();
            const newNode = {
                ...nodeToInsert,
                id: `${nodeToInsert.id}_${timestamp}`,
                type: data.agent,
                isRunning: true,
                dataComponent: nodeToInsert.dataComponent as ComponentType<{ data: any }>,
                streamedData: null,
            };

            const sourceType = edgeToInsert.source;
            // const sourceNode = [...nodes].reverse().find(n => n.type === sourceType) || nodes[0];

            let newEdges = [];

            // If this is an 'end' node, connect it to all 'critics' nodes
            if (data.agent === 'end') {
                const criticsNodes = nodes.filter(n => n.type === 'critics');
                newEdges = criticsNodes.map(criticNode => ({
                    id: `critics-end_${criticNode.id}_${timestamp}`,
                    source: criticNode.id,
                    target: newNode.id,
                    animated: true
                }));
            } else {
                // Regular edge connection
                // newEdges = [{
                //     ...edgeToInsert,
                //     id: `${edgeToInsert.id}_${timestamp}`,
                //     source: sourceNode.id,
                //     target: newNode.id,
                //     animated: true
                // }];
                newEdges = [{
                    ...edgeToInsert,
                    id: `${edgeToInsert.id}_${timestamp}`,
                    source: nodes[nodes.length - 1].id,
                    target: newNode.id,
                    animated: true
                }];
            }

            const currentNodes = nodes.map(e => ({
                id: e.id,
                type: e.type!,
                title: e.data.title as string,
                description: e.data.description as string,
                isRunning: e.data.isRunning as boolean,
                dataComponent: e.data.dataComponent as ComponentType<{ data: any }>,
                streamedData: e.data.streamedData
            }));

            console.log(currentNodes);

            const {nodes: insertNodes, edges: insertEdges} = getLayoutedElements(
                [...currentNodes, newNode],
                [...edges, ...newEdges]
            );

            setNodes(insertNodes);
            setEdges(insertEdges);

            fitView({duration: 500, nodes: insertNodes.slice(insertNodes.length - 2, insertNodes.length)});
        }

        if (data.type === "agent_end") {
            setNodes(nodes =>
                nodes.map((node, index) =>
                    index === nodes.length - 1
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