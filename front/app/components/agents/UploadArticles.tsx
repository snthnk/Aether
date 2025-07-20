import {Button} from "@/components/ui/button";
import {useContext, useEffect, useState} from "react";
import {Send, SkipForward, Upload} from "lucide-react";
import {FlowContext} from "@/app/FlowChart";
import {
    FileUpload,
    FileUploadDropzone,
    FileUploadItem,
    FileUploadItemDelete,
    FileUploadItemMetadata,
    FileUploadItemPreview,
    FileUploadItemProgress,
    FileUploadList,
    FileUploadTrigger
} from "@/components/ui/file-upload";
import {toast} from "sonner";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from "@/components/ui/dialog";

export default function UploadArticles() {
    const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
    const {sendMessage} = useContext(FlowContext);

    const [uploadedFilesData, setUploadedFilesData] = useState<{ uuid: string, name: string }[]>([]);

    const [disabled, setDisabled] = useState(false);

    useEffect(() => {
        setUploadedFilesData(prevData =>
            prevData.filter(fileData =>
                uploadedFiles.some(file => file.name === fileData.name)
            )
        );
    }, [uploadedFiles]);
    return (
        <div className="grid grid-cols-2 gap-2 w-full mt-2">
            <Dialog>
                <DialogTrigger asChild>
                    <Button disabled={disabled}><Upload/> Загрузить</Button>
                </DialogTrigger>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>
                            Загрузка документов
                        </DialogTitle>
                        <DialogDescription>
                            Загрузите свои статьи, чтобы уточнить контекст Формулировщику
                        </DialogDescription>
                    </DialogHeader>
                    <FileUpload
                        multiple
                        accept=".pdf"
                        maxFiles={10}
                        maxSize={100 * 1024 * 1024} // 10MB
                        value={uploadedFiles}
                        onValueChange={setUploadedFiles}
                        onUpload={async (
                            files: File[],
                            {onProgress, onSuccess}
                        ) => {
                            try {
                                for (const file of files) {
                                    const formData = new FormData()
                                    formData.append("file", file)

                                    await new Promise<any>((resolve, reject) => {
                                        const xhr = new XMLHttpRequest()

                                        xhr.upload.onprogress = (e) => {
                                            if (e.lengthComputable) {
                                                const progress = (e.loaded / e.total) * 100
                                                onProgress(file, progress)
                                            }
                                        }

                                        xhr.onload = () => {
                                            if (xhr.status >= 200 && xhr.status < 300) {
                                                const responseData = JSON.parse(xhr.responseText);
                                                onSuccess(file)

                                                setUploadedFilesData(prev => [...prev, {
                                                    uuid: responseData.uuid,
                                                    name: file.name
                                                }]);

                                                resolve(responseData)
                                            } else {
                                                reject(new Error(`Upload failed: ${xhr.status}`))
                                            }
                                        }

                                        xhr.onerror = () => reject(new Error('Upload failed'))

                                        xhr.open('POST', 'http://localhost:8000/upload')
                                        xhr.send(formData)
                                    })
                                }
                            } catch (error) {
                                toast.error("Ошибка загрузки файла", {richColors: true})
                                console.error(error)
                            }
                        }}
                        className="w-full"
                    >
                        <FileUploadDropzone className="w-full">
                            <div className="flex flex-col items-center gap-2">
                                <Upload className="h-8 w-8 text-muted-foreground"/>
                                <div className="text-center">
                                    <p className="text-sm font-medium">
                                        Перетащите файлы сюда или нажмите для выбора
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        Поддерживаются: .pdf (до 100MB)
                                    </p>
                                </div>
                                <FileUploadTrigger asChild>
                                    <Button variant="outline" size="sm">
                                        Выберите файлы
                                    </Button>
                                </FileUploadTrigger>
                            </div>
                        </FileUploadDropzone>

                        <FileUploadList className="max-h-40 overflow-y-auto">
                            {uploadedFiles.map((file) => (
                                <FileUploadItem key={file.name} value={file}>
                                    <FileUploadItemPreview/>
                                    <FileUploadItemMetadata/>
                                    <FileUploadItemDelete asChild>
                                        <Button variant="ghost" size="sm">
                                            ×
                                        </Button>
                                    </FileUploadItemDelete>
                                    <FileUploadItemProgress/>
                                </FileUploadItem>
                            ))}
                        </FileUploadList>
                    </FileUpload>

                    {uploadedFiles.length > 0 && (
                        <div className="text-sm text-muted-foreground">
                            Загружено файлов: {uploadedFiles.length}
                        </div>
                    )}
                    <Button disabled={disabled || uploadedFiles.length === 0} onClick={() => {
                        setDisabled(true);
                        sendMessage(JSON.stringify({
                            type: 'upload_files',
                            files: uploadedFilesData
                        }));
                    }}><Send/> Отправить</Button>
                </DialogContent>
            </Dialog>
            <Button variant="secondary" disabled={disabled} onClick={() => {
                setDisabled(true)
                sendMessage(JSON.stringify({
                    type: 'skip_upload'
                }))
            }}><SkipForward/> Пропустить</Button>
        </div>
    );
}