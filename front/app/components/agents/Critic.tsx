import {Button} from "@/components/ui/button";
import {BadgeQuestionMark, MessageCircle, Send, SkipForward} from "lucide-react";
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from "@/components/ui/dialog";
import {Textarea} from "@/components/ui/textarea";
import MarkdownRenderer from "@/components/ui/markdown-renderer";
import {TextShimmerWave} from "@/components/ui/text-shimmer-wave";
import {Dispatch, SetStateAction, useContext, useEffect, useState} from "react";
import {FlowContext} from "@/app/FlowChart";
import {DataType, Hypothesis} from "@/app/components/agents/types";

export default function Critic({data}: { data: DataType & { hyp_index: number } }) {
    const {sendMessage} = useContext(FlowContext)
    const [disabled, setDisabled] = useState(false);
    useEffect(() => {
        setDisabled(false);
    }, [data, setDisabled]);
    if (!data) return (
        <div className="flex gap-2 items-center">
            <BadgeQuestionMark className="size-4"/>
            <TextShimmerWave className='font-mono' duration={1}>
                Критикую гипотезы формулировщика...
            </TextShimmerWave>
        </div>
    );
    return (
        <div className="flex flex-col gap-2">
            {data.output ? data.output.hypotheses_and_critics[data.output.hypotheses_and_critics.length - 1].map(({critique}, i) => (
                <MarkdownRenderer key={i}>{critique}</MarkdownRenderer>
            )) : (
                <>
                    <p className="font-medium text-base">Доступен комментарий к гипотезе {data.hyp_index + 1}!</p>
                    <div className="grid grid-cols-2 w-full gap-2">
                        <CommentDialog data={data as unknown as Hypothesis} disabled={disabled}
                                       setDisabled={setDisabled}/>
                        <Button variant="secondary" disabled={disabled} onClick={() => {
                            sendMessage("")
                            setDisabled(true)
                        }}><SkipForward/> Пропустить</Button>
                    </div>
                </>
            )}
        </div>
    )
}

function CommentDialog({data, disabled, setDisabled}: {
    data: Hypothesis,
    disabled: boolean,
    setDisabled: Dispatch<SetStateAction<boolean>>
}) {
    const [comment, setComment] = useState("");
    const [open, setOpen] = useState(false);
    const {sendMessage} = useContext(FlowContext)
    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button disabled={disabled} onClick={() => setOpen(true)}><MessageCircle/> Добавить</Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>
                        Добавьте комментарий к гипотезе {data.hyp_index + 1}
                    </DialogTitle>
                    <DialogDescription>
                        Это поможет ориентироваться Критику в будущем.
                    </DialogDescription>
                </DialogHeader>
                <div className="flex flex-col gap-4">
                    <div>
                        <h2 className="font-bold text-2xl">Гипотеза:</h2>
                        <MarkdownRenderer>{data.formulation}</MarkdownRenderer>
                    </div>
                    <div>
                        <h2 className="font-bold text-2xl">Критика:</h2>
                        <MarkdownRenderer>{data.critique}</MarkdownRenderer>
                    </div>
                    <div className="flex flex-col gap-2 w-full">
                        <h3 className="font-semibold text-lg">Ваш комментарий:</h3>
                        <Textarea onChange={(e) => setComment(e.target.value)}
                                  placeholder="Введите ваш комментарий... (необязательно)"/>
                        <DialogClose onClick={() => {
                            setDisabled(true)
                            sendMessage(comment)
                        }} disabled={disabled || comment.length === 0}
                                     asChild><Button><Send/> Отправить</Button></DialogClose>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}