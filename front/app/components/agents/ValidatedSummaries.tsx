import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {ListChecks} from "lucide-react";
import {Badge} from "@/components/ui/badge";
import {DataType} from "@/app/components/agents/types";

export default function ValidatedSummaries({data}: { data: DataType }) {
    return (
        <div className="flex gap-2 items-center text-muted-foreground">
            {data ? (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <ListChecks className="size-4"/>
                        <p className='font-mono'>
                            Прошли
                            проверку <b>{data.output.validated_summaries.length} из {data.output.summaries.length}</b> статей
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {data.output.validated_summaries.map((summary, i) => (
                            <Badge key={i} asChild>
                                <a
                                    className="text-[0.75em] !rounded-full"
                                    href={summary.source}
                                    target="_blank">
                                    {summary.title.slice(0, 20) + "..."}
                                </a>
                            </Badge>
                        ))}
                        {data.output.summaries
                            .filter(sum => !new Set(data.output.validated_summaries.map(vs => vs.title)).has(sum.title))
                            .map((summary, i) => (
                                <Badge variant="destructive" key={i} asChild>
                                    <a
                                        className="text-[0.75em] !rounded-full"
                                        href={summary.source}
                                        target="_blank"
                                    >
                                        {summary.title.slice(0, 20) + "..."}
                                    </a>
                                </Badge>
                            ))}
                    </div>
                </div>
            ) : (
                <>
                    <ListChecks className="size-4"/>
                    <TextShimmerWave className='font-mono' duration={1}>
                        Валидирую резюме статей...
                    </TextShimmerWave>
                </>
            )}
        </div>
    );
}