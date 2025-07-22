'use client'

import {DotLottie, DotLottieReact} from "@lottiefiles/dotlottie-react";
import {useState} from "react";

export default function Logo() {
    const [dotLottie, setDotLottie] = useState<DotLottie | null>(null)
    return (
        <DotLottieReact
            src="/logo.lottie"
            className="fixed top-0 right-0 size-48 overflow-hidden z-10 flex justify-center"
            speed={1.25}
            dotLottieRefCallback={setDotLottie}
            onMouseEnter={() => {
                dotLottie?.setLoop(true)
                dotLottie?.play()
            }}
            onMouseLeave={() => dotLottie?.setLoop(false)}
            loop
        />
    );
}