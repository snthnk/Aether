import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";
import MarkdownRenderer from "@/components/ui/markdown-renderer";
import {DataType} from "@/app/components/agents/types";

export default function SearchReport({data}: { data: DataType }) {
    return (
        <div className="flex gap-2 items-center">
            {data ? (
                <MarkdownRenderer>{data.output.final_report!}</MarkdownRenderer>
            ) : (
                <>
                    <Search className="size-4"/>
                    <TextShimmerWave className='font-mono' duration={1}>
                        Пишу отчет по поиску...
                    </TextShimmerWave>
                </>
            )}
        </div>
    );
}