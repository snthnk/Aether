import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";

export default function Formulator({data}: { data: string | null }) {
    return (
        <div className="flex gap-2 items-center">
            {data ? (
                <div>
                    <p className="font-medium">Сформулирована гипотеза:</p>
                    <div className="max-h-22 text-xs overflow-y-auto">
                        <p>{data}</p>
                    </div>
                </div>
            ) : (
                <>
                    <TextShimmerWave className='font-mono text-xs' duration={1}>
                        Формулирую гипотезу...
                    </TextShimmerWave>
                </>
            )}
        </div>
    )
}