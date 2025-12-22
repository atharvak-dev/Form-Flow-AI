/**
 * useAdvancedVoice - Unified Voice Processing Hook
 * 
 * Combines all voice features into a single, easy-to-use hook:
 * - Speech recognition (Web Speech API)
 * - Wake word detection
 * - Multilingual processing
 * - Voice commands
 * - Entity extraction
 * - Smart refinement
 * - Validation
 * - Autofill suggestions
 * - Analytics tracking
 * 
 * Usage:
 * const { 
 *   isListening, 
 *   transcript, 
 *   confidence, 
 *   startListening, 
 *   stopListening,
 *   processedValue,
 *   suggestions,
 *   autofillSuggestions
 * } = useAdvancedVoice({ fieldName, fieldType, onResult });
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import voiceApi from '../services/voiceApi';

// Generate unique session ID
const generateSessionId = () =>
    `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const useAdvancedVoice = ({
    fieldName = '',
    fieldType = 'text',
    question = '',
    formContext = {},
    qaHistory = [],
    userId = null,
    formId = null,
    language = 'en-US',
    onResult = null,
    onCommand = null,
    onBatchResult = null,
    onError = null,
    enableWakeWord = false,
    wakeWordCallback = null,
    confidenceThreshold = 0.6, // Below this, ask for clarification
    autoConfirmThreshold = 0.85 // Above this, auto-accept
}) => {
    // State
    const [isListening, setIsListening] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [interimTranscript, setInterimTranscript] = useState('');
    const [processedValue, setProcessedValue] = useState('');
    const [confidence, setConfidence] = useState(null);
    const [needsClarification, setNeedsClarification] = useState(false);
    const [clarificationQuestion, setClarificationQuestion] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [issues, setIssues] = useState([]);
    const [autofillSuggestions, setAutofillSuggestions] = useState([]);
    const [detectedLanguage, setDetectedLanguage] = useState(null);
    const [error, setError] = useState(null);

    // Refs
    const recognitionRef = useRef(null);
    const sessionIdRef = useRef(generateSessionId());
    const isWakeWordActiveRef = useRef(false);

    // Initialize speech recognition
    useEffect(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            setError('Speech recognition not supported');
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = language;
        recognition.maxAlternatives = 3;

        recognition.onstart = () => {
            setIsListening(true);
            setError(null);
            setInterimTranscript('');

            // Track analytics
            voiceApi.trackAnalyticsEvent('voice_start', formId, sessionIdRef.current, fieldName);
        };

        recognition.onend = () => {
            setIsListening(false);

            // Track analytics
            voiceApi.trackAnalyticsEvent('voice_end', formId, sessionIdRef.current, fieldName);
        };

        recognition.onerror = (event) => {
            console.warn('Speech recognition error:', event.error);
            setIsListening(false);

            if (event.error !== 'no-speech' && event.error !== 'aborted') {
                setError(`Recognition error: ${event.error}`);
                onError?.(event.error);
            }
        };

        recognition.onresult = async (event) => {
            const results = event.results;
            const lastResult = results[results.length - 1];

            if (lastResult.isFinal) {
                const finalTranscript = lastResult[0].transcript;
                setTranscript(finalTranscript);
                setInterimTranscript('');

                // Check for wake word first if enabled
                if (enableWakeWord && !isWakeWordActiveRef.current) {
                    const wakeWords = ['hey wizard', 'hey form', 'ok wizard'];
                    const isWakeWord = wakeWords.some(w =>
                        finalTranscript.toLowerCase().includes(w)
                    );

                    if (isWakeWord) {
                        isWakeWordActiveRef.current = true;
                        wakeWordCallback?.();
                        return;
                    }
                }

                // Process the voice input
                await processInput(finalTranscript);
            } else {
                // Interim result
                setInterimTranscript(lastResult[0].transcript);
            }
        };

        recognitionRef.current = recognition;

        return () => {
            recognition.abort();
        };
    }, [language, enableWakeWord]);

    // Load autofill suggestions when field changes
    useEffect(() => {
        const loadAutofill = async () => {
            if (userId && fieldName) {
                const result = await voiceApi.getAutofillSuggestions(
                    userId,
                    fieldName,
                    fieldType
                );
                if (result.success && result.suggestions) {
                    setAutofillSuggestions(result.suggestions);
                }
            }
        };

        loadAutofill();
    }, [userId, fieldName, fieldType]);

    // Process voice input through the full pipeline
    const processInput = useCallback(async (text) => {
        if (!text.trim()) return;

        setIsProcessing(true);
        setNeedsClarification(false);
        setClarificationQuestion('');
        setSuggestions([]);
        setIssues([]);

        try {
            const result = await voiceApi.processVoiceInput({
                text,
                fieldName,
                fieldType,
                question,
                formContext,
                qaHistory,
                userId,
                formId,
                sessionId: sessionIdRef.current
            });

            // Handle different result types
            switch (result.type) {
                case 'command':
                    // Voice command detected
                    onCommand?.(result.action, result.params, result.message);
                    break;

                case 'batch':
                    // Multiple fields extracted
                    onBatchResult?.(result.entities, result.validation_results);
                    break;

                case 'single':
                    // Single field result
                    setProcessedValue(result.value);
                    setConfidence(result.confidence);
                    setDetectedLanguage(result.detected_language);

                    if (result.issues?.length > 0) {
                        setIssues(result.issues);
                    }

                    if (result.needs_clarification || result.confidence < confidenceThreshold) {
                        setNeedsClarification(true);
                        setClarificationQuestion(result.clarification_question ||
                            `Did you mean "${result.value}"?`);
                        setSuggestions(result.suggestions || []);
                    } else if (result.confidence >= autoConfirmThreshold) {
                        // High confidence - auto-confirm
                        onResult?.(result.value, result.confidence, true);
                    } else {
                        // Medium confidence - return but might need confirmation
                        onResult?.(result.value, result.confidence, false);
                    }
                    break;

                case 'error':
                    setError(result.error);
                    onError?.(result.error);
                    break;
            }

        } catch (err) {
            console.error('Voice processing error:', err);
            setError(err.message);
            onError?.(err.message);
        } finally {
            setIsProcessing(false);
        }
    }, [fieldName, fieldType, question, formContext, qaHistory, userId, formId,
        confidenceThreshold, autoConfirmThreshold, onResult, onCommand, onBatchResult, onError]);

    // Start listening
    const startListening = useCallback(() => {
        if (recognitionRef.current && !isListening) {
            try {
                recognitionRef.current.start();
            } catch (err) {
                // Might already be running
                console.warn('Could not start recognition:', err);
            }
        }
    }, [isListening]);

    // Stop listening
    const stopListening = useCallback(() => {
        if (recognitionRef.current && isListening) {
            recognitionRef.current.stop();
        }
    }, [isListening]);

    // Confirm a suggestion
    const confirmSuggestion = useCallback((value) => {
        setProcessedValue(value);
        setNeedsClarification(false);
        setSuggestions([]);
        onResult?.(value, 1.0, true);
    }, [onResult]);

    // Select an autofill suggestion
    const selectAutofill = useCallback((suggestion) => {
        const value = suggestion.value || suggestion;
        setProcessedValue(value);
        onResult?.(value, suggestion.confidence || 1.0, true);
    }, [onResult]);

    // Reset state
    const reset = useCallback(() => {
        setTranscript('');
        setInterimTranscript('');
        setProcessedValue('');
        setConfidence(null);
        setNeedsClarification(false);
        setClarificationQuestion('');
        setSuggestions([]);
        setIssues([]);
        setError(null);
    }, []);

    return {
        // State
        isListening,
        isProcessing,
        transcript,
        interimTranscript,
        processedValue,
        confidence,
        needsClarification,
        clarificationQuestion,
        suggestions,
        issues,
        autofillSuggestions,
        detectedLanguage,
        error,

        // Actions
        startListening,
        stopListening,
        confirmSuggestion,
        selectAutofill,
        reset,
        processInput, // For manual text processing

        // Session
        sessionId: sessionIdRef.current
    };
};

export default useAdvancedVoice;
