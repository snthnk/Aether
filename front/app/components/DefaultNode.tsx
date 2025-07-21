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
import {Expand} from "lucide-react";

const DISABLED_DIALOG_TYPES = ["upload_articles", "prompt", "critics"];

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
    const dialogDisabled = type === "critics" ? !(data.streamedData && data.streamedData.output) : DISABLED_DIALOG_TYPES.includes(type);
    return (
        <NodeStatusIndicator status={!isRunning ? "success" : "loading"}>
            <BaseNode className="nowheel">
                <Handle type="target" isConnectable={false} position={Position.Top}/>
                {!id.startsWith("end") && <Handle type="source" isConnectable={false} position={Position.Bottom}/>}
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
                {dialogDisabled ? (
                    <CardContent className="p-0 text-xs max-h-28 overflow-y-auto cursor-pointer">
                        <data.dataComponent data={data.streamedData}/>
                    </CardContent>
                ) : (
                    <Dialog>
                        <DialogTrigger asChild>
                            <CardContent className="p-1 relative text-xs max-h-28 overflow-y-auto cursor-pointer">
                                <data.dataComponent data={data.streamedData}/>
                                <div className="absolute top-0 left-0 w-full h-full flex gap-2 items-center justify-center opacity-0 hover:opacity-100 hover:bg-black/50 transition-all text-white font-semibold text-xl rounded-sm">
                                    <Expand/> Расширить
                                </div>
                            </CardContent>
                        </DialogTrigger>
                        <DialogContent>
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
                )}
            </BaseNode>
        </NodeStatusIndicator>
    );
}

export default memo(DefaultNode);