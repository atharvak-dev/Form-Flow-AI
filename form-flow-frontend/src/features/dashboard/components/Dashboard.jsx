"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Clock, ExternalLink, FileText, CheckCircle2, XCircle } from "lucide-react"
import api from '@/services/api'
import { ROUTES } from '@/constants'
import { useTheme } from '@/context/ThemeProvider'

export function Dashboard() {
    const { isDark } = useTheme();
    const [history, setHistory] = useState([])
    const [loading, setLoading] = useState(true)
    const [user, setUser] = useState(null)

    // Dynamic Theme Styles
    const mainTextClass = isDark ? "text-white" : "text-zinc-900";
    const subTextClass = isDark ? "text-white/60" : "text-zinc-500";

    // Stats Cards
    const cardBgClass = isDark
        ? "bg-black/40 border-white/10 backdrop-blur-xl"
        : "bg-white/60 border-zinc-200 backdrop-blur-xl shadow-lg shadow-zinc-200/50";
    const cardLabelClass = isDark ? "text-white/40" : "text-zinc-500";

    // History Container
    const historyContainerClass = isDark
        ? "bg-black/40 border-white/20 backdrop-blur-2xl shadow-2xl"
        : "bg-white border-zinc-200 shadow-xl shadow-zinc-200/50";

    const historyHeaderClass = isDark ? "bg-white/5 border-white/10" : "bg-zinc-50 border-zinc-200";
    const historyHeaderTextClass = isDark ? "text-white/40" : "text-zinc-400";

    const emptyStateTextClass = isDark ? "text-white/40" : "text-zinc-400";
    const emptyIconBgClass = isDark ? "bg-white/5" : "bg-zinc-100";
    const emptyIconClass = isDark ? "text-white/20" : "text-zinc-300";

    // List Items
    const itemBorderClass = isDark ? "divide-white/5" : "divide-zinc-100";
    const itemHoverClass = isDark ? "hover:bg-white/5" : "hover:bg-zinc-50";
    const timeTextClass = isDark ? "text-white/40" : "text-zinc-400";
    const linkHoverClass = isDark ? "hover:bg-white/10 text-white/40 hover:text-white" : "hover:bg-zinc-100 text-zinc-400 hover:text-zinc-900";

    useEffect(() => {
        fetchHistory()
    }, [])

    const fetchHistory = async () => {
        const token = localStorage.getItem('token')
        if (!token) {
            window.location.href = ROUTES.LOGIN
            return
        }

        try {
            const userRes = await api.get("/users/me")
            setUser(userRes.data)

            if (userRes.data.submissions) {
                const sorted = [...userRes.data.submissions].sort((a, b) => b.id - a.id);
                setHistory(sorted);
            }
        } catch (err) {
            console.error("Dashboard fetch error:", err);
            if (err.response && err.response.status === 401) {
                localStorage.removeItem('token')
                window.location.href = ROUTES.LOGIN
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className={`w-full min-h-screen p-6 md:p-12 font-sans relative z-10 ${mainTextClass}`}>
            <div className="max-w-5xl mx-auto space-y-8">

                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
                        <p className={`mt-1 ${subTextClass}`}>
                            Welcome back, {user?.first_name || 'User'}
                        </p>
                    </div>
                </div>

                {/* Stats / Overview */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className={`rounded-2xl p-6 border ${cardBgClass}`}>
                        <div className={`text-sm font-medium uppercase tracking-wider mb-2 ${cardLabelClass}`}>Total Forms</div>
                        <div className="text-4xl font-bold">{history.length}</div>
                    </div>
                    <div className={`rounded-2xl p-6 border ${cardBgClass}`}>
                        <div className={`text-sm font-medium uppercase tracking-wider mb-2 ${cardLabelClass}`}>Success Rate</div>
                        <div className="text-4xl font-bold text-green-400">
                            {history.length > 0
                                ? Math.round((history.filter(h => h.status === 'Success').length / history.length) * 100)
                                : 0}%
                        </div>
                    </div>
                </div>

                {/* History List */}
                <div className={`rounded-3xl overflow-hidden min-h-[400px] border ${historyContainerClass}`}>
                    {/* Window Header */}
                    <div className={`p-4 flex items-center border-b shrink-0 gap-4 ${historyHeaderClass}`}>
                        <div className="flex gap-2">
                            <div className="w-3 h-3 rounded-full bg-red-400/80"></div>
                            <div className="w-3 h-3 rounded-full bg-yellow-400/80"></div>
                            <div className="w-3 h-3 rounded-full bg-green-400/80"></div>
                        </div>
                        <div className={`text-xs font-semibold font-mono uppercase tracking-widest ${historyHeaderTextClass}`}>
                            submission_history.log
                        </div>
                    </div>

                    <div className="p-0">
                        {loading ? (
                            <div className={`p-12 text-center ${emptyStateTextClass}`}>Loading history...</div>
                        ) : history.length === 0 ? (
                            <div className="p-12 text-center flex flex-col items-center gap-4">
                                <div className={`w-16 h-16 rounded-full flex items-center justify-center ${emptyIconBgClass}`}>
                                    <FileText className={`h-8 w-8 ${emptyIconClass}`} />
                                </div>
                                <p className={emptyStateTextClass}>No forms submitted yet.</p>
                                <a href={ROUTES.HOME} className="text-green-400 hover:underline">Fill your first form</a>
                            </div>
                        ) : (
                            <div className={`divide-y ${itemBorderClass}`}>
                                {history.map((item) => {
                                    const ratingEmojis = ["😔", "😕", "😐", "🙂", "😍"];
                                    const localFeedback = JSON.parse(localStorage.getItem('form_feedback_history') || '{}');
                                    const feedback = localFeedback[item.form_url];
                                    const emoji = feedback ? ratingEmojis[feedback.rating - 1] : null;

                                    return (
                                        <motion.div
                                            key={item.id}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className={`p-5 flex items-center justify-between transition-colors group ${itemHoverClass}`}
                                        >
                                            <div className="flex items-center gap-4">
                                                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${item.status === 'Success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                                                    }`}>
                                                    {item.status === 'Success' ? <CheckCircle2 className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
                                                </div>
                                                <div>
                                                    <div className={`font-medium group-hover:text-green-500 transition-colors truncate max-w-[300px] md:max-w-[500px] flex items-center gap-2 ${mainTextClass}`}>
                                                        {item.form_url}
                                                        {emoji && (
                                                            <span title={`You rated this: ${feedback.rating}/5`} className={`text-lg w-7 h-7 rounded-full flex items-center justify-center -ml-1 shadow-sm border ${isDark ? 'bg-white/10 border-white/5' : 'bg-zinc-100 border-zinc-200'}`}>
                                                                {emoji}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className={`text-xs flex items-center gap-2 mt-1 ${timeTextClass}`}>
                                                        <Clock className="h-3 w-3" />
                                                        {new Date(item.timestamp).toLocaleString(undefined, {
                                                            dateStyle: 'medium',
                                                            timeStyle: 'short'
                                                        })}
                                                    </div>
                                                </div>
                                            </div>

                                            <a
                                                href={item.form_url}
                                                target="_blank"
                                                rel="noreferrer"
                                                className={`p-2 rounded-lg transition-colors ${linkHoverClass}`}
                                                title="Open Form URL"
                                            >
                                                <ExternalLink className="h-5 w-5" />
                                            </a>
                                        </motion.div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
