import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {BadgeQuestionMark, Search} from "lucide-react";

export default function QueryRefiner({data}: { data: any }) {
    return (
        <div className="flex gap-2 items-center text-muted-foreground text-xs">
            <BadgeQuestionMark className="size-4"/>
            {data ? (
                <p className='font-mono'>
                    Найдено <b>{data.output.papers.length}</b> статей в OpenAlex</p>
            ) : (
                <TextShimmerWave className='font-mono' duration={1}>
                    Ищу статьи в OpenAlex...
                </TextShimmerWave>
            )}
        </div>
    );
}