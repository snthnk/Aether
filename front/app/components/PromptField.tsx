import {useContext, useState} from "react";
import {Handle, Position} from "@xyflow/react";
import {Textarea} from "@/components/ui/textarea";
import {Button} from "@/components/ui/button";
import {Send} from "lucide-react";
import {BaseNode} from "@/components/base-node";
import {FlowContext} from "@/app/FlowChart";
import {getLayoutedElements} from "@/app/dagre";
import initialNodes from "@/app/chartElements/nodes";

export const PromptField = () => {
    const [prompt, setPrompt] = useState("");
    const [activated, setActivated] = useState(false);
    const {connect, isConnected, setNodes, setEdges} = useContext(FlowContext);
    return (
        <BaseNode className="flex flex-col gap-2 p-4">
            {activated && <Handle type="source" position={Position.Bottom} id="prompt"/>}
            <Textarea className="h-32 max-h-40" disabled={isConnected}
                      value={prompt} onChange={(e) => setPrompt(e.target.value)}
                      placeholder="Введите промпт для генерации гипотез..."/>
            <Button
                onClick={() => {
                    const {nodes: layoutedNodes} = getLayoutedElements([{
                        ...initialNodes[0],
                        type: 'prompt',
                        isRunning: false
                    }], [])
                    setNodes(layoutedNodes);
                    setEdges([]);
                    setActivated(true);
                    connect(`http://localhost:8000/events?${new URLSearchParams({prompt}).toString()}&no_delay=true`)
                    // connect(`http://localhost:8000/generate?${new URLSearchParams({prompt}).toString()}`)
                }}
                disabled={isConnected}><Send/> Отправить</Button>
        </BaseNode>
    )
}