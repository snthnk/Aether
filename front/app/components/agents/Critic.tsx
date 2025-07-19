import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {BadgeQuestionMark} from "lucide-react";
import MarkdownRenderer from "@/components/ui/markdown-renderer";

export default function Formulator({data}: { data: any }) {
    return (
        <div className="flex flex-col gap-8">
                {data ? data.output.hypotheses_and_critics[data.output.hypotheses_and_critics.length - 1].map(({critique}: {
                    critique: string
                }, i) => (
                    <MarkdownRenderer key={i}>{critique}</MarkdownRenderer>
                )) : (
                    <div className="flex gap-2 items-center">
                        <BadgeQuestionMark className="size-4"/>
                        <TextShimmerWave className='font-mono' duration={1}>
                            Критикую гипотезы формулировщика...
                        </TextShimmerWave>
                    </div>
                )}
        </div>
    )
}