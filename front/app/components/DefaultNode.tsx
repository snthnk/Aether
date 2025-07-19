import {BaseNode} from "@/components/base-node";
import {Handle, Position} from "@xyflow/react";
import {NodeStatusIndicator} from "@/components/node-status-indicator";
import {CardContent, CardDescription, CardHeader, CardTitle} from "@/components/ui/card";
import {Badge} from "@/components/ui/badge";
import {ComponentType, memo} from "react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from "@/components/ui/dialog";

function DefaultNode({id, type, data}: {
    id: string,
    type: string,
    data: {
        title: string,
        description: string,
        dataComponent: ComponentType<{ data: any }>,
        streamedData: any,
        isRunning?: boolean
    }
}) {
    const isRunning = data.isRunning
    return (
        <NodeStatusIndicator status={!isRunning ? "success" : "loading"}>
            <BaseNode className="nowheel">
                <Handle type="target" position={Position.Top}/>
                {!id.startsWith("end") && <Handle type="source" position={Position.Bottom}/>}
                <CardHeader className="p-0 pb-2">
                    <CardTitle className="flex gap-2 items-center justify-between">
                        <p>{data.title} ({type})</p>
                        <Badge className="text-xs"
                               variant={!isRunning ? "default" : "secondary"}>{!isRunning ? "Успешно!" : "Загрузка..."}</Badge>
                    </CardTitle>
                    <CardDescription>
                        {data.description}
                    </CardDescription>
                </CardHeader>
                <Dialog>
                    <DialogTrigger asChild>
                        <CardContent className="p-0 text-xs max-h-28 overflow-y-auto cursor-pointer">
                            <data.dataComponent data={data.streamedData}/>
                        </CardContent>
                    </DialogTrigger>
                    <DialogContent className="text-base max-h-[calc(100dvh-2rem)] max-w-2xl! overflow-y-auto">
                        <DialogHeader>
                            <DialogTitle>
                                {data.title}
                            </DialogTitle>
                            <DialogDescription>
                                {data.description}
                            </DialogDescription>
                        </DialogHeader>
                        <data.dataComponent data={data.streamedData}/>
                    </DialogContent>
                </Dialog>
            </BaseNode>
        </NodeStatusIndicator>
    );
}

export default memo(DefaultNode);