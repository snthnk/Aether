import {BaseNode} from "@/components/base-node";
import {Handle, Position} from "@xyflow/react";
import {NodeStatusIndicator} from "@/components/node-status-indicator";
import {CardDescription, CardHeader, CardTitle} from "@/components/ui/card";
import {Badge} from "@/components/ui/badge";
import useFlowStore from "@/app/store";
import nodes from "@/app/chartElements/nodes";

export default function DefaultNode({data}: { data: { title: string, description: string } }) {
    const {currentStep} = useFlowStore()
    console.log(nodes.findIndex(({title}) => title === data.title));
    const isSuccess = currentStep-1 >= nodes.findIndex(({title}) => title === data.title)
    return (
        <NodeStatusIndicator status={isSuccess ? "success" : "loading"}>
            <BaseNode>
                <Handle type="target" position={Position.Top}/>
                <Handle type="source" position={Position.Bottom}/>
                <CardHeader className="p-0">
                    <CardTitle className="flex justify-between">
                        <p>{data.title}</p>
                        <Badge
                            variant={isSuccess ? "default" : "secondary"}>{isSuccess ? "Успешно!" : "Загрузка..."}</Badge>
                    </CardTitle>
                    <CardDescription>
                        {data.description}
                    </CardDescription>
                </CardHeader>
            </BaseNode>
        </NodeStatusIndicator>
    );
}