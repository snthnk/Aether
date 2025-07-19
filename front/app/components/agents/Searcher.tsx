import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";
import MarkdownRenderer from "@/components/ui/markdown-renderer";

export default function Searcher({data}: { data: any }) {
    return (
        <div className="flex gap-2 items-center">
            <Search className="size-4"/>
            {data ? (
                <MarkdownRenderer>{data.output.final_report}</MarkdownRenderer>
            ) : (
                <TextShimmerWave className='font-mono' duration={1}>
                    Сжимаю данные поиска...
                </TextShimmerWave>
            )}
        </div>
    );
}