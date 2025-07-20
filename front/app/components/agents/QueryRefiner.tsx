import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {BadgeQuestionMark} from "lucide-react";
import {DataType} from "@/app/components/agents/types";

export default function QueryRefiner({data}: { data: DataType }) {
    return (
        <div className="flex gap-2 items-center  ">
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