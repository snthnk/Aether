import {useCallback, useRef, useState} from 'react';

interface UseSSEOptions {
    onOpen?: (event: Event) => void;
    onMessage?: (data: Record<string, string>, event: MessageEvent) => void;
    onError?: (error: Event) => void;
    withCredentials?: boolean;
    enabled?: boolean;
}

interface UseSSEReturn {
    connect: (url: string) => void;
    data: Record<string, string>|null;
    error: Event | Error | null;
    isConnected: boolean;
    disconnect: () => void;
}

const useSSE = (options: UseSSEOptions = {}): UseSSEReturn => {
    const [data, setData] = useState<UseSSEReturn["data"]>(null);
    const [error, setError] = useState<Event | Error | null>(null);
    const [isConnected, setIsConnected] = useState<boolean>(false);
    const eventSourceRef = useRef<EventSource | null>(null);

    const {
        onOpen,
        onMessage,
        onError,
        withCredentials = false,
        enabled = true,
    } = options;

    const connect = useCallback((url: string): void => {
        if (!enabled || !url) return;

        // Clean up any existing connection first
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }

        try {
            const eventSource = new EventSource(url, {withCredentials});
            eventSourceRef.current = eventSource;

            eventSource.onopen = (event: Event): void => {
                setIsConnected(true);
                setError(null);
                onOpen?.(event);
            };

            eventSource.onmessage = (event: MessageEvent): void => {
                try {
                    const parsedData = JSON.parse(event.data);
                    setData(parsedData);
                    onMessage?.(parsedData, event);
                } catch {
                    setData(event.data);
                    onMessage?.(event.data, event);
                }
            };

            eventSource.onerror = (event: Event): void => {
                setIsConnected(false);
                setError(event);
                onError?.(event);
                eventSource.close();
                eventSourceRef.current = null;
            };

        } catch (err) {
            setError(err as Error);
            setIsConnected(false);
        }
    }, [enabled, onOpen, onMessage, onError, withCredentials]);

    const disconnect = (): void => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }

        setIsConnected(false);
    };

    return {
        connect,
        data,
        error,
        isConnected,
        disconnect,
    };
};

export default useSSE;
