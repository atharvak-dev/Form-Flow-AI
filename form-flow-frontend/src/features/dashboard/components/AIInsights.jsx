/**
 * AIInsights Component - Premium Redesign
 * 
 * Displays AI-generated insights with animated typing effect and premium styling.
 * Redesigned with glassmorphism to match landing page FeatureCard aesthetic.
 */

import { useState, useEffect } from 'react';
import { Sparkles, RefreshCw, Lightbulb, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';
import { useTheme } from '@/context/ThemeProvider';
import { motion, AnimatePresence } from 'framer-motion';

// Parse insights into structured format
function parseInsights(insightsText) {
    if (!insightsText) return [];

    // Split by common delimiters and filter empty
    const parts = insightsText
        .split(/[.!?]/)
        .map(s => s.trim())
        .filter(s => s.length > 10);

    return parts.slice(0, 3).map((text, i) => ({
        id: i,
        text: text + '.',
        type: text.toLowerCase().includes('success') || text.toLowerCase().includes('great')
            ? 'success'
            : text.toLowerCase().includes('consider') || text.toLowerCase().includes('try')
                ? 'tip'
                : 'insight'
    }));
}

export function AIInsights({ insights, isLoading, onRefresh }) {
    const { isDark } = useTheme();
    const [displayedInsights, setDisplayedInsights] = useState([]);

    useEffect(() => {
        if (insights) {
            setDisplayedInsights(parseInsights(insights));
        }
    }, [insights]);

    const iconMap = {
        success: CheckCircle,
        tip: Lightbulb,
        insight: TrendingUp,
    };

    const colorMap = {
        success: {
            bg: isDark ? 'bg-emerald-500/10' : 'bg-emerald-50',
            text: isDark ? 'text-emerald-400' : 'text-emerald-600',
            border: isDark ? 'border-emerald-500/20' : 'border-emerald-200',
            glow: isDark ? 'shadow-[0_0_10px_rgba(16,185,129,0.1)]' : '',
        },
        tip: {
            bg: isDark ? 'bg-teal-500/10' : 'bg-teal-50',
            text: isDark ? 'text-teal-400' : 'text-teal-600',
            border: isDark ? 'border-teal-500/20' : 'border-teal-200',
            glow: isDark ? 'shadow-[0_0_10px_rgba(20,184,166,0.1)]' : '',
        },
        insight: {
            bg: isDark ? 'bg-emerald-500/10' : 'bg-emerald-50',
            text: isDark ? 'text-emerald-400' : 'text-emerald-600',
            border: isDark ? 'border-emerald-500/20' : 'border-emerald-200',
            glow: isDark ? 'shadow-[0_0_10px_rgba(16,185,129,0.1)]' : '',
        },
    };

    return (
        <div className="h-full flex flex-col relative group">
            {/* Refresh Button */}
            <button
                onClick={onRefresh}
                disabled={isLoading}
                className={`absolute top-0 right-0 p-2 rounded-xl transition-all opacity-0 group-hover:opacity-100 z-10 ${isDark
                    ? 'hover:bg-white/10 text-white/40 hover:text-white'
                    : 'hover:bg-zinc-100 text-zinc-400 hover:text-zinc-900'
                    }`}
                title="Refresh insights"
            >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>

            {/* Content */}
            <div className="flex-1 flex flex-col justify-center">
                <AnimatePresence mode="wait">
                    {isLoading ? (
                        <motion.div
                            key="loading"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex flex-col items-center justify-center gap-4 py-8"
                        >
                            <div className="relative">
                                <div className={`w-12 h-12 rounded-full border-2 animate-spin ${isDark
                                    ? 'border-emerald-500/20 border-t-emerald-500'
                                    : 'border-emerald-200 border-t-emerald-500'
                                    }`} />
                                <Sparkles className={`absolute inset-0 m-auto w-5 h-5 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
                            </div>
                            <p className={`text-sm font-mono ${isDark ? 'text-white/40' : 'text-zinc-500'}`}>
                                Analyzing patterns...
                            </p>
                        </motion.div>
                    ) : displayedInsights.length > 0 ? (
                        <motion.div
                            key="insights"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="space-y-3"
                        >
                            {displayedInsights.map((item, idx) => {
                                const Icon = iconMap[item.type];
                                const colors = colorMap[item.type];

                                return (
                                    <motion.div
                                        key={item.id}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.1 }}
                                        className={`group/insight relative flex items-start gap-3 p-3 rounded-xl border transition-all duration-300 ${colors.bg} ${colors.border} ${colors.glow} hover:scale-[1.01]`}
                                    >
                                        {/* Hover spotlight */}
                                        <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-transparent to-transparent opacity-0 group-hover/insight:opacity-100 transition-opacity duration-500 rounded-xl pointer-events-none" />

                                        <div className={`mt-0.5 relative z-10 ${colors.text}`}>
                                            <Icon className="w-4 h-4" />
                                        </div>
                                        <p className={`text-sm leading-relaxed flex-1 relative z-10 ${isDark ? 'text-white/80' : 'text-zinc-700'}`}>
                                            {item.text}
                                        </p>
                                    </motion.div>
                                );
                            })}
                        </motion.div>
                    ) : (
                        <motion.div
                            key="empty"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex flex-col items-center justify-center gap-4 py-8 text-center"
                        >
                            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center border ${isDark
                                ? 'bg-white/[0.03] border-white/[0.06]'
                                : 'bg-zinc-50 border-zinc-200'
                                }`}>
                                <Sparkles className={`w-7 h-7 ${isDark ? 'text-white/15' : 'text-zinc-300'}`} />
                            </div>
                            <div>
                                <p className={`font-medium ${isDark ? 'text-white/60' : 'text-zinc-600'}`}>
                                    No insights yet
                                </p>
                                <p className={`text-xs mt-1 ${isDark ? 'text-white/35' : 'text-zinc-400'}`}>
                                    Submit more forms to get AI-powered insights
                                </p>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
