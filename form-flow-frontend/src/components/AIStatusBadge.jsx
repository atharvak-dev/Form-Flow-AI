import { useState, useEffect } from 'react';
import { getAIHealth } from '@/services/api';
import { Brain, Zap, AlertCircle } from 'lucide-react';

/**
 * AI Status Badge - Shows current AI mode (Intelligent/Fallback)
 * 
 * Fetches /health/ai on mount and displays a small badge.
 */
export default function AIStatusBadge() {
    const [aiMode, setAiMode] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkHealth = async () => {
            try {
                const health = await getAIHealth();
                setAiMode(health.mode);
            } catch (error) {
                setAiMode('unknown');
            } finally {
                setLoading(false);
            }
        };
        checkHealth();
    }, []);

    if (loading) {
        return null; // Don't show anything while loading
    }

    const isIntelligent = aiMode === 'intelligent';
    const isFallback = aiMode === 'fallback';

    return (
        <div
            className={`
                inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
                transition-all duration-200 cursor-default
                ${isIntelligent
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : isFallback
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-gray-500/10 text-gray-400 border border-gray-500/20'
                }
            `}
            title={isIntelligent
                ? 'AI is running with full LangChain capabilities'
                : isFallback
                    ? 'AI is running in fallback mode (regex only)'
                    : 'AI status unknown'
            }
        >
            {isIntelligent ? (
                <>
                    <Brain size={12} />
                    <span>Intelligent</span>
                </>
            ) : isFallback ? (
                <>
                    <Zap size={12} />
                    <span>Fallback</span>
                </>
            ) : (
                <>
                    <AlertCircle size={12} />
                    <span>Unknown</span>
                </>
            )}
        </div>
    );
}
