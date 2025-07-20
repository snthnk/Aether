import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import MarkdownRenderer from "@/components/ui/markdown-renderer";
import {Badge} from "@/components/ui/badge";
import {DataType} from "@/app/components/agents/types";

export default function Hypotheses({data}: { data: DataType }) {
    console.log(data);
    return (
        <div>
            {data ? (
                <div className="space-y-4">
                    {data.input.hypotheses_and_critics[data.input.hypotheses_and_critics.length - 1].map(({
                                                                                                              formulation,
                                                                                                              is_approved
                                                                                                          }, i) => (
                        <div key={i}>
                            <h2 className="text-[1.125em] font-semibold">Гипотеза {i + 1}.</h2>
                            <p className="font-medium mb-1">Статус: <Badge
                                variant={is_approved ? "default" : "destructive"}
                                className="ml-1 text-[0.875em]">{is_approved ? "подтверждена" : "опровергнута"}</Badge>
                            </p>
                            <MarkdownRenderer>{formulation}</MarkdownRenderer>
                        </div>
                    ))}
                </div>
            ) : (
                <TextShimmerWave className='font-mono' duration={1}>
                    Окончательная формулировка гипотез...
                </TextShimmerWave>
            )}
        </div>
    );
}