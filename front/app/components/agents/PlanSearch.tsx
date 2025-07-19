import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";

export default function PlanSearch({data}: { data: any }) {
    return (
        <div className="text-muted-foreground flex flex-wrap gap-1">
            {data ? data.output.current_search_request.search_queries.map((query, i) => (
                <div className="bg-muted flex items-center gap-1 p-1 font-semibold rounded-full text-[0.75em]" key={i}>
                    <Search className="size-3"/> {query}
                </div>
            )) : (
                <div className="flex gap-2 items-center">
                    <Search className="size-4"/>
                    <TextShimmerWave className='font-mono' duration={1}>
                        Формулирование запроса поиска...
                    </TextShimmerWave>
                </div>
            )}
        </div>
    );
}