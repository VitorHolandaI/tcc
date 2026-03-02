import { useEffect, useRef, useState } from 'react';
import { editor } from 'monaco-editor';

export interface KeystrokeEvent {
    key: string;
    timestamp: string;
    application: string;
    flight_time: number | null;
    hold_time: number | null;
    command_type: string | null;
}

export const useKeystrokeCapture = (
    editorInstance: editor.IStandaloneCodeEditor | null
) => {
    const [keystrokeEvents, setKeystrokeEvents] = useState<KeystrokeEvent[]>([]);
    const lastKeyTimeRef = useRef<number | null>(null);
    const keyPressTimesRef = useRef<Map<string, number>>(new Map());
    const modifiersRef = useRef({
        ctrl: false,
        alt: false,
        shift: false,
        meta: false
    });

    useEffect(() => {
        if (!editorInstance) return;

        // Handler para keydown
        const keydownDisposable = editorInstance.onKeyDown((e) => {
            const currentTime = Date.now() / 1000; // segundos
            const key = getKeyString(e);

            // Atualizar modifiers
            if (e.ctrlKey || e.metaKey) modifiersRef.current.ctrl = true;
            if (e.altKey) modifiersRef.current.alt = true;
            if (e.shiftKey) modifiersRef.current.shift = true;

            // Calcular flight_time
            let flight_time: number | null = null;
            if (lastKeyTimeRef.current !== null) {
                flight_time = currentTime - lastKeyTimeRef.current;
            }

            // Detectar command_type
            const command_type = detectCommandType(e, key);

            // Armazenar timestamp de press
            keyPressTimesRef.current.set(key, currentTime);

            // Criar evento (hold_time será adicionado no keyup)
            const event: KeystrokeEvent = {
                key,
                timestamp: new Date().toISOString().replace('T', ' ').substring(0, 23),
                application: 'Browser',
                flight_time: flight_time ? parseFloat(flight_time.toFixed(3)) : null,
                hold_time: null, // será preenchido no keyup
                command_type
            };

            //console.log('Keystroke captured:', event);

            setKeystrokeEvents(prev => [...prev, event]);
            lastKeyTimeRef.current = currentTime;
        });

        // Handler para keyup
        const keyupDisposable = editorInstance.onKeyUp((e) => {
            const currentTime = Date.now() / 1000;
            const key = getKeyString(e);

            // Atualizar modifiers
            if (!e.ctrlKey && !e.metaKey) modifiersRef.current.ctrl = false;
            if (!e.altKey) modifiersRef.current.alt = false;
            if (!e.shiftKey) modifiersRef.current.shift = false;

            // Calcular hold_time
            const pressTime = keyPressTimesRef.current.get(key);
            if (pressTime) {
                const hold_time = currentTime - pressTime;

                // Atualizar último evento com hold_time
                setKeystrokeEvents(prev => {
                    const newEvents = [...prev];
                    const lastEvent = newEvents[newEvents.length - 1];
                    if (lastEvent && lastEvent.key === key && lastEvent.hold_time === null) {
                        lastEvent.hold_time = parseFloat(hold_time.toFixed(3));
                    }
                    return newEvents;
                });

                keyPressTimesRef.current.delete(key);
            }
        });

        return () => {
            keydownDisposable.dispose();
            keyupDisposable.dispose();
        };
    }, [editorInstance]);

    const clearEvents = () => {
        setKeystrokeEvents([]);
        lastKeyTimeRef.current = null;
        keyPressTimesRef.current.clear();
    };

    return { keystrokeEvents, clearEvents };
};

// Helper functions
function getKeyString(e: editor.IKeyboardEvent): string {
    const key = e.browserEvent.key;

    // Detectar combinações
    if (e.ctrlKey || e.metaKey) {
        if (key === 'v') return 'ctrl+v';
        if (key === 'c') return 'ctrl+c';
        if (key === 'x') return 'ctrl+x';
        if (key === 'z') return 'ctrl+z';
        if (key === 'y') return 'ctrl+y';
        if (key === 's') return 'ctrl+s';
        return `ctrl+${key}`;
    }

    return key;
}

function detectCommandType(e: editor.IKeyboardEvent, key: string): string | null {
    // Paste
    if ((e.ctrlKey || e.metaKey) && e.browserEvent.key === 'v') {
        return 'paste';
    }

    // Copy
    if ((e.ctrlKey || e.metaKey) && e.browserEvent.key === 'c') {
        return 'copy';
    }

    // Cut
    if ((e.ctrlKey || e.metaKey) && e.browserEvent.key === 'x') {
        return 'cut';
    }

    // Backspace
    if (e.browserEvent.key === 'Backspace') {
        return 'backspace';
    }

    // Cursor movement
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'PageUp', 'PageDown'].includes(e.browserEvent.key)) {
        return 'cursor_movement';
    }

    return null;
}
