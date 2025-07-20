import type {Metadata} from "next";
import {Geist, Geist_Mono} from "next/font/google";
import "./globals.css";
import {Toaster} from "@/components/ui/sonner";
import Image from "next/image";
import aiScienceImage from './ai_science.png'

const geistSans = Geist({
    variable: "--font-geist-sans",
    subsets: ["latin"],
});

const geistMono = Geist_Mono({
    variable: "--font-geist-mono",
    subsets: ["latin"],
});

export const metadata: Metadata = {
    title: "Агентная система для решения научных задач",
    description: "Интеллектуальная платформа, где автономные программные агенты совместно решают сложные научные задачи — от моделирования и анализа данных до генерации гипотез и оптимизации экспериментов.",
};

export default function RootLayout({
                                       children,
                                   }: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
        <body
            className={`${geistSans.variable} ${geistMono.variable} antialiased`}
        >
        <Image src={aiScienceImage} alt={"AI Science"} className="fixed top-0 right-0 h-16 w-auto m-2 z-50" />
        {children}
        <Toaster />
        </body>
        </html>
    );
}
