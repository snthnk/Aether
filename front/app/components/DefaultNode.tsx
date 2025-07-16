import {BaseNode} from "@/components/base-node";
import {Handle, Position} from "@xyflow/react";
import {NodeStatusIndicator} from "@/components/node-status-indicator";
import {CardContent, CardDescription, CardHeader, CardTitle} from "@/components/ui/card";
import {Badge} from "@/components/ui/badge";
import {ComponentType} from "react";

export default function DefaultNode({id, data}: { id: string, data: { title: string, description: string, dataComponent: ComponentType<{data: any}>, streamedData: any, isRunning?: boolean } }) {
    const isRunning = data.isRunning
    return (
        <NodeStatusIndicator status={!isRunning ? "success" : "loading"}>
            <BaseNode className="nowheel">
                <Handle type="target" position={Position.Top}/>
                {!id.startsWith("end") && <Handle type="source" position={Position.Bottom}/>}
                <CardHeader className="p-0 pb-2">
                    <CardTitle className="flex justify-between">
                        <p>{data.title}</p>
                        <Badge
                            variant={!isRunning ? "default" : "secondary"}>{!isRunning ? "Успешно!" : "Загрузка..."}</Badge>
                    </CardTitle>
                    <CardDescription>
                        {data.description}
                    </CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                    <data.dataComponent data={data.streamedData}/>
                </CardContent>
            </BaseNode>
        </NodeStatusIndicator>
    );
}