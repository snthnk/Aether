import {useContext, useEffect, useState} from "react";
import {Handle, Position} from "@xyflow/react";
import {Textarea} from "@/components/ui/textarea";
import {Button} from "@/components/ui/button";
import {Send} from "lucide-react";
import {BaseNode} from "@/components/base-node";
import {FlowContext} from "@/app/FlowChart";
import {getLayoutedElements} from "@/app/dagre";
import initialNodes from "@/app/chartElements/nodes";
import {CardDescription, CardHeader, CardTitle} from "@/components/ui/card";
import {GlowEffect} from "@/components/ui/glow-effect";

export const PromptField = () => {
    const [prompt, setPrompt] = useState("");
    const [activated, setActivated] = useState(false);
    const {connect, sendMessage, isConnected, setNodes, setEdges} = useContext(FlowContext);
    useEffect(() => {
        if (!isConnected) return;
        sendMessage(JSON.stringify({prompt}));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isConnected, prompt]);
    const disabled = isConnected || prompt.length === 0;
    return (
        <BaseNode className="flex flex-col gap-2 p-4">
            {activated && <Handle type="source" position={Position.Bottom} id="prompt"/>}
            <CardHeader className="p-0 pb-2">
                <CardTitle>
                    Введите запрос
                </CardTitle>
                <CardDescription>
                    Введите запрос для генераций гипотез.
                </CardDescription>
            </CardHeader>
            <Textarea className="h-32 max-h-40 z-10" disabled={isConnected}
                      value={prompt} onChange={(e) => setPrompt(e.target.value)}
                      placeholder="Введите промпт для генерации гипотез..."/>
            <div className="relative w-full mt-2">
                <GlowEffect
                    colors={['#074709', '#18931b', '#136c13', '#52C755']}
                    opacity={disabled ? 0 : 1}
                    mode='rotate'
                />

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
                        connect(`http://localhost:8000/generate`)
                        // connect(`http://localhost:8000/generate?${new URLSearchParams({prompt}).toString()}`)
                    }}
                    className="w-full relative"
                    disabled={disabled}><Send/>Отправить</Button>
            </div>
        </BaseNode>
    )
}