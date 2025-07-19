import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";

export default function Formulator({data}: { data: any }) {
    return (
        <div className="flex flex-col gap-2 items-center text-muted-foreground text-xs">
            {data ? data.output.hypotheses_and_critics[data.output.hypotheses_and_critics.length-1].map(({formulation}: {formulation: string}, i) => (
                <p key={i}><b>{i + 1}.</b> {formulation}</p>
            )) : (
                <TextShimmerWave className='font-mono' duration={1}>
                    Формулирую гипотезы...
                </TextShimmerWave>
            )}
        </div>
    )
}