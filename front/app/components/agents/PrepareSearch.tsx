import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";
import {DataType} from "@/app/components/agents/types";

export default function PrepareSearch({data}: { data: DataType }) {
    return (
        <div>
            {data ? (
                <p>
                    <b>Запрос поиска:</b> {data.output.current_search_request?.input_query}
                </p>
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