/**
 * Accessible Form Field Component
 * 
 * WCAG 2.1 AA Compliant Form Field with:
 * - Proper ARIA labels and descriptions
 * - Error announcements for screen readers
 * - Keyboard navigation support
 * - Focus management
 * - High contrast support
 */

import React, { useId, forwardRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle2, HelpCircle } from 'lucide-react';

const AccessibleFormField = forwardRef(({
    id,
    label,
    type = 'text',
    value,
    onChange,
    onBlur,
    onFocus,
    error,
    hint,
    required = false,
    disabled = false,
    autoComplete,
    placeholder,
    className = '',
    inputClassName = '',
    ...props
}, ref) => {
    // Generate unique IDs for accessibility
    const uniqueId = useId();
    const fieldId = id || `field-${uniqueId}`;
    const labelId = `${fieldId}-label`;
    const hintId = `${fieldId}-hint`;
    const errorId = `${fieldId}-error`;

    // Build aria-describedby based on available descriptions
    const describedBy = [
        hint ? hintId : null,
        error ? errorId : null
    ].filter(Boolean).join(' ') || undefined;

    return (
        <div
            className={`accessible-form-field ${className}`}
            role="group"
            aria-labelledby={labelId}
        >
            {/* Label with required indicator */}
            <label
                id={labelId}
                htmlFor={fieldId}
                className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1"
            >
                {label}
                {required && (
                    <span
                        className="text-red-500 ml-1"
                        aria-label="required field"
                        role="img"
                    >
                        *
                    </span>
                )}
            </label>

            {/* Hint text */}
            <AnimatePresence>
                {hint && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        id={hintId}
                        className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 mb-1.5"
                        role="note"
                    >
                        <HelpCircle className="w-3.5 h-3.5 flex-shrink-0" aria-hidden="true" />
                        <span>{hint}</span>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Input wrapper for icon positioning */}
            <div className="relative">
                <input
                    ref={ref}
                    id={fieldId}
                    type={type}
                    value={value}
                    onChange={onChange}
                    onBlur={onBlur}
                    onFocus={onFocus}
                    disabled={disabled}
                    required={required}
                    autoComplete={autoComplete}
                    placeholder={placeholder}

                    // ARIA attributes for accessibility
                    aria-labelledby={labelId}
                    aria-describedby={describedBy}
                    aria-invalid={!!error}
                    aria-required={required}
                    aria-disabled={disabled}

                    className={`
                        w-full px-4 py-2.5 
                        border-2 rounded-xl
                        bg-white dark:bg-gray-800
                        text-gray-900 dark:text-gray-100
                        placeholder-gray-400 dark:placeholder-gray-500
                        transition-all duration-200
                        focus:outline-none focus:ring-2 focus:ring-offset-2
                        disabled:opacity-50 disabled:cursor-not-allowed
                        ${error
                            ? 'border-red-500 focus:ring-red-500'
                            : 'border-gray-300 dark:border-gray-600 focus:ring-emerald-500 focus:border-emerald-500'
                        }
                        ${inputClassName}
                    `}

                    {...props}
                />

                {/* Status icon */}
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    {error ? (
                        <AlertCircle className="w-5 h-5 text-red-500" aria-hidden="true" />
                    ) : value && !error ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-500" aria-hidden="true" />
                    ) : null}
                </div>
            </div>

            {/* Error message with live announcement */}
            <AnimatePresence>
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        id={errorId}
                        className="flex items-center gap-1.5 mt-1.5 text-sm text-red-600 dark:text-red-400"
                        role="alert"
                        aria-live="assertive"
                        aria-atomic="true"
                    >
                        <AlertCircle className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
                        <span>{error}</span>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
});

AccessibleFormField.displayName = 'AccessibleFormField';

/**
 * Accessible Voice Button
 */
export const AccessibleVoiceButton = ({
    isListening,
    onClick,
    disabled = false,
    className = ''
}) => {
    return (
        <button
            onClick={onClick}
            disabled={disabled}

            // ARIA attributes
            aria-label={isListening ? 'Stop voice recording' : 'Start voice recording'}
            aria-pressed={isListening}
            aria-disabled={disabled}

            // Keyboard support
            onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onClick?.();
                }
            }}

            className={`
                relative p-4 rounded-full
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500
                disabled:opacity-50 disabled:cursor-not-allowed
                ${isListening
                    ? 'bg-red-500 text-white shadow-lg shadow-red-500/30'
                    : 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 hover:bg-emerald-600'
                }
                ${className}
            `}

            tabIndex={0}
            role="button"
        >
            {/* Visual indicator */}
            <span aria-hidden="true" className="text-2xl">
                {isListening ? '🔴' : '🎤'}
            </span>

            {/* Screen reader text */}
            <span className="sr-only">
                {isListening ? 'Recording in progress. Click to stop.' : 'Click to start voice recording'}
            </span>

            {/* Pulse animation when listening */}
            {isListening && (
                <span
                    className="absolute inset-0 rounded-full bg-red-400 animate-ping opacity-30"
                    aria-hidden="true"
                />
            )}
        </button>
    );
};

/**
 * Accessible Progress Indicator
 */
export const AccessibleProgress = ({
    current,
    total,
    currentFieldLabel = '',
    className = ''
}) => {
    const percentage = Math.round((current / total) * 100);

    return (
        <div
            role="progressbar"
            aria-valuenow={current}
            aria-valuemin={0}
            aria-valuemax={total}
            aria-label={`Form progress: ${current} of ${total} fields completed`}
            aria-describedby="progress-details"
            className={`relative ${className}`}
        >
            {/* Visual progress bar */}
            <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 0.3, ease: 'easeOut' }}
                    className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full"
                    aria-hidden="true"
                />
            </div>

            {/* Text description for screen readers */}
            <div id="progress-details" className="sr-only">
                You have completed {current} out of {total} fields.
                {currentFieldLabel && ` Currently on: ${currentFieldLabel}`}
            </div>

            {/* Visual text */}
            <div
                className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1"
                aria-hidden="true"
            >
                <span>{current} / {total} completed</span>
                <span>{percentage}%</span>
            </div>
        </div>
    );
};

/**
 * Live Region Announcer for screen readers
 */
export const LiveAnnouncer = ({ message, priority = 'polite' }) => {
    return (
        <div
            role="status"
            aria-live={priority}
            aria-atomic="true"
            className="sr-only"
        >
            {message}
        </div>
    );
};

/**
 * Skip Link for keyboard navigation
 */
export const SkipLink = ({ targetId, children = 'Skip to main content' }) => {
    return (
        <a
            href={`#${targetId}`}
            className="
                sr-only focus:not-sr-only
                focus:absolute focus:top-4 focus:left-4
                focus:z-50 focus:px-4 focus:py-2
                focus:bg-emerald-600 focus:text-white
                focus:rounded-lg focus:shadow-lg
                focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500
            "
        >
            {children}
        </a>
    );
};

export default AccessibleFormField;
