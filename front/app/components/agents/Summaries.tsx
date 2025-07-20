import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Package} from "lucide-react";
import {DataType} from "@/app/components/agents/types";

export default function Summaries({data}: { data: DataType }) {
    return (
        <div className="flex gap-2 items-center text-muted-foreground">
            {data ? (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <Package className="size-4"/>
                        <p className='font-mono'>
                            Суммаризировано <b>{data.output.summaries.length}</b> статей</p>
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {data.output.summaries.map((summary, i) => (
                            <a
                                className="bg-muted flex items-center gap-1 p-1 font-semibold rounded-full text-[0.75em]"
                                href={summary.source}
                                target="_blank"
                                key={i}>
                                {summary.title.slice(0, 20)+"..."}
                            </a>
                        ))}
                    </div>
                </div>
            ) : (
                <>
                    <Package className="size-4"/>
                    <TextShimmerWave className='font-mono' duration={1}>
                        Суммаризирую статьи...
                    </TextShimmerWave>
                </>
            )}
        </div>
    );
}