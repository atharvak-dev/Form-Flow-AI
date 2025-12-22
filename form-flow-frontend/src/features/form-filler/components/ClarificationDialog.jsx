/**
 * ClarificationDialog Component
 * 
 * Displays when AI needs clarification or has suggestions.
 * Shows:
 * - Clarification question
 * - Clickable suggestions
 * - Issue warnings
 */

import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, HelpCircle, CheckCircle2, X } from 'lucide-react';

const ClarificationDialog = ({
    isOpen,
    question,
    suggestions = [],
    issues = [],
    onSelect,
    onDismiss,
    originalInput
}) => {
    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className="absolute inset-x-4 bottom-full mb-3 z-50"
            >
                <div className="bg-white/95 backdrop-blur-md rounded-2xl shadow-xl border border-amber-200/50 overflow-hidden">
                    {/* Header */}
                    <div className="px-4 py-3 bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-100/50 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <HelpCircle className="w-5 h-5 text-amber-600" />
                            <span className="font-medium text-amber-900">Clarification Needed</span>
                        </div>
                        <button
                            onClick={onDismiss}
                            className="p-1 rounded-lg hover:bg-amber-100/50 text-amber-600"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="p-4">
                        {/* Original Input */}
                        {originalInput && (
                            <div className="mb-3 text-sm text-gray-500">
                                You said: <span className="italic">"{originalInput}"</span>
                            </div>
                        )}

                        {/* Question */}
                        {question && (
                            <p className="text-gray-800 font-medium mb-3">{question}</p>
                        )}

                        {/* Issues/Warnings */}
                        {issues && issues.length > 0 && (
                            <div className="mb-3 space-y-1">
                                {issues.map((issue, idx) => (
                                    <div key={idx} className="flex items-start gap-2 text-sm text-orange-700 bg-orange-50 rounded-lg p-2">
                                        <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                        <span>{issue}</span>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Suggestions */}
                        {suggestions && suggestions.length > 0 && (
                            <div className="space-y-2">
                                <p className="text-sm text-gray-600 mb-2">Did you mean:</p>
                                {suggestions.map((suggestion, idx) => (
                                    <motion.button
                                        key={idx}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => onSelect(suggestion)}
                                        className="w-full text-left px-4 py-3 bg-gradient-to-r from-emerald-50 to-teal-50 hover:from-emerald-100 hover:to-teal-100 border border-emerald-200/50 rounded-xl flex items-center justify-between group transition-all"
                                    >
                                        <span className="text-gray-800 font-mono">{suggestion}</span>
                                        <CheckCircle2 className="w-5 h-5 text-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    </motion.button>
                                ))}
                            </div>
                        )}

                        {/* Manual Input Option */}
                        <div className="mt-4 pt-3 border-t border-gray-100">
                            <p className="text-xs text-gray-500 text-center">
                                Or speak again with the correct value
                            </p>
                        </div>
                    </div>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};

export default ClarificationDialog;
