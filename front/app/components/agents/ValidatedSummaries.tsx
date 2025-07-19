import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";

export default function ValidatedSummaries({data}: { data: any }) {
    return (
        <div className="flex gap-2 items-center text-muted-foreground text-xs">
            <Search className="size-4"/>
            <div>
                {data ? data.output.validated_summaries.map(({source}, i) => (
                    <p key={i}><b>{i + 1}.</b> {source}</p>
                )) : (
                    <TextShimmerWave className='font-mono' duration={1}>
                        Валидирую резюме статей...
                    </TextShimmerWave>
                )}
            </div>
        </div>
    );
}