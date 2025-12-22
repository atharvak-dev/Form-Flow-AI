/**
 * EnhancedVoiceInput Component
 * 
 * A complete, production-ready voice input component with:
 * - Confidence visualization
 * - Clarification dialogs
 * - Autofill suggestions
 * - Wake word support
 * - Accessibility (WCAG 2.1 AA)
 * - Smooth animations
 * - Multi-language indicator
 * 
 * This is the "senior dev" level component that integrates all features.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Mic, MicOff, Loader2, Check, AlertCircle,
    Sparkles, Globe, Volume2, ChevronDown, X,
    Lightbulb, History
} from 'lucide-react';
import useAdvancedVoice from '../../hooks/useAdvancedVoice';
import ConfidenceBar from './ConfidenceBar';
import ClarificationDialog from './ClarificationDialog';
import { useTheme } from '../../context/ThemeProvider';

// Language flags for visual indicator
const LANGUAGE_FLAGS = {
    'en-US': '🇺🇸',
    'en-GB': '🇬🇧',
    'en-IN': '🇮🇳',
    'hi': '🇮🇳',
    'es': '🇪🇸',
    'fr': '🇫🇷',
    'de': '🇩🇪'
};

const EnhancedVoiceInput = ({
    fieldName,
    fieldType = 'text',
    question = '',
    placeholder = 'Click to speak or type...',
    value = '',
    onChange,
    onBlur,
    formContext = {},
    qaHistory = [],
    userId = null,
    formId = null,
    disabled = false,
    required = false,
    error = null,
    hint = null,
    enableWakeWord = false,
    showConfidence = true,
    showAutofill = true,
    className = ''
}) => {
    // Theme context
    const themeContext = useTheme?.();
    const hapticEnabled = themeContext?.customizations?.hapticEnabled ?? true;

    // Local state
    const [inputValue, setInputValue] = useState(value);
    const [showAutofillDropdown, setShowAutofillDropdown] = useState(false);
    const [recentConfirmation, setRecentConfirmation] = useState(null);

    const inputRef = useRef(null);
    const autofillRef = useRef(null);

    // Voice hook
    const {
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
        error: voiceError,
        startListening,
        stopListening,
        confirmSuggestion,
        selectAutofill,
        reset
    } = useAdvancedVoice({
        fieldName,
        fieldType,
        question,
        formContext,
        qaHistory,
        userId,
        formId,
        enableWakeWord,
        confidenceThreshold: 0.6,
        autoConfirmThreshold: 0.85,
        onResult: (value, conf, isAutoConfirmed) => {
            setInputValue(value);
            onChange?.(value);

            // Haptic feedback
            if (hapticEnabled && navigator.vibrate) {
                navigator.vibrate(isAutoConfirmed ? [50] : [30, 20, 30]);
            }

            // Show confirmation animation
            if (isAutoConfirmed && conf >= 0.85) {
                setRecentConfirmation('auto');
                setTimeout(() => setRecentConfirmation(null), 2000);
            }
        },
        onCommand: (action, params, message) => {
            console.log('Voice command:', action, params, message);
            // Handle commands (can be customized per use-case)
        },
        onBatchResult: (entities, validationResults) => {
            console.log('Batch extraction:', entities);
            // Could trigger multi-field fill here
        }
    });

    // Sync external value
    useEffect(() => {
        if (value !== inputValue) {
            setInputValue(value);
        }
    }, [value]);

    // Close autofill on outside click
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (autofillRef.current && !autofillRef.current.contains(e.target)) {
                setShowAutofillDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Handle manual input change
    const handleInputChange = (e) => {
        const newValue = e.target.value;
        setInputValue(newValue);
        onChange?.(newValue);
    };

    // Toggle voice recording
    const handleVoiceToggle = () => {
        if (isListening) {
            stopListening();
        } else {
            reset();
            startListening();
        }
    };

    // Handle clarification selection
    const handleClarificationSelect = (selectedValue) => {
        confirmSuggestion(selectedValue);
        setInputValue(selectedValue);
        onChange?.(selectedValue);
    };

    // Handle autofill selection
    const handleAutofillSelect = (suggestion) => {
        const value = suggestion.value || suggestion;
        setInputValue(value);
        onChange?.(value);
        setShowAutofillDropdown(false);
        selectAutofill(suggestion);

        if (hapticEnabled && navigator.vibrate) {
            navigator.vibrate([30]);
        }
    };

    // Generate unique IDs for accessibility
    const fieldId = `voice-field-${fieldName}`;
    const errorId = `${fieldId}-error`;
    const hintId = `${fieldId}-hint`;

    return (
        <div className={`enhanced-voice-input relative ${className}`}>
            {/* Main input container */}
            <div className="relative">
                {/* Input field */}
                <div className="relative flex items-center">
                    <input
                        ref={inputRef}
                        id={fieldId}
                        type="text"
                        value={inputValue}
                        onChange={handleInputChange}
                        onBlur={onBlur}
                        onFocus={() => showAutofill && autofillSuggestions.length > 0 && setShowAutofillDropdown(true)}
                        placeholder={isListening ? 'Listening...' : placeholder}
                        disabled={disabled || isProcessing}
                        required={required}
                        autoComplete="off"

                        // Accessibility
                        aria-label={question || fieldName}
                        aria-invalid={!!error}
                        aria-describedby={`${hint ? hintId : ''} ${error ? errorId : ''}`.trim() || undefined}
                        aria-busy={isProcessing}

                        className={`
                            w-full pl-4 pr-24 py-3.5
                            bg-white/80 dark:bg-gray-800/80
                            backdrop-blur-sm
                            border-2 rounded-2xl
                            text-gray-900 dark:text-gray-100
                            placeholder-gray-400 dark:placeholder-gray-500
                            transition-all duration-300
                            focus:outline-none focus:ring-2 focus:ring-offset-2
                            disabled:opacity-50 disabled:cursor-not-allowed
                            ${isListening
                                ? 'border-emerald-400 ring-2 ring-emerald-400/30 bg-emerald-50/50 dark:bg-emerald-900/20'
                                : error
                                    ? 'border-red-400 focus:ring-red-500'
                                    : 'border-gray-200 dark:border-gray-600 focus:ring-emerald-500 focus:border-emerald-400'
                            }
                            ${recentConfirmation === 'auto' ? 'border-emerald-500 bg-emerald-50' : ''}
                        `}
                    />

                    {/* Right side controls */}
                    <div className="absolute right-2 flex items-center gap-1.5">
                        {/* Language indicator */}
                        <AnimatePresence>
                            {detectedLanguage && detectedLanguage !== 'en-US' && (
                                <motion.span
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.8 }}
                                    className="text-lg"
                                    title={`Detected: ${detectedLanguage}`}
                                >
                                    {LANGUAGE_FLAGS[detectedLanguage] || <Globe className="w-4 h-4 text-gray-400" />}
                                </motion.span>
                            )}
                        </AnimatePresence>

                        {/* Processing indicator */}
                        {isProcessing && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="p-1"
                            >
                                <Loader2 className="w-5 h-5 text-emerald-500 animate-spin" />
                            </motion.div>
                        )}

                        {/* Success indicator */}
                        <AnimatePresence>
                            {recentConfirmation === 'auto' && (
                                <motion.div
                                    initial={{ opacity: 0, scale: 0 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0 }}
                                    className="p-1 bg-emerald-500 rounded-full"
                                >
                                    <Check className="w-4 h-4 text-white" />
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Autofill button */}
                        {showAutofill && autofillSuggestions.length > 0 && !isListening && (
                            <button
                                type="button"
                                onClick={() => setShowAutofillDropdown(!showAutofillDropdown)}
                                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                                aria-label="Show suggestions from history"
                            >
                                <History className="w-4 h-4" />
                            </button>
                        )}

                        {/* Voice button */}
                        <motion.button
                            type="button"
                            onClick={handleVoiceToggle}
                            disabled={disabled || isProcessing}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}

                            // Accessibility
                            aria-label={isListening ? 'Stop recording' : 'Start voice input'}
                            aria-pressed={isListening}

                            className={`
                                p-2.5 rounded-xl
                                transition-all duration-300
                                focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-emerald-500
                                disabled:opacity-50 disabled:cursor-not-allowed
                                ${isListening
                                    ? 'bg-red-500 text-white shadow-lg shadow-red-500/30'
                                    : 'bg-gradient-to-br from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/30 hover:shadow-xl hover:shadow-emerald-500/40'
                                }
                            `}
                        >
                            {isListening ? (
                                <motion.div
                                    animate={{ scale: [1, 1.2, 1] }}
                                    transition={{ repeat: Infinity, duration: 1.5 }}
                                >
                                    <MicOff className="w-5 h-5" />
                                </motion.div>
                            ) : (
                                <Mic className="w-5 h-5" />
                            )}

                            {/* Pulse animation when listening */}
                            {isListening && (
                                <span className="absolute inset-0 rounded-xl bg-red-400 animate-ping opacity-30" />
                            )}
                        </motion.button>
                    </div>
                </div>

                {/* Interim transcript display */}
                <AnimatePresence>
                    {(isListening || interimTranscript) && (
                        <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            className="absolute left-4 right-24 -bottom-6 text-sm text-emerald-600 dark:text-emerald-400 truncate"
                        >
                            {interimTranscript || (isListening ? '🎙️ Listening...' : '')}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Confidence bar */}
            <AnimatePresence>
                {showConfidence && confidence !== null && !needsClarification && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-2"
                    >
                        <ConfidenceBar score={confidence} size="small" />
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Issues display */}
            <AnimatePresence>
                {issues.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mt-2 space-y-1"
                    >
                        {issues.map((issue, idx) => (
                            <div
                                key={idx}
                                className="flex items-start gap-2 px-3 py-2 bg-amber-50 dark:bg-amber-900/30 rounded-lg text-sm text-amber-700 dark:text-amber-300"
                            >
                                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                <span>{issue}</span>
                            </div>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Hint text */}
            {hint && (
                <p id={hintId} className="mt-1.5 text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                    <Lightbulb className="w-3 h-3" />
                    {hint}
                </p>
            )}

            {/* Error display */}
            <AnimatePresence>
                {(error || voiceError) && (
                    <motion.p
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        id={errorId}
                        className="mt-1.5 text-sm text-red-600 dark:text-red-400 flex items-center gap-1"
                        role="alert"
                    >
                        <AlertCircle className="w-4 h-4" />
                        {error || voiceError}
                    </motion.p>
                )}
            </AnimatePresence>

            {/* Clarification Dialog */}
            <ClarificationDialog
                isOpen={needsClarification}
                question={clarificationQuestion}
                suggestions={suggestions}
                issues={issues}
                originalInput={transcript}
                onSelect={handleClarificationSelect}
                onDismiss={() => reset()}
            />

            {/* Autofill Dropdown */}
            <AnimatePresence>
                {showAutofillDropdown && autofillSuggestions.length > 0 && (
                    <motion.div
                        ref={autofillRef}
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="absolute z-50 left-0 right-0 mt-2 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-600 overflow-hidden"
                    >
                        <div className="px-3 py-2 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-100 dark:border-gray-600 flex items-center justify-between">
                            <span className="text-xs font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1">
                                <History className="w-3 h-3" />
                                From your history
                            </span>
                            <button
                                onClick={() => setShowAutofillDropdown(false)}
                                className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                            >
                                <X className="w-3 h-3 text-gray-400" />
                            </button>
                        </div>
                        <div className="max-h-48 overflow-y-auto">
                            {autofillSuggestions.map((suggestion, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => handleAutofillSelect(suggestion)}
                                    className="w-full px-4 py-3 text-left hover:bg-emerald-50 dark:hover:bg-emerald-900/20 flex items-center justify-between group transition-colors"
                                >
                                    <span className="text-gray-800 dark:text-gray-200 font-mono">
                                        {suggestion.label || suggestion.value}
                                    </span>
                                    <span className="text-xs text-gray-400 group-hover:text-emerald-600">
                                        {Math.round((suggestion.confidence || 0) * 100)}% • {suggestion.usage_count}x
                                    </span>
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default EnhancedVoiceInput;
