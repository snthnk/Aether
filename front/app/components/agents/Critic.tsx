import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {BadgeQuestionMark} from "lucide-react";

export default function Formulator({data}: { data: any }) {
    return (
        <div className="flex gap-2 items-center text-muted-foreground text-xs">
            <BadgeQuestionMark className="size-4 text-muted-foreground"/>
            <div>
                {data ? data.output.hypotheses_and_critics[data.output.hypotheses_and_critics.length - 1].map(({critique}: {
                    critique: string
                }, i) => (
                    <p key={i}><b>{i + 1}.</b> {critique}</p>
                )) : (
                    <TextShimmerWave className='font-mono' duration={1}>
                        Критикую гипотезы формулировщика...
                    </TextShimmerWave>
                )}
            </div>
        </div>
    )
}