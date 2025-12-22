/**
 * Wake Word Detector Component
 * 
 * Listens for "Hey Wizard" or "Hey Form" to activate voice input.
 * Uses Web Speech API in continuous mode.
 * 
 * Features:
 * - Always-on listening (low power)
 * - Visual indicator when ready
 * - Customizable wake phrase
 * - Debouncing to prevent false activations
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Volume2, VolumeX, Loader2 } from 'lucide-react';

// Wake phrases to detect
const WAKE_PHRASES = [
    'hey wizard',
    'hey form',
    'ok wizard',
    'hello wizard',
    'hi wizard'
];

const WakeWordDetector = ({
    onActivate,
    enabled = true,
    onStatusChange
}) => {
    const [isListening, setIsListening] = useState(false);
    const [isSupported, setIsSupported] = useState(false);
    const [status, setStatus] = useState('idle'); // idle, listening, activated, error
    const [lastHeard, setLastHeard] = useState('');

    const recognitionRef = useRef(null);
    const debounceRef = useRef(null);
    const cooldownRef = useRef(false);

    // Check browser support
    useEffect(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        setIsSupported(!!SpeechRecognition);
    }, []);

    // Initialize continuous recognition
    useEffect(() => {
        if (!isSupported || !enabled) return;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();

        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            setIsListening(true);
            setStatus('listening');
            onStatusChange?.('listening');
        };

        recognition.onend = () => {
            // Auto-restart if still enabled
            if (enabled && !cooldownRef.current) {
                setTimeout(() => {
                    try {
                        recognition.start();
                    } catch (e) {
                        // Ignore - might already be running
                    }
                }, 100);
            }
        };

        recognition.onerror = (event) => {
            console.warn('Wake word recognition error:', event.error);

            if (event.error === 'not-allowed') {
                setStatus('error');
                onStatusChange?.('error');
            }
        };

        recognition.onresult = (event) => {
            // Get the latest result
            const lastResult = event.results[event.results.length - 1];
            const transcript = lastResult[0].transcript.toLowerCase().trim();

            setLastHeard(transcript);

            // Check for wake phrase
            const detected = WAKE_PHRASES.some(phrase =>
                transcript.includes(phrase)
            );

            if (detected && !cooldownRef.current) {
                // Wake phrase detected!
                cooldownRef.current = true;
                setStatus('activated');
                onStatusChange?.('activated');

                // Stop listening temporarily
                recognition.stop();

                // Call activation callback
                onActivate?.();

                // Cooldown to prevent rapid re-activation
                setTimeout(() => {
                    cooldownRef.current = false;
                    setStatus('listening');

                    // Restart listening
                    try {
                        recognition.start();
                    } catch (e) {
                        // Ignore
                    }
                }, 3000);
            }
        };

        recognitionRef.current = recognition;

        // Start listening
        try {
            recognition.start();
        } catch (e) {
            console.warn('Could not start wake word detection:', e);
        }

        return () => {
            recognition.stop();
        };
    }, [isSupported, enabled, onActivate, onStatusChange]);

    // Toggle listening
    const toggleListening = useCallback(() => {
        if (!recognitionRef.current) return;

        if (isListening) {
            recognitionRef.current.stop();
            setIsListening(false);
            setStatus('idle');
        } else {
            try {
                recognitionRef.current.start();
            } catch (e) {
                // Ignore
            }
        }
    }, [isListening]);

    if (!isSupported) {
        return null;
    }

    return (
        <div className="wake-word-detector">
            <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={toggleListening}
                className={`
                    relative p-3 rounded-full transition-all
                    ${status === 'listening'
                        ? 'bg-emerald-100 text-emerald-600 border-2 border-emerald-300'
                        : status === 'activated'
                            ? 'bg-amber-100 text-amber-600 border-2 border-amber-300'
                            : 'bg-gray-100 text-gray-600 border-2 border-gray-200'}
                `}
                aria-label={isListening ? 'Disable wake word' : 'Enable wake word'}
                aria-pressed={isListening}
            >
                {/* Status indicator */}
                <AnimatePresence mode="wait">
                    {status === 'listening' && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full"
                        >
                            <span className="absolute inset-0 rounded-full bg-emerald-400 animate-ping" />
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Icon */}
                {status === 'activated' ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                ) : isListening ? (
                    <Volume2 className="w-5 h-5" />
                ) : (
                    <VolumeX className="w-5 h-5" />
                )}
            </motion.button>

            {/* Status text */}
            <AnimatePresence>
                {status === 'listening' && (
                    <motion.p
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 5 }}
                        className="text-xs text-emerald-600 mt-1 text-center"
                    >
                        Say "Hey Wizard"
                    </motion.p>
                )}
                {status === 'activated' && (
                    <motion.p
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 5 }}
                        className="text-xs text-amber-600 mt-1 text-center font-medium"
                    >
                        Activated! 🎤
                    </motion.p>
                )}
            </AnimatePresence>
        </div>
    );
};

/**
 * Hook for wake word detection
 */
export const useWakeWord = ({
    enabled = true,
    onActivate,
    phrases = WAKE_PHRASES
}) => {
    const [status, setStatus] = useState('idle');
    const [isListening, setIsListening] = useState(false);

    useEffect(() => {
        if (!enabled) return;

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return;

        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;

        let cooldown = false;

        recognition.onresult = (event) => {
            const lastResult = event.results[event.results.length - 1];
            const transcript = lastResult[0].transcript.toLowerCase();

            const detected = phrases.some(p => transcript.includes(p));

            if (detected && !cooldown) {
                cooldown = true;
                setStatus('activated');
                onActivate?.();

                setTimeout(() => {
                    cooldown = false;
                    setStatus('listening');
                }, 3000);
            }
        };

        recognition.onstart = () => setIsListening(true);
        recognition.onend = () => {
            if (enabled) {
                setTimeout(() => {
                    try { recognition.start(); } catch (e) { }
                }, 100);
            }
        };

        try {
            recognition.start();
            setStatus('listening');
        } catch (e) {
            setStatus('error');
        }

        return () => recognition.stop();
    }, [enabled, onActivate, phrases]);

    return { status, isListening };
};

export default WakeWordDetector;
