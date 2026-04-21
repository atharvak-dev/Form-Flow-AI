/**
 * Plugin Card Component
 * Premium SaaS redesign: minimal, structured, elegant hierarchy
 */
import { memo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Database, Key, Trash2, Settings, Activity, Server, DatabaseZap } from 'lucide-react';
import { useTheme } from '@/context/ThemeProvider';

const PluginCard = memo(function PluginCard({
    plugin,
    onEdit,
    onAPIKeys,
    onTest,
    onDelete,
    onPrefetch,
}) {
    const { isDark } = useTheme();

    const handleMouseEnter = useCallback(() => {
        onPrefetch?.(plugin.id);
    }, [plugin.id, onPrefetch]);

    const dbColors = {
        postgresql: 'text-blue-500',
        mysql: 'text-orange-500',
        mongodb: 'text-emerald-500',
    };

    return (
        <motion.article
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98 }}
            whileHover={{ y: -4 }}
            onMouseEnter={handleMouseEnter}
            className={`
                group relative flex flex-col rounded-3xl border transition-all duration-300
                ${isDark
                    ? 'bg-zinc-900/50 border-white/[0.06] hover:border-white/[0.12] hover:bg-zinc-900/80 shadow-[0_4px_24px_rgba(0,0,0,0.2)] hover:shadow-[0_8px_32px_rgba(0,0,0,0.4)]'
                    : 'bg-white border-zinc-200 hover:border-zinc-300 shadow-sm hover:shadow-xl hover:shadow-zinc-200/50'
                }
            `}
        >
            {/* Top Section - Header & Header Actions */}
            <div className="flex items-start justify-between p-6 pb-4">
                <div className="flex items-start gap-4">
                    {/* Database Icon */}
                    <div className={`w-12 h-12 rounded-[1.25rem] flex items-center justify-center shrink-0 border transition-transform duration-300 group-hover:scale-105 ${isDark
                        ? 'bg-zinc-800/80 border-white/[0.08]'
                        : 'bg-zinc-50 border-zinc-200/80'
                        }`}>
                        <Database className={`w-5 h-5 ${dbColors[plugin.database_type.toLowerCase()] || 'text-zinc-500'}`} />
                    </div>

                    {/* Title & Subtitle */}
                    <div className="flex flex-col pt-1">
                        <div className="flex items-center gap-2">
                            <h3 className={`text-lg font-semibold tracking-tight leading-none truncate max-w-[160px] ${isDark ? 'text-zinc-100 group-hover:text-white' : 'text-zinc-900'}`}>
                                {plugin.name}
                            </h3>
                            {/* Status Indicator */}
                            <div className="flex items-center justify-center w-5 h-5" title={plugin.is_active ? 'Active' : 'Inactive'}>
                                <div className={`w-2 h-2 rounded-full ${plugin.is_active 
                                    ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]' 
                                    : 'bg-zinc-500'
                                }`} />
                            </div>
                        </div>
                        
                        <div className="flex items-center gap-1.5 mt-2">
                            <Server className={`w-3.5 h-3.5 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`} />
                            <span className={`text-[11px] font-medium tracking-wide uppercase ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>
                                {plugin.database_type}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Top Action (Delete) */}
                <button
                    onClick={(e) => { e.stopPropagation(); onDelete?.(plugin); }}
                    title="Delete Plugin"
                    className={`p-2 -mr-2 -mt-2 rounded-xl transition-colors opacity-0 group-hover:opacity-100 ${isDark
                        ? 'text-zinc-500 hover:text-red-400 hover:bg-red-500/10'
                        : 'text-zinc-400 hover:text-red-600 hover:bg-red-50'
                        }`}
                >
                    <Trash2 className="w-[18px] h-[18px]" />
                </button>
            </div>

            {/* Middle Section - Description */}
            <div className="px-6 pb-5 flex-1">
                {plugin.description ? (
                    <p className={`text-[13px] leading-relaxed line-clamp-2 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                        {plugin.description}
                    </p>
                ) : (
                    <p className={`text-[13px] italic opacity-50 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>
                        No description provided.
                    </p>
                )}
            </div>

            {/* Bottom Section - Stats & Actions */}
            <div className={`mt-auto rounded-b-[calc(1.5rem-1px)] border-t overflow-hidden ${isDark 
                ? 'bg-black/20 border-white/[0.06]' 
                : 'bg-zinc-50 border-zinc-100'
            }`}>
                
                {/* Stats Row */}
                <div className={`grid grid-cols-3 border-b ${isDark ? 'border-white/[0.04]' : 'border-zinc-200/60'}`}>
                    {[
                        { label: 'Tables', value: plugin.tables?.length || 0 },
                        { label: 'API Keys', value: plugin.api_key_count || 0 },
                        { label: 'Requests', value: plugin.session_count || 0, highlight: true }
                    ].map((stat, i) => (
                        <div key={stat.label} className={`flex flex-col items-center justify-center py-3 ${i !== 2 ? (isDark ? 'border-r border-white/[0.04]' : 'border-r border-zinc-200/60') : ''}`}>
                            <span className={`text-[10px] font-semibold tracking-widest uppercase mb-1 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>
                                {stat.label}
                            </span>
                            <span className={`text-base font-mono font-medium ${isDark 
                                ? (stat.highlight ? 'text-emerald-400' : 'text-zinc-200')
                                : (stat.highlight ? 'text-emerald-600' : 'text-zinc-900')
                            }`}>
                                {stat.value}
                            </span>
                        </div>
                    ))}
                </div>

                {/* Primary Actions Row */}
                <div className="flex items-center">
                    <button
                        onClick={(e) => { e.stopPropagation(); onEdit?.(plugin); }}
                        className={`flex-1 flex items-center justify-center gap-2 py-3.5 text-[12px] font-medium transition-colors ${
                            isDark
                                ? 'text-zinc-300 hover:text-white hover:bg-white/[0.05]'
                                : 'text-zinc-600 hover:text-zinc-900 hover:bg-black/[0.02]'
                        }`}
                    >
                        <Settings className="w-4 h-4" /> Setup
                    </button>
                    
                    <div className={`w-px h-6 ${isDark ? 'bg-white/[0.04]' : 'bg-zinc-200'}`} />

                    <button
                        onClick={(e) => { e.stopPropagation(); onTest?.(plugin); }}
                        className={`flex-1 flex items-center justify-center gap-2 py-3.5 text-[12px] font-medium transition-colors ${
                            isDark
                                ? 'text-zinc-300 hover:text-white hover:bg-white/[0.05]'
                                : 'text-zinc-600 hover:text-zinc-900 hover:bg-black/[0.02]'
                        }`}
                    >
                        <Activity className="w-4 h-4" /> Test
                    </button>

                    <div className={`w-px h-6 ${isDark ? 'bg-white/[0.04]' : 'bg-zinc-200'}`} />

                    <button
                        onClick={(e) => { e.stopPropagation(); onAPIKeys?.(plugin); }}
                        className={`flex-1 flex items-center justify-center gap-2 py-3.5 text-[12px] font-medium transition-colors ${
                            isDark
                                ? 'text-zinc-300 hover:text-white hover:bg-white/[0.05]'
                                : 'text-zinc-600 hover:text-zinc-900 hover:bg-black/[0.02]'
                        }`}
                    >
                        <Key className="w-4 h-4" /> Keys
                    </button>
                </div>
            </div>
        </motion.article>
    );
}, (prevProps, nextProps) => {
    return (
        prevProps.plugin.id === nextProps.plugin.id &&
        prevProps.plugin.name === nextProps.plugin.name &&
        prevProps.plugin.is_active === nextProps.plugin.is_active &&
        prevProps.plugin.updated_at === nextProps.plugin.updated_at
    );
});

