import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";

export default function Hypotheses({data}: { data: any }) {
    return (
        <div className="text-xs">
            {data ? (
                <>
                    <p className="font-medium">Гипотезы:</p>
                    <div className="space-y-4">
                        {data.input.hypotheses_and_critics[data.input.hypotheses_and_critics.length - 1].map(({formulation}, i) => (
                            <p key={i}><b className="text-sm">{i + 1}.</b> {formulation}</p>
                        ))}
                    </div>
                </>
            ) : (
                <TextShimmerWave className='font-mono' duration={1}>
                    Окончательная формулировка гипотез...
                </TextShimmerWave>
            )}
        </div>
    );
}