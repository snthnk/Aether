import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {GitBranch} from "lucide-react";

export default function Orchestrator() {
    return (
        <div className="flex gap-2 items-center text-muted-foreground">
            <GitBranch/>
            <TextShimmerWave className='font-mono text-xs' duration={1}>
                Распределяю задачи между агентами...
            </TextShimmerWave>
        </div>
    );
}