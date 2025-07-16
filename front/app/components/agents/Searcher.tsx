import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";

export default function Searcher({data}: { data: number | null }) {
    return (
        <div className="flex gap-2 items-center text-muted-foreground">
            <Search className="size-4"/>
            {data ? (
                <p className='font-mono text-xs text-muted-foreground'>
                    Найдено <b>{data}</b> статей в OpenAlex</p>
            ) : (
                <TextShimmerWave className='font-mono text-xs' duration={1}>
                    Ищу статьи в Интернете...
                </TextShimmerWave>
            )}
        </div>
    );
}