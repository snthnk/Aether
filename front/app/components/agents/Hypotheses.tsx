import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";

export default function Hypotheses({data}: { data: string[] | null }) {
    return (
        <div>
            {data ? (
                <>
                    <p className="font-medium">Гипотезы:</p>
                    <div className="max-h-64 space-y-4 text-xs overflow-y-auto">
                        {data.map((hp, i) => (
                            <p key={i}><b className="text-sm">{i + 1}.</b> {hp}</p>
                        ))}
                    </div>
                </>
            ) : (
                <TextShimmerWave className='font-mono text-xs' duration={1}>
                    Окончательная формулировка гипотез...
                </TextShimmerWave>
            )}
        </div>
    );
}