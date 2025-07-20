import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";
import MarkdownRenderer from "@/components/ui/markdown-renderer";
import {DataType} from "@/app/components/agents/types";

export default function Searcher({data}: { data: DataType }) {
    return (
        <div className="flex gap-2 items-center">
            <Search className="size-4"/>
            {data ? (
                <MarkdownRenderer>{data.output.final_report!}</MarkdownRenderer>
            ) : (
                <TextShimmerWave className='font-mono' duration={1}>
                    Сжимаю данные поиска...
                </TextShimmerWave>
            )}
        </div>
    );
}