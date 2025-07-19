import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";

export default function SearchReport({data}: { data: any }) {
    return (
        <div className="flex gap-2 items-center text-muted-foreground text-xs">
            <Search className="size-4"/>
            {data ? (
                <p>{data.output.final_report}</p>
            ) : (
                <TextShimmerWave className='font-mono' duration={1}>
                    Пишу отчет по поиску...
                </TextShimmerWave>
            )}
        </div>
    );
}