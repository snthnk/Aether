import {useEffect, useRef, useState} from 'react';

interface UseWebSocketReturn {
    lastMessage: Record<string, string> | null;
    connect: (url: string) => void;
    sendMessage: (message: string) => void;
    isConnected: boolean;
}

const useWebSocket = ({onError}: { onError: () => void }): UseWebSocketReturn => {
    const [lastMessage, setLastMessage] = useState<Record<string, string> | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const websocketRef = useRef<WebSocket | null>(null);

    const connect = (url: string) => {
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
            websocketRef.current.close();
        }

        const ws = new WebSocket(url);
        websocketRef.current = ws;

        ws.onopen = () => setIsConnected(true);
        ws.onclose = () => setIsConnected(false);
        ws.onerror = () => {
            onError();
            setIsConnected(false);
        };
        ws.onmessage = (event) => setLastMessage(JSON.parse(event.data));
    };

    const sendMessage = (message: string) => {
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
            websocketRef.current.send(message);
        }
    };

    useEffect(() => {
        return () => {
            websocketRef.current?.close();
        };
    }, []);

    return {
        lastMessage,
        connect,
        sendMessage,
        isConnected,
    };
};

export default useWebSocket;