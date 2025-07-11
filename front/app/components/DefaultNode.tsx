import {BaseNode} from "@/components/base-node";
import {Handle, Position} from "@xyflow/react";
import {NodeStatusIndicator} from "@/components/node-status-indicator";
import {CardDescription, CardHeader, CardTitle} from "@/components/ui/card";
import {Badge} from "@/components/ui/badge";
import {useContext} from "react";
import {FlowContext} from "@/app/FlowChart";

export default function DefaultNode({id, data}: { id: string, data: { title: string, description: string } }) {
    const {nodes} = useContext(FlowContext)
    const isRunning = nodes[nodes.length - 1].id === id;
    return (
        <NodeStatusIndicator status={!isRunning ? "success" : "loading"}>
            <BaseNode>
                <Handle type="target" position={Position.Top}/>
                <Handle type="source" position={Position.Bottom}/>
                <CardHeader className="p-0">
                    <CardTitle className="flex justify-between">
                        <p>{data.title}</p>
                        <Badge
                            variant={!isRunning ? "default" : "secondary"}>{!isRunning ? "Успешно!" : "Загрузка..."}</Badge>
                    </CardTitle>
                    <CardDescription>
                        {data.description}
                    </CardDescription>
                </CardHeader>
            </BaseNode>
        </NodeStatusIndicator>
    );
}