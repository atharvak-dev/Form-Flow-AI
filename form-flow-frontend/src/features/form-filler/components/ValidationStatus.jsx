/**
 * ValidationStatus Component
 * 
 * Displays real-time validation feedback with auto-correction.
 */

import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, CheckCircle, Lightbulb } from 'lucide-react';

const ValidationStatus = ({
    isValid,
    issues = [],
    suggestions = [],
    autoCorrected,
    onAcceptCorrection
}) => {
    if (isValid && !autoCorrected) return null;

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-2"
            >
                {/* Auto-corrected Banner */}
                {autoCorrected && (
                    <div className="flex items-center gap-2 px-3 py-2 bg-emerald-50 rounded-lg border border-emerald-200 mb-2">
                        <CheckCircle className="w-4 h-4 text-emerald-600" />
                        <span className="text-sm text-emerald-800">
                            Auto-corrected to: <strong>{autoCorrected}</strong>
                        </span>
                        <button
                            onClick={() => onAcceptCorrection && onAcceptCorrection(autoCorrected)}
                            className="ml-auto text-xs px-2 py-1 bg-emerald-500 text-white rounded-md hover:bg-emerald-600"
                        >
                            Accept
                        </button>
                    </div>
                )}

                {/* Issues */}
                {issues.length > 0 && (
                    <div className="space-y-1">
                        {issues.map((issue, idx) => (
                            <div key={idx} className="flex items-start gap-2 text-sm text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
                                <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                <span>{issue}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Suggestions */}
                {suggestions.length > 0 && (
                    <div className="mt-2 p-2 bg-blue-50 rounded-lg">
                        <div className="flex items-center gap-1 text-xs text-blue-700 mb-1">
                            <Lightbulb className="w-3 h-3" />
                            <span>Suggestions:</span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                            {suggestions.map((suggestion, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => onAcceptCorrection && onAcceptCorrection(suggestion)}
                                    className="text-xs px-2 py-1 bg-white border border-blue-200 rounded-md hover:bg-blue-100 text-blue-800"
                                >
                                    {suggestion}
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </motion.div>
        </AnimatePresence>
    );
};

export default ValidationStatus;
