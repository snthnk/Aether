import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {BadgeQuestionMark} from "lucide-react";

export default function Critic({data}: { data: boolean | null }) {
    return (
        <div className="flex gap-2 items-center">
            <BadgeQuestionMark className="size-4 text-muted-foreground"/>
            {data !== null ? (
                <p>Вердикт: <b
                    className={`${data ? "text-green-600" : "text-destructive"}`}>{data ? "OK" : "проверить ещё раз"}</b>
                </p>
            ) : (
                <TextShimmerWave className='font-mono text-xs' duration={1}>
                    Критикую гипотезу Формулировщика...
                </TextShimmerWave>
            )}
        </div>
    )
}