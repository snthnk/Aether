import {Button} from "@/components/ui/button";
import {useContext, useState} from "react";
import {Play, SkipForward, Upload} from "lucide-react";
import {FlowContext} from "@/app/FlowChart";
import {
    FileUpload,
    FileUploadDropzone,
    FileUploadItem,
    FileUploadItemDelete,
    FileUploadItemMetadata,
    FileUploadItemPreview,
    FileUploadList,
    FileUploadTrigger
} from "@/components/ui/file-upload";

export default function UploadArticles() {
    const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
    const {sendMessage} = useContext(FlowContext);

    const handleFilesChange = (files: File[]) => {
        setUploadedFiles(files);
    };

    // const handleContinue = async () => {
    //     if (uploadedFiles.length > 0) {
    //         // Convert files to binary data
    //         const filesData = await Promise.all(
    //             uploadedFiles.map(async (file) => {
    //                 const arrayBuffer = await file.arrayBuffer();
    //                 return {
    //                     name: file.name,
    //                     type: file.type,
    //                     size: file.size,
    //                     data: new Uint8Array(arrayBuffer)
    //                 };
    //             })
    //         );
    //
    //         sendMessage({
    //             type: 'files',
    //             files: filesData
    //         });
    //     } else {
    //         // Skip - send empty message or handle skip logic
    //         sendMessage({
    //             type: 'skip'
    //         });
    //     }
    // };

    return (
        <div className="flex flex-col w-full gap-4 items-center">
            <p className="font-medium">Загрузите свои файлы!</p>
            <FileUpload
                multiple
                accept=".pdf,.doc,.docx,.txt,.md"
                maxFiles={10}
                maxSize={10 * 1024 * 1024} // 10MB
                onValueChange={handleFilesChange}
                className="w-full max-w-md"
            >
                <FileUploadDropzone className="w-full">
                    <div className="flex flex-col items-center gap-2">
                        <Upload className="h-8 w-8 text-muted-foreground"/>
                        <div className="text-center">
                            <p className="text-sm font-medium">
                                Перетащите файлы сюда или нажмите для выбора
                            </p>
                            <p className="text-xs text-muted-foreground">
                                Поддерживаются: PDF, DOC, DOCX, TXT, MD (до 10MB)
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
                        </FileUploadItem>
                    ))}
                </FileUploadList>
            </FileUpload>

            {uploadedFiles.length > 0 && (
                <div className="text-sm text-muted-foreground">
                    Загружено файлов: {uploadedFiles.length}
                </div>
            )}

            <Button
                variant={uploadedFiles.length ? "default" : "secondary"}
                // onClick={handleContinue}
                onClick={() => sendMessage("")}
                className="w-full max-w-md"
            >
                {uploadedFiles.length ? (
                    <><Play className="mr-2 h-4 w-4"/> Продолжить</>
                ) : (
                    <><SkipForward className="mr-2 h-4 w-4"/> Пропустить</>
                )}
            </Button>
        </div>
    );
}