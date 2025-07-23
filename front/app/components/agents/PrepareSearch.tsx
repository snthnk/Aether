import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";
import {DataType} from "@/app/components/agents/types";

export default function PrepareSearch({data}: { data: DataType }) {
    return (
        <div>
            {data ? (
                <>
                    <h2 className="text-[1.25em] font-medium mb-2">Перевод запроса поиска:</h2>
                    <code>{data.output.current_search_request?.input_query}</code>
                </>
            ) : (
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