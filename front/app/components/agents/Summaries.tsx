import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";

export default function Summaries({data}: { data: any }) {
    return (
        <div className="flex gap-2 items-center text-muted-foreground text-xs">
            <Search className="size-4"/>
            <div>
                {data ? data.output.summaries.map(({source}, i) => (
                    <p key={i}><b>{i + 1}.</b> {source}</p>
                )) : (
                    <TextShimmerWave className='font-mono' duration={1}>
                        Создаю резюме статей...
                    </TextShimmerWave>
                )}
            </div>
        </div>
    );
}