import {useContext, useState} from "react";
import {Handle, Position} from "@xyflow/react";
import {Textarea} from "@/components/ui/textarea";
import {Button} from "@/components/ui/button";
import {Send} from "lucide-react";
import {BaseNode} from "@/components/base-node";
import {FlowContext} from "@/app/FlowChart";

export const PromptField = () => {
    const [prompt, setPrompt] = useState("");
    const [activated, setActivated] = useState(false);
    const {connect, isConnected} = useContext(FlowContext);
    return (
        <BaseNode className="flex flex-col gap-2 p-4">
            {activated && <Handle type="source" position={Position.Bottom} id="prompt"/>}
            <Textarea className="h-32 max-h-40" disabled={isConnected}
                      value={prompt} onChange={(e) => setPrompt(e.target.value)}
                      placeholder="Введите промпт для генерации гипотез..."/>
            <Button
                onClick={() => {
                    setActivated(true);
                    connect(`http://localhost:8000/generate?${new URLSearchParams({prompt}).toString()}`)
                }}
                disabled={isConnected}><Send/> Отправить</Button>
        </BaseNode>
    )
}