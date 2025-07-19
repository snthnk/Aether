import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Search} from "lucide-react";

export default function ArxivSearcher({data}: { data: any }) {
    return (
        <div className="flex items-center gap-2 text-muted-foreground">
            {data ? (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <Search className="size-4"/>
                        <p className='font-mono'>
                            Найдено <b>{data.output.papers.length}</b> статей в arXiv</p>
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {data.output.papers.map((paper, i) => (
                            <a
                                className="bg-muted flex items-center gap-1 p-1 font-semibold rounded-full text-[0.75em]"
                                href={paper.id}
                                target="_blank"
                                key={i}>
                                {paper.title.slice(0, 20)+"..."}
                            </a>
                        ))}
                    </div>
                </div>
            ) : (
                <>
                    <Search className="size-4"/>
                    <TextShimmerWave className='font-mono' duration={1}>
                        Ищу статьи в arXiv...
                    </TextShimmerWave>
                </>
            )}
        </div>
    );
}