/**
 * ConfidenceBar Component
 * 
 * Displays a visual confidence indicator for AI predictions.
 * - Green (≥80%): High confidence - auto-fill
 * - Yellow (60-79%): Medium - show confirmation
 * - Red (<60%): Low - request clarification
 */

import { motion } from 'framer-motion';

const ConfidenceBar = ({ score, showLabel = true, size = 'normal' }) => {
    if (score === null || score === undefined) return null;

    const percentage = Math.round(score * 100);

    // Determine color based on confidence level
    const getColor = () => {
        if (score >= 0.8) return { bg: 'bg-emerald-500', glow: 'shadow-emerald-500/50' };
        if (score >= 0.6) return { bg: 'bg-amber-500', glow: 'shadow-amber-500/50' };
        return { bg: 'bg-red-500', glow: 'shadow-red-500/50' };
    };

    const getLabel = () => {
        if (score >= 0.8) return { text: 'High Confidence', emoji: '✓' };
        if (score >= 0.6) return { text: 'Needs Confirmation', emoji: '?' };
        return { text: 'Low Confidence', emoji: '⚠' };
    };

    const { bg, glow } = getColor();
    const { text, emoji } = getLabel();

    const barHeight = size === 'small' ? 'h-1.5' : 'h-2.5';
    const fontSize = size === 'small' ? 'text-xs' : 'text-sm';

    return (
        <div className="w-full">
            {showLabel && (
                <div className={`flex justify-between ${fontSize} text-gray-600 mb-1`}>
                    <span className="flex items-center gap-1">
                        <span>{emoji}</span>
                        <span>{text}</span>
                    </span>
                    <span className="font-mono font-medium">{percentage}%</span>
                </div>
            )}

            <div className={`w-full bg-gray-200/50 rounded-full ${barHeight} overflow-hidden`}>
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 0.5, ease: 'easeOut' }}
                    className={`${bg} ${barHeight} rounded-full shadow-md ${glow}`}
                />
            </div>
        </div>
    );
};

export default ConfidenceBar;
