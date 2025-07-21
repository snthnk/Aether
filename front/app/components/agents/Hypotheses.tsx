import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import MarkdownRenderer from "@/components/ui/markdown-renderer";
import {Badge} from "@/components/ui/badge";

type Replacements = {
    tag: string
    title: string
    link: string
}[]


function replaceReferenceTags(markdown: string, references: Replacements): string {
    return references.reduce((text, {tag, title, link}) => {
        const escapedTag = tag.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(escapedTag, 'g');
        const replacement = `[${title}](${link})`;
        return text.replace(regex, replacement);
    }, markdown);
}

export default function Hypotheses({data}: {
    data: {
        output: {
            hypotheses: {
                hypothesis: string
                is_approved: boolean
                critique: {
                    summary: string
                    recommendations: string
                }
                tags: Replacements
            }[]
        }
    }
}) {
    console.log(data);
    try {
        return (
            <div>
                {data ? (
                    <div className="space-y-8">
                        {data.output.hypotheses.map(({
                                                         hypothesis,
                                                         critique,
                                                         tags,
                                                         is_approved
                                                     }, i) => (
                            <div key={i}>
                                <h1 className="text-[1.25em] font-semibold">Гипотеза {i + 1}.</h1>
                                <p className="font-medium mb-1">Статус: <Badge
                                    variant={is_approved ? "default" : "destructive"}
                                    className="ml-1 text-[0.875em]">{is_approved ? "подтверждена" : "опровергнута"}</Badge>
                                </p>
                                <MarkdownRenderer>{replaceReferenceTags(hypothesis, tags.map(t => ({
                                    ...t,
                                    title: `${t.title.slice(0, 30)}...`
                                })))}</MarkdownRenderer>
                                <h1 className="text-[1.25em] font-semibold mt-4">Критика к гипотезе {i + 1}.</h1>
                                <div className="mb-4">
                                    <h2 className="font-semibold text-[1.125em]">Сводка:</h2>
                                    <MarkdownRenderer>{critique.summary}</MarkdownRenderer>
                                </div>
                                <div className="mb-4">
                                    <h3 className="font-semibold text-[1.125em]">Рекоммендации:</h3>
                                    <MarkdownRenderer>{critique.recommendations}</MarkdownRenderer>
                                </div>
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
    } catch (e) {
        console.log(e);
        return null
    }
}