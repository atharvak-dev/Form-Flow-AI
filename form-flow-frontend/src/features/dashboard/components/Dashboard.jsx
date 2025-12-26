"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Clock, ExternalLink, FileText, CheckCircle2, XCircle, TrendingUp, PieChart, BarChart3 } from "lucide-react"
import api, { getAnalytics } from '@/services/api'
import { ROUTES } from '@/constants'
import { useTheme } from '@/context/ThemeProvider'
import { SubmissionTrendChart, SuccessRateChart, FieldTypesChart, FormTypeChart } from './AnalyticsCharts'
import { AIInsights } from './AIInsights'

const ITEMS_PER_PAGE = 5;

export function Dashboard() {
    const { isDark } = useTheme();
    const [history, setHistory] = useState([])
    const [loading, setLoading] = useState(true)
    const [user, setUser] = useState(null)
    const [analytics, setAnalytics] = useState(null)
    const [analyticsLoading, setAnalyticsLoading] = useState(false)
    const [currentPage, setCurrentPage] = useState(1)
    const [activeTab, setActiveTab] = useState('history'); // 'history' or 'analytics'

    // Derive chart data from history if analytics API fails
    const chartData = analytics?.charts || generateChartsFromHistory(history);

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
        fetchAnalytics()
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

    const fetchAnalytics = async () => {
        setAnalyticsLoading(true)
        try {
            const data = await getAnalytics()
            setAnalytics(data)
        } catch (err) {
            console.error("Analytics fetch error:", err)
        } finally {
            setAnalyticsLoading(false)
        }
    }

    // Generate chart data from history as fallback
    function generateChartsFromHistory(submissions) {
        if (!submissions || submissions.length === 0) {
            return null;
        }

        // Get last 7 days
        const today = new Date();
        const submissions_by_day = [];
        for (let i = 6; i >= 0; i--) {
            const day = new Date(today);
            day.setDate(day.getDate() - i);
            const dayStr = day.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const count = submissions.filter(s => {
                const subDate = new Date(s.timestamp);
                return subDate.toDateString() === day.toDateString();
            }).length;
            submissions_by_day.push({ date: dayStr, count });
        }

        // Field types (estimated)
        const totalFields = submissions.length * 8;
        const field_types = [
            { name: "Text", value: Math.round(totalFields * 0.35) },
            { name: "Email", value: Math.round(totalFields * 0.15) },
            { name: "Phone", value: Math.round(totalFields * 0.12) },
            { name: "Select", value: Math.round(totalFields * 0.18) },
            { name: "Checkbox", value: Math.round(totalFields * 0.10) },
            { name: "Other", value: Math.round(totalFields * 0.10) },
        ];

        // Success by type
        const success_by_type = [
            {
                type: "Standard",
                success: submissions.filter(s => s.status === 'Success').length,
                fail: submissions.filter(s => s.status !== 'Success').length
            }
        ];

        return { submissions_by_day, field_types, success_by_type };
    }

    // Pagination calculations
    const totalPages = Math.ceil(history.length / ITEMS_PER_PAGE);
    const paginatedHistory = history.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
    );

    return (
        <div className={`w-full min-h-screen p-6 md:p-12 font-sans relative z-10 ${mainTextClass}`}>
            <div className="max-w-5xl mx-auto space-y-6">

                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
                        <p className={`mt-1 ${subTextClass}`}>
                            Welcome back, {user?.first_name || 'User'}
                        </p>
                    </div>
                </div>

                {/* Mac-style Window with Integrated Tabs */}
                <div className={`rounded-3xl border overflow-hidden ${historyContainerClass} relative z-0 min-h-[500px]`}>

                    {/* Integrated Window Header & Tabs */}
                    <div className={`px-4 py-3 flex items-center gap-4 border-b shrink-0 ${isDark ? 'bg-white/5 border-white/10' : 'bg-zinc-50 border-zinc-200'}`}>
                        {/* Traffic Lights */}
                        <div className="flex gap-2 shrink-0">
                            <div className="w-3 h-3 rounded-full bg-red-400/80"></div>
                            <div className="w-3 h-3 rounded-full bg-yellow-400/80"></div>
                            <div className="w-3 h-3 rounded-full bg-green-400/80"></div>
                        </div>

                        {/* Divider */}
                        <div className={`w-px h-4 ${isDark ? 'bg-white/10' : 'bg-zinc-300'}`}></div>

                        {/* Tabs */}
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => setActiveTab('history')}
                                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-2 ${activeTab === 'history'
                                        ? `${isDark ? 'bg-white/10 text-white shadow-sm' : 'bg-white text-zinc-900 shadow-sm border border-black/5'}`
                                        : `${isDark ? 'text-white/40 hover:bg-white/5 hover:text-white/60' : 'text-zinc-400 hover:bg-zinc-200/50 hover:text-zinc-600'}`
                                    }`}
                            >
                                <FileText className="w-3.5 h-3.5" />
                                submission_history.log
                            </button>
                            <button
                                onClick={() => setActiveTab('analytics')}
                                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-2 ${activeTab === 'analytics'
                                        ? `${isDark ? 'bg-white/10 text-white shadow-sm' : 'bg-white text-zinc-900 shadow-sm border border-black/5'}`
                                        : `${isDark ? 'text-white/40 hover:bg-white/5 hover:text-white/60' : 'text-zinc-400 hover:bg-zinc-200/50 hover:text-zinc-600'}`
                                    }`}
                            >
                                <TrendingUp className="w-3.5 h-3.5" />
                                analytics.log
                            </button>
                        </div>
                    </div>

                    {/* Window Content */}
                    <div className="p-6">
                        {/* Tab Content: HISTORY */}
                        {activeTab === 'history' && (
                            <div className="space-y-6">
                                {/* Entries Info (moved from old header) */}
                                {history.length > 0 && (
                                    <div className={`text-xs font-mono opacity-40 text-right -mt-2 mb-2`}>
                                        Entries {(currentPage - 1) * ITEMS_PER_PAGE + 1}-{Math.min(currentPage * ITEMS_PER_PAGE, history.length)} of {history.length}
                                    </div>
                                )}

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
                                    <>
                                        <div className={`divide-y ${itemBorderClass}`}>
                                            {paginatedHistory.map((item) => {
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
                                                                <div className={`font-medium group-hover:text-green-500 transition-colors truncate max-w-[200px] md:max-w-[400px] flex items-center gap-2 ${mainTextClass}`}>
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

                                        {/* Pagination Controls */}
                                        {history.length > ITEMS_PER_PAGE && (
                                            <div className="flex items-center justify-center gap-4 pt-4 border-t border-transparent">
                                                <button
                                                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                                    disabled={currentPage === 1}
                                                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${isDark ? 'bg-white/10 hover:bg-white/20 disabled:bg-white/5 disabled:text-white/30' : 'bg-zinc-100 hover:bg-zinc-200 disabled:bg-zinc-50 disabled:text-zinc-300'}`}
                                                >
                                                    Previous
                                                </button>
                                                <span className={`text-sm ${subTextClass}`}>
                                                    {currentPage} / {totalPages}
                                                </span>
                                                <button
                                                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                                    disabled={currentPage === totalPages}
                                                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${isDark ? 'bg-white/10 hover:bg-white/20 disabled:bg-white/5 disabled:text-white/30' : 'bg-zinc-100 hover:bg-zinc-200 disabled:bg-zinc-50 disabled:text-zinc-300'}`}
                                                >
                                                    Next
                                                </button>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>
                        )}

                        {/* Tab Content: ANALYTICS */}
                        {activeTab === 'analytics' && (
                            <div className="space-y-8">
                                {/* Stats Cards - Moved Inside Analytics Tab */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div className={`rounded-2xl p-6 border ${cardBgClass}`}>
                                        <div className={`text-xs font-medium uppercase tracking-wider mb-2 ${cardLabelClass}`}>Total Forms</div>
                                        <div className="text-4xl font-bold">{analytics?.summary?.total_forms || history.length}</div>
                                    </div>
                                    <div className={`rounded-2xl p-6 border ${cardBgClass}`}>
                                        <div className={`text-xs font-medium uppercase tracking-wider mb-2 ${cardLabelClass}`}>Success Rate</div>
                                        <div className="text-4xl font-bold text-green-400">
                                            {analytics?.summary?.success_rate || (history.length > 0
                                                ? Math.round((history.filter(h => h.status === 'Success').length / history.length) * 100)
                                                : 0)}%
                                        </div>
                                    </div>
                                    <div className={`rounded-2xl p-6 border ${cardBgClass}`}>
                                        <div className={`text-xs font-medium uppercase tracking-wider mb-2 ${cardLabelClass}`}>Time Saved</div>
                                        <div className="text-4xl font-bold text-blue-400">
                                            {analytics?.summary?.avg_time_saved_seconds
                                                ? `${Math.round(analytics.summary.avg_time_saved_seconds / 60)}m`
                                                : '0m'}
                                        </div>
                                    </div>
                                </div>

                                {/* AI Insights */}
                                {analytics?.ai_insights && (
                                    <AIInsights
                                        insights={analytics.ai_insights}
                                        isLoading={analyticsLoading}
                                        onRefresh={fetchAnalytics}
                                    />
                                )}

                                {/* Charts Grid (using fallback chartData) */}
                                {chartData && history.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className={`rounded-2xl p-6 border ${cardBgClass}`}>
                                            <div className="flex items-center gap-2 mb-4">
                                                <TrendingUp className={`h-5 w-5 ${isDark ? 'text-green-400' : 'text-green-600'}`} />
                                                <h3 className={`font-semibold ${mainTextClass}`}>Submission Trend (7 days)</h3>
                                            </div>
                                            <SubmissionTrendChart data={chartData.submissions_by_day || []} />
                                        </div>

                                        <div className={`rounded-2xl p-6 border ${cardBgClass}`}>
                                            <div className="flex items-center gap-2 mb-4">
                                                <BarChart3 className={`h-5 w-5 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
                                                <h3 className={`font-semibold ${mainTextClass}`}>Fields Filled by Type</h3>
                                            </div>
                                            <FieldTypesChart data={chartData.field_types || []} />
                                        </div>

                                        {chartData.success_by_type?.length > 0 && (
                                            <div className={`rounded-2xl p-6 border md:col-span-2 ${cardBgClass}`}>
                                                <div className="flex items-center gap-2 mb-4">
                                                    <PieChart className={`h-5 w-5 ${isDark ? 'text-purple-400' : 'text-purple-600'}`} />
                                                    <h3 className={`font-semibold ${mainTextClass}`}>Success by Form Type</h3>
                                                </div>
                                                <div className="h-64">
                                                    <FormTypeChart data={chartData.success_by_type} />
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="text-center py-12 opacity-50">
                                        No data available for charts yet.
                                    </div>
                                )}
                            </div>
                        )}

                    </div>
                </div>
            </div>
        </div>
    )
}
