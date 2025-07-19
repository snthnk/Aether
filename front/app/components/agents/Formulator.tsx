import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import MarkdownRenderer from "@/components/ui/markdown-renderer";
import {Badge} from "@/components/ui/badge";

export default function Formulator({data}: { data: any }) {
    return (
        <div className="flex flex-col gap-2 items-center">
            {data ? (
                <div className="space-y-4">
                    {data.output.hypotheses_and_critics[data.output.hypotheses_and_critics.length - 1].map(({formulation}: {
                        formulation: string
                    }, i) => (
                        <div key={i}>
                            <h2 className="text-[1.125em] font-semibold">Гипотеза {i + 1}.</h2>
                            <p className="font-medium mb-1">Статус: <Badge
                                variant={"secondary"}
                                className="ml-1 text-[0.875em]">требует подтверждения Критиком</Badge></p>
                            <MarkdownRenderer>{formulation}</MarkdownRenderer>
                        </div>
                    ))}
                </div>
            ) : (
                <TextShimmerWave className='font-mono' duration={1}>
                    Формулирую гипотезы...
                </TextShimmerWave>
            )}
        </div>
    )
}