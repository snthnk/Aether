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
import {useContext, useState} from "react";
import {FlowContext} from "@/app/FlowChart";

export default function Critic({data}: { data: any }) {
    const {sendMessage} = useContext(FlowContext)
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
            {data.output ? data.output.hypotheses_and_critics[data.output.hypotheses_and_critics.length - 1].map(({critique}: {
                critique: string
            }, i) => (
                <MarkdownRenderer key={i}>{critique}</MarkdownRenderer>
            )) : (
                <>
                    <p className="font-medium text-base">Доступен комментарий!</p>
                    <div className="flex w-full gap-2">
                        <CommentDialog data={data}/>
                        <Button variant="secondary" onClick={() => sendMessage("")}><SkipForward/> Пропустить</Button>
                    </div>
                </>
            )}
        </div>
    )
}

function CommentDialog({data}: { data: any }) {
    const [comment, setComment] = useState("");
    const [open, setOpen] = useState(false);
    const {sendMessage} = useContext(FlowContext)
    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button onClick={() => setOpen(true)}><MessageCircle/> Добавить</Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>
                        Добавьте комментарий
                    </DialogTitle>
                    <DialogDescription>
                        Это поможет ориентироваться Критику в будущем.
                    </DialogDescription>
                </DialogHeader>
                <div className="flex flex-col gap-4">
                    <div>
                        <h3 className="font-semibold text-lg">Гипотеза:</h3>
                        <p>{data.formulation}</p>
                    </div>
                    <div>
                        <h3 className="font-semibold text-lg">Критика:</h3>
                        <p>{data.critique}</p>
                    </div>
                    <div className="flex flex-col w-full">
                        <h3 className="font-semibold text-lg">Ваш комментарий:</h3>
                        <Textarea onChange={(e) => setComment(e.target.value)}
                                  placeholder="Введите ваш комментарий... (необязательно)"/>
                        <DialogClose onClick={() => sendMessage(comment)}><Send/> Отправить</DialogClose>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}