export function PluginCardSkeleton() {
    const { isDark } = useTheme();

    return (
        <div className={`flex flex-col rounded-3xl border ${isDark ? 'bg-zinc-900/30 border-white/[0.05]' : 'bg-white border-zinc-200'} animate-pulse`}>
            {/* Header */}
            <div className="flex items-start gap-4 p-6 pb-4">
                <div className={`w-12 h-12 rounded-[1.25rem] ${isDark ? 'bg-white/5' : 'bg-zinc-100'}`} />
                <div className="pt-1 flex-1">
                    <div className={`h-5 w-32 rounded mb-2.5 ${isDark ? 'bg-white/10' : 'bg-zinc-200'}`} />
                    <div className={`h-3 w-20 rounded ${isDark ? 'bg-white/5' : 'bg-zinc-100'}`} />
                </div>
            </div>
            
            {/* Description */}
            <div className="px-6 pb-5">
                <div className={`h-3 w-full rounded mb-2 ${isDark ? 'bg-white/5' : 'bg-zinc-100'}`} />
                <div className={`h-3 w-2/3 rounded ${isDark ? 'bg-white/5' : 'bg-zinc-100'}`} />
            </div>

            {/* Footer */}
            <div className={`mt-auto flex flex-col rounded-b-[calc(1.5rem-1px)] border-t ${isDark ? 'bg-black/10 border-white/[0.05]' : 'bg-zinc-50 border-zinc-100'}`}>
                <div className="grid grid-cols-3 p-4">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="flex flex-col items-center gap-2">
                            <div className={`w-12 h-2 rounded ${isDark ? 'bg-white/5' : 'bg-zinc-200'}`} />
                            <div className={`w-6 h-4 rounded ${isDark ? 'bg-white/10' : 'bg-zinc-300'}`} />
                        </div>
                    ))}
                </div>
                <div className={`flex items-center border-t py-4 ${isDark ? 'border-white/[0.04]' : 'border-zinc-200/60'}`}>
                    <div className={`flex-1 h-4 mx-8 rounded ${isDark ? 'bg-white/5' : 'bg-zinc-200'}`} />
                    <div className={`flex-1 h-4 mx-8 rounded ${isDark ? 'bg-white/5' : 'bg-zinc-200'}`} />
                    <div className={`flex-1 h-4 mx-8 rounded ${isDark ? 'bg-white/5' : 'bg-zinc-200'}`} />
                </div>
            </div>
        </div>
    );
}

export default PluginCard;
