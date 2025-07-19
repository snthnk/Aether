import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";

export default function PrepareSearch({data}: { data: any }) {
    return (
        <div className="flex gap-2 items-center text-muted-foreground text-xs">
            <Search className="size-4"/>
            <div>
                {data ? data.output.current_search_request.search_queries.map((query, i) => (
                    <p key={i}>
                        {query}
                    </p>
                )) : (
                    <TextShimmerWave className='font-mono' duration={1}>
                        Формулирование запроса поиска...
                    </TextShimmerWave>
                )}
            </div>
        </div>
    );
}