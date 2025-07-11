import {useRef, useState} from "react";
import {Handle, Position, useReactFlow} from "@xyflow/react";
import {Textarea} from "@/components/ui/textarea";
import {Button} from "@/components/ui/button";
import {Send} from "lucide-react";
import {BaseNode} from "@/components/base-node";
import useFlowStore from "@/app/store";
import nodes from "@/app/chartElements/nodes";

export const PromptField = () => {
    const {fitView} = useReactFlow()
    const {currentStep, setCurrentStep, increaseStep} = useFlowStore()
    const [disabled, setDisabled] = useState(false);
    const ref = useRef<number>(0);
    return (
        <BaseNode className="flex flex-col gap-2 p-4">
            {currentStep >= 1 && <Handle type="source" position={Position.Bottom} id="prompt"/>}
            <Textarea className="h-32 max-h-40" disabled={disabled}
                      placeholder="Введите промпт для генерации гипотез..."/>
            <Button onClick={async () => {
                setCurrentStep(0);
                setDisabled(true);
                ref.current = 0;

                const int = setInterval(async () => {
                    increaseStep();
                    ref.current += 1;
                    if (ref.current >= nodes.length) return;
                    await fitView({duration: 500, padding: 0.4, nodes: [nodes[ref.current], nodes[ref.current - 1]]})
                }, 1000)

                setTimeout(async () => {
                    clearInterval(int);
                    setDisabled(false);
                    await fitView({duration: 500})
                }, 11000)

            }} disabled={disabled}><Send/> Отправить</Button>
        </BaseNode>
    )
}