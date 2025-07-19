import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";

export default function ArxivSearcher({data}: { data: any }) {
    return (
        <div className="flex gap-2 items-center text-muted-foreground text-xs">
            <Search className="size-4"/>
            <div>
                {data ? (
                    <p className='font-mono'>
                        Найдено <b>{data.output.papers.length}</b> статей в Arxiv</p>
                ) : (
                    <TextShimmerWave className='font-mono' duration={1}>
                        Ищу статьи в Arxiv...
                    </TextShimmerWave>
                )}
            </div>
        </div>
    );
}