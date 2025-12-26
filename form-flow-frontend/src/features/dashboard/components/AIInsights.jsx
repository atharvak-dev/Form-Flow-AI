/**
 * AIInsights Component
 * 
 * Displays AI-generated insights about form filling patterns.
 */

import { Sparkles, RefreshCw } from 'lucide-react';
import { useTheme } from '@/context/ThemeProvider';

export function AIInsights({ insights, isLoading, onRefresh }) {
    const { isDark } = useTheme();

    const cardClass = isDark
        ? "bg-gradient-to-br from-emerald-900/30 to-blue-900/30 border-emerald-500/20"
        : "bg-gradient-to-br from-emerald-50 to-blue-50 border-emerald-200";

    const textClass = isDark ? "text-white/80" : "text-zinc-700";
    const iconClass = isDark ? "text-emerald-400" : "text-emerald-600";

    return (
        <div className={`rounded-2xl p-6 border backdrop-blur-xl ${cardClass}`}>
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <div className={`p-2 rounded-lg ${isDark ? 'bg-emerald-500/20' : 'bg-emerald-100'}`}>
                        <Sparkles className={`h-5 w-5 ${iconClass}`} />
                    </div>
                    <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                        AI Insights
                    </h3>
                </div>
                <button
                    onClick={onRefresh}
                    disabled={isLoading}
                    className={`p-2 rounded-lg transition-colors ${isDark
                            ? 'hover:bg-white/10 text-white/50 hover:text-white'
                            : 'hover:bg-zinc-100 text-zinc-400 hover:text-zinc-900'
                        } ${isLoading ? 'animate-spin' : ''}`}
                    title="Refresh insights"
                >
                    <RefreshCw className="h-4 w-4" />
                </button>
            </div>

            <p className={`text-sm leading-relaxed ${textClass}`}>
                {isLoading ? "Generating insights..." : insights}
            </p>
        </div>
    );
}
