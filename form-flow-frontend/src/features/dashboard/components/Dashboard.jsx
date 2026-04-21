"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
    Clock, ExternalLink, FileText, CheckCircle2, XCircle, TrendingUp,
    PieChart, BarChart3, User, Sparkles, Target, Zap, Activity,
    ArrowUpRight, Trophy, Flame, Calendar, Puzzle
} from "lucide-react"
import api, { getAnalytics } from '@/services/api'
import { ROUTES } from '@/constants'
import { useTheme } from '@/context/ThemeProvider'
import { SubmissionTrendChart, SuccessRateChart, FieldTypesChart, FormTypeChart, TopDomainsChart, ActivityHourlyChart } from './AnalyticsCharts'
import { AIInsights } from './AIInsights'
import { ProfileSettings } from './ProfileSettings'
import { PluginDashboard } from '@/features/plugins'

const ITEMS_PER_PAGE = 5;

// ─── Glassmorphism BentoCard ──────────────────────────────────────────────────
// Matches the landing page FeatureCard aesthetic: gradient border wrapper,
// backdrop-blur glass inner, hover spotlight, radial dot grid overlay.
function BentoCard({ children, className = "", size = "default", glow = false, accent = null }) {
    const { isDark } = useTheme();

    const sizeClasses = {
        default: 'p-5',
        lg: 'p-6',
        xl: 'p-8',
        compact: 'p-4',
        none: 'p-0',
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className={`group relative rounded-3xl p-[1px] overflow-hidden transition-all duration-500 ${className}`}
        >
            {/* Animated Border Gradient */}
            <div className={`absolute inset-0 bg-gradient-to-br opacity-100 transition-opacity duration-500 ${isDark
                ? 'from-zinc-700/50 via-zinc-800/10 to-transparent'
                : 'from-zinc-300 via-zinc-200/50 to-transparent'
                }`} />

            {/* Hover Spotlight Effect */}
            <div className={`absolute inset-0 bg-gradient-to-br from-emerald-500/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

            {/* Glow Effect */}
            {glow && isDark && (
                <div className="absolute -inset-1 bg-emerald-500/10 blur-2xl rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
            )}

            {/* Inner Content - Glassy Background */}
            <div className={`relative h-full flex flex-col rounded-[calc(1.5rem-1px)] overflow-hidden transition-colors duration-500 ${sizeClasses[size]} ${isDark
                ? 'bg-zinc-900/40 backdrop-blur-sm'
                : 'bg-white/80 shadow-[0_2px_8px_rgba(0,0,0,0.04)] backdrop-blur-sm'
                }`}>
                {/* Subtle radial grid pattern overlay */}
                <div className={`absolute inset-0 pointer-events-none opacity-[0.03] ${isDark
                    ? 'bg-[radial-gradient(#fff_1px,transparent_1px)]'
                    : 'bg-[radial-gradient(#000_1px,transparent_1px)]'
                    } [background-size:16px_16px]`} />

                {/* Content */}
                <div className="relative z-10 h-full">
                    {children}
                </div>
            </div>
        </motion.div>
    );
}

// ─── Terminal Window Chrome ───────────────────────────────────────────────────
// macOS-inspired window header, matching form-filler's FormCompletion.jsx
function TerminalHeader({ title, icon: Icon }) {
    const { isDark } = useTheme();
    return (
        <div className={`flex items-center justify-between px-6 py-4 border-b ${isDark
            ? 'bg-[#18181A]/80 border-white/[0.06]'
            : 'bg-zinc-100/80 border-zinc-200/60'
            }`}>
            <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-red-400/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-400/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-400/80"></div>
            </div>
            <div className={`text-[10px] font-semibold flex items-center gap-2 font-mono uppercase tracking-[0.2em] ${isDark ? 'text-white/30' : 'text-zinc-400'
                }`}>
                {Icon && <Icon size={11} />}
                {title}
            </div>
            <div className="w-14"></div>
        </div>
    );
}

// ─── Stat Card with icon and trend ────────────────────────────────────────────
function StatCard({ icon: Icon, label, value, trend, color = "green", delay = 0 }) {
    const { isDark } = useTheme();

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay, duration: 0.4 }}
            className="flex items-center gap-4"
        >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center border ${isDark
                ? 'bg-emerald-500/10 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.15)]'
                : 'bg-emerald-50 border-emerald-200'
                }`}>
                <Icon className={`w-5 h-5 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
            </div>
            <div className="flex-1">
                <p className={`text-[10px] font-semibold uppercase tracking-[0.15em] ${isDark ? 'text-white/40' : 'text-zinc-500'}`}>
                    {label}
                </p>
                <div className="flex items-baseline gap-2">
                    <span className={`text-2xl font-bold tracking-tight font-mono ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                        {value}
                    </span>
                    {trend && (
                        <span className={`text-xs font-medium flex items-center gap-0.5 ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            <ArrowUpRight className={`w-3 h-3 ${trend < 0 ? 'rotate-180' : ''}`} />
                            {Math.abs(trend)}%
                        </span>
                    )}
                </div>
            </div>
        </motion.div>
    );
}

export function Dashboard() {
    const { isDark } = useTheme();
    const [history, setHistory] = useState([])
    const [loading, setLoading] = useState(true)
    const [user, setUser] = useState(null)
    const [analytics, setAnalytics] = useState(null)
    const [analyticsLoading, setAnalyticsLoading] = useState(false)
    const [currentPage, setCurrentPage] = useState(1)
    const [activeTab, setActiveTab] = useState('analytics');

    // Ensure chartData always has valid structure
    const rawChartData = analytics?.charts || generateChartsFromHistory(history);
    const chartData = rawChartData || {
        submissions_by_day: [],
        activity_by_hour: [],
        field_types: [],
        top_domains: [],
        form_types: []
    };

    // Calculate stats
    const successRate = analytics?.summary?.success_rate ||
        (history.length > 0 ? Math.round((history.filter(h => h.status === 'Success').length / history.length) * 100) : 0);
    const timeSaved = analytics?.summary?.avg_time_saved_seconds
        ? `${Math.round(analytics.summary.avg_time_saved_seconds / 60)}m`
        : `${history.length * 3}m`;
    const totalForms = analytics?.summary?.total_forms || history.length;
    const streakDays = analytics?.summary?.streak_days || 0;

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

    function generateChartsFromHistory(submissions) {
        if (!submissions || submissions.length === 0) return null;

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

        const totalFields = submissions.length * 8;
        const field_types = [
            { name: "Text", value: Math.round(totalFields * 0.35) },
            { name: "Email", value: Math.round(totalFields * 0.15) },
            { name: "Phone", value: Math.round(totalFields * 0.12) },
            { name: "Select", value: Math.round(totalFields * 0.18) },
            { name: "Checkbox", value: Math.round(totalFields * 0.10) },
            { name: "Other", value: Math.round(totalFields * 0.10) },
        ];

        const success_by_type = [{
            type: "Standard",
            success: submissions.filter(s => s.status === 'Success').length,
            fail: submissions.filter(s => s.status !== 'Success').length
        }];

        const domainCounts = {};
        submissions.forEach(s => {
            try {
                const hostname = new URL(s.form_url).hostname.replace('www.', '');
                domainCounts[hostname] = (domainCounts[hostname] || 0) + 1;
            } catch (e) { }
        });
        const top_domains = Object.entries(domainCounts)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 5);

        const hours = Array(24).fill(0).map((_, i) => ({ hour: i, count: 0 }));
        submissions.forEach(s => {
            const h = new Date(s.timestamp).getHours();
            if (hours[h]) hours[h].count++;
        });

        return { submissions_by_day, field_types, success_by_type, top_domains, activity_by_hour: hours };
    }

    const totalPages = Math.ceil(history.length / ITEMS_PER_PAGE);
    const paginatedHistory = history.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

    // Tab config
    const tabs = [
        { id: 'analytics', label: 'Analytics', icon: TrendingUp },
        { id: 'history', label: 'History', icon: FileText },
        { id: 'plugins', label: 'Plugins', icon: Puzzle },
        { id: 'profile', label: 'Profile', icon: User },
    ];

    return (
        <div className={`w-full min-h-screen font-sans relative z-10 ${isDark ? 'text-white' : 'text-zinc-900'}`}>

            {/* Ambient Spotlights — matching landing page FeaturesGrid */}
            {isDark && (
                <>
                    <div className="absolute top-0 left-1/4 w-[1000px] h-[400px] bg-emerald-900/10 rounded-[100%] blur-[120px] pointer-events-none" />
                    <div className="absolute bottom-0 right-1/4 w-[800px] h-[600px] bg-emerald-900/5 rounded-[100%] blur-[120px] pointer-events-none" />
                </>
            )}

            <div className="max-w-7xl mx-auto px-6 py-8 space-y-8 relative">

                {/* ─── Header Section ──────────────────────────────────────────── */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-12 pt-8 pb-4"
                >
                    <div className="space-y-5">
                        {/* Badge — matching landing page style */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className={`
                                inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-semibold uppercase tracking-wider backdrop-blur-sm
                                ${isDark
                                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                                    : 'bg-emerald-50 border-emerald-200 text-emerald-700'
                                }
                            `}
                        >
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </span>
                            System Online
                        </motion.div>

                        <h1 className={`text-4xl md:text-5xl font-semibold tracking-tight leading-[1.1] ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                            {user?.first_name || 'Commander'}'s{' '}
                            <span className={isDark ? 'text-zinc-500' : 'text-zinc-400'}>Command Center</span>
                        </h1>
                    </div>

                    {/* Tab Switcher — refined pill nav matching EditorialTeam */}
                    <div className={`
                        inline-flex items-center gap-1 p-1.5 rounded-full border backdrop-blur-xl
                        ${isDark
                            ? 'bg-zinc-900/40 border-white/[0.05] shadow-2xl'
                            : 'bg-white/60 border-zinc-200/50 shadow-xl shadow-zinc-200/20'
                        }
                    `}>
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`
                                    relative flex items-center gap-2.5 px-5 py-2.5 rounded-full text-[11px] font-bold uppercase tracking-[0.15em] transition-all duration-500
                                    ${activeTab === tab.id
                                        ? isDark ? 'text-black' : 'text-white'
                                        : isDark ? 'text-zinc-500 hover:text-white' : 'text-zinc-400 hover:text-zinc-900'
                                    }
                                `}
                            >
                                {activeTab === tab.id && (
                                    <motion.div
                                        layoutId="dashboard-tab-bg"
                                        className={`absolute inset-0 rounded-full z-0 shadow-lg ${isDark ? 'bg-white' : 'bg-zinc-900 shadow-zinc-900/40'}`}
                                        transition={{ type: "spring", bounce: 0.15, duration: 0.6 }}
                                    />
                                )}
                                <tab.icon className={`w-3.5 h-3.5 relative z-10 transition-transform duration-500 ${activeTab === tab.id ? 'scale-110' : ''}`} />
                                <span className="relative z-10 hidden sm:inline">{tab.label}</span>
                            </button>
                        ))}
                    </div>
                </motion.div>

                {/* ─── Tab Content ──────────────────────────────────────────────── */}
                <AnimatePresence mode="wait">

                    {/* ── Analytics Tab ─────────────────────────────────────────── */}
                    {activeTab === 'analytics' && (
                        <motion.div
                            key="analytics"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.3 }}
                            className="space-y-6"
                        >
                            {/* Top Stats Row */}
                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                                <BentoCard>
                                    <StatCard icon={Target} label="Total Forms" value={totalForms} trend={12} delay={0} />
                                </BentoCard>
                                <BentoCard>
                                    <StatCard icon={CheckCircle2} label="Success Rate" value={`${successRate}%`} delay={0.1} />
                                </BentoCard>
                                <BentoCard>
                                    <StatCard icon={Clock} label="Time Saved" value={timeSaved} delay={0.2} />
                                </BentoCard>
                                <BentoCard>
                                    <StatCard icon={Flame} label="Day Streak" value={streakDays || history.length} delay={0.3} />
                                </BentoCard>
                            </div>

                            {/* Main Bento Grid */}
                            <div className="grid grid-cols-12 gap-4 auto-rows-[minmax(140px,auto)]">

                                {/* AI Insights - Featured Card */}
                                <BentoCard className="col-span-12 lg:col-span-5 row-span-2" size="lg" glow>
                                    <div className="h-full flex flex-col">
                                        <div className="flex items-center gap-3 mb-4">
                                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${isDark
                                                ? 'bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
                                                : 'bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200'
                                                }`}>
                                                <Sparkles className={`w-5 h-5 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
                                            </div>
                                            <div>
                                                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-zinc-900'}`}>AI Insights</h3>
                                                <p className={`text-xs ${isDark ? 'text-white/40' : 'text-zinc-500'}`}>Powered by machine learning</p>
                                            </div>
                                        </div>
                                        <div className="flex-1 overflow-hidden">
                                            <AIInsights
                                                insights={analytics?.ai_insights}
                                                isLoading={analyticsLoading}
                                                onRefresh={fetchAnalytics}
                                            />
                                        </div>
                                    </div>
                                </BentoCard>

                                {/* Activity Trend Chart */}
                                <BentoCard className="col-span-12 lg:col-span-7 row-span-2" size="lg">
                                    <div className="h-full flex flex-col">
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center gap-3">
                                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${isDark
                                                    ? 'bg-emerald-500/10 border-emerald-500/20'
                                                    : 'bg-emerald-50 border-emerald-200'
                                                    }`}>
                                                    <TrendingUp className={`w-5 h-5 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
                                                </div>
                                                <div>
                                                    <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-zinc-900'}`}>Activity Trend</h3>
                                                    <p className={`text-xs ${isDark ? 'text-white/40' : 'text-zinc-500'}`}>Last 7 days</p>
                                                </div>
                                            </div>
                                            <div className={`px-3 py-1 rounded-full text-xs font-medium border ${isDark
                                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                                : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                                }`}>
                                                <Calendar className="w-3 h-3 inline mr-1" />
                                                Weekly
                                            </div>
                                        </div>
                                        <div className="h-[200px]">
                                            <SubmissionTrendChart data={chartData?.submissions_by_day || []} />
                                        </div>
                                    </div>
                                </BentoCard>

                                {/* Success Rate Donut */}
                                <BentoCard className="col-span-6 lg:col-span-4 row-span-2" size="lg">
                                    <div className="h-full flex flex-col">
                                        <div className="flex items-center gap-2 mb-2">
                                            <PieChart className={`w-4 h-4 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
                                            <h3 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-zinc-900'}`}>Success Rate</h3>
                                        </div>
                                        <div className="h-[160px]">
                                            <SuccessRateChart successRate={successRate} />
                                        </div>
                                    </div>
                                </BentoCard>

                                {/* Hourly Activity */}
                                <BentoCard className="col-span-6 lg:col-span-4" size="compact">
                                    <div className="h-full flex flex-col">
                                        <div className="flex items-center gap-2 mb-3">
                                            <Activity className={`w-4 h-4 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
                                            <h3 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-zinc-900'}`}>Peak Hours</h3>
                                        </div>
                                        <div className="h-[100px]">
                                            <ActivityHourlyChart data={chartData?.activity_by_hour || []} />
                                        </div>
                                    </div>
                                </BentoCard>

                                {/* Field Composition */}
                                <BentoCard className="col-span-12 lg:col-span-4 row-span-2" size="lg">
                                    <div className="h-full flex flex-col">
                                        <div className="flex items-center gap-2 mb-4">
                                            <BarChart3 className={`w-4 h-4 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
                                            <h3 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-zinc-900'}`}>Field Types</h3>
                                        </div>
                                        <p className={`text-xs mb-4 ${isDark ? 'text-white/40' : 'text-zinc-500'}`}>
                                            Breakdown of all input types filled
                                        </p>
                                        <div className="h-[120px]">
                                            <FieldTypesChart data={chartData?.field_types || []} />
                                        </div>
                                        {/* Legend */}
                                        <div className={`grid grid-cols-3 gap-2 mt-4 pt-4 border-t ${isDark ? 'border-white/[0.06]' : 'border-zinc-200/50'}`}>
                                            {(chartData?.field_types || []).slice(0, 6).map((type, i) => (
                                                <div key={type.name} className="flex items-center gap-1.5 text-[10px]">
                                                    <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: ['#10B981', '#14B8A6', '#22C55E', '#84CC16', '#34D399', '#6EE7B7'][i] }} />
                                                    <span className={isDark ? 'text-white/60' : 'text-zinc-600'}>{type.name}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </BentoCard>

                                {/* Top Domains */}
                                <BentoCard className="col-span-12 lg:col-span-4" size="compact">
                                    <div className="h-full flex flex-col">
                                        <div className="flex items-center gap-2 mb-3">
                                            <ExternalLink className={`w-4 h-4 ${isDark ? 'text-teal-400' : 'text-teal-600'}`} />
                                            <h3 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-zinc-900'}`}>Top Domains</h3>
                                        </div>
                                        <div className="h-[100px]">
                                            <TopDomainsChart data={chartData?.top_domains || []} />
                                        </div>
                                    </div>
                                </BentoCard>

                            </div>
                        </motion.div>
                    )}

                    {/* ── History Tab — Immersive Timeline ──────────────────────── */}
                    {activeTab === 'history' && (
                        <motion.div
                            key="history"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.4 }}
                            className="space-y-6"
                        >
                            {/* ── Summary Stats Bar ───────────────────────────────── */}
                            {history.length > 0 && (
                                <div className="grid grid-cols-3 gap-4">
                                    {[
                                        { label: 'Total Submissions', value: history.length, icon: FileText, color: 'emerald' },
                                        { label: 'Successful', value: history.filter(h => h.status === 'Success').length, icon: CheckCircle2, color: 'emerald' },
                                        { label: 'Failed', value: history.filter(h => h.status !== 'Success').length, icon: XCircle, color: 'red' },
                                    ].map((stat, i) => (
                                        <BentoCard key={stat.label} size="compact">
                                            <motion.div
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: i * 0.1 }}
                                                className="flex items-center gap-3"
                                            >
                                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${isDark
                                                    ? `bg-${stat.color}-500/10 border-${stat.color}-500/20`
                                                    : `bg-${stat.color}-50 border-${stat.color}-200`
                                                    }`}>
                                                    <stat.icon className={`w-5 h-5 ${isDark ? `text-${stat.color}-400` : `text-${stat.color}-600`}`} />
                                                </div>
                                                <div>
                                                    <p className={`text-[10px] font-semibold uppercase tracking-[0.15em] ${isDark ? 'text-white/40' : 'text-zinc-500'}`}>
                                                        {stat.label}
                                                    </p>
                                                    <p className={`text-xl font-bold font-mono tracking-tight ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                                                        {stat.value}
                                                    </p>
                                                </div>
                                            </motion.div>
                                        </BentoCard>
                                    ))}
                                </div>
                            )}

                            {/* ── Main History Card ──────────────────────────────── */}
                            <BentoCard size="none" className="min-h-[500px] !rounded-3xl overflow-hidden flex flex-col">
                                {/* Terminal chrome header */}
                                <div className="flex-none">
                                    <TerminalHeader title="submission_history.log" icon={FileText} />
                                </div>

                                {/* Activity Log Toolbar */}
                                <div className={`flex-none flex flex-col sm:flex-row items-start sm:items-center justify-between px-6 py-5 border-b backdrop-blur-md transition-colors ${isDark ? 'bg-black/20 border-white/[0.06]' : 'bg-white/40 border-zinc-200/60'}`}>
                                    <div className="flex items-center gap-4">
                                        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border shadow-sm ${isDark
                                            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 shadow-emerald-500/10'
                                            : 'bg-gradient-to-b from-emerald-50 to-emerald-100/50 border-emerald-200 text-emerald-600'
                                            }`}>
                                            <FileText className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <h3 className={`font-semibold text-lg tracking-tight ${isDark ? 'text-white' : 'text-zinc-900'}`}>Activity Log</h3>
                                            <p className={`text-sm ${isDark ? 'text-white/50' : 'text-zinc-500'}`}>
                                                All form submissions and their outcomes
                                            </p>
                                        </div>
                                    </div>
                                    {history.length > 0 && (
                                        <div className={`mt-4 sm:mt-0 flex items-center gap-2.5 text-xs font-mono px-4 py-2 rounded-xl border backdrop-blur-md shadow-sm ${isDark
                                            ? 'text-zinc-400 bg-zinc-900/50 border-white/[0.08]'
                                            : 'text-zinc-500 bg-white/80 border-zinc-200/80'
                                            }`}>
                                            <Activity className={`w-3.5 h-3.5 ${isDark ? 'text-emerald-500/70' : 'text-emerald-500'}`} />
                                            <span className="flex items-center">
                                                <span className={`font-semibold ${isDark ? 'text-zinc-200' : 'text-zinc-700'}`}>{(currentPage - 1) * ITEMS_PER_PAGE + 1}</span>
                                                <span className="opacity-40 mx-1">-</span>
                                                <span className={`font-semibold ${isDark ? 'text-zinc-200' : 'text-zinc-700'}`}>{Math.min(currentPage * ITEMS_PER_PAGE, history.length)}</span>
                                                <span className="opacity-40 mx-1.5">of</span>
                                                <span className={`font-semibold ${isDark ? 'text-zinc-200' : 'text-zinc-700'}`}>{history.length}</span>
                                            </span>
                                        </div>
                                    )}
                                </div>

                                <div className="flex-1 p-6">

                                    {loading ? (
                                        <div className="flex flex-col items-center justify-center py-20 gap-5">
                                            <div className="relative">
                                                <div className={`w-16 h-16 rounded-full border-2 animate-spin ${isDark
                                                    ? 'border-emerald-500/20 border-t-emerald-500'
                                                    : 'border-emerald-200 border-t-emerald-500'
                                                    }`} />
                                                <FileText className={`absolute inset-0 m-auto w-6 h-6 ${isDark ? 'text-emerald-400/50' : 'text-emerald-500/50'}`} />
                                            </div>
                                            <p className={`font-mono text-sm ${isDark ? 'text-white/30' : 'text-zinc-400'}`}>
                                                Fetching submission logs...
                                            </p>
                                        </div>
                                    ) : history.length === 0 ? (
                                        <div className="flex flex-col items-center justify-center py-20 gap-6">
                                            <div className="relative">
                                                <motion.div
                                                    animate={{ rotate: 360 }}
                                                    transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
                                                    className={`absolute -inset-4 rounded-full blur-2xl opacity-20 ${isDark ? 'bg-emerald-500' : 'bg-emerald-400'}`}
                                                />
                                                <div className={`relative w-24 h-24 rounded-3xl flex items-center justify-center border ${isDark
                                                    ? 'bg-white/[0.03] border-white/[0.06]'
                                                    : 'bg-zinc-50 border-zinc-200'
                                                    }`}>
                                                    <FileText className={`h-10 w-10 ${isDark ? 'text-white/15' : 'text-zinc-300'}`} />
                                                </div>
                                            </div>
                                            <div className="text-center">
                                                <p className={`text-xl font-semibold tracking-tight mb-2 ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                                                    No submissions yet
                                                </p>
                                                <p className={`text-sm max-w-xs mx-auto leading-relaxed ${isDark ? 'text-white/35' : 'text-zinc-400'}`}>
                                                    Start filling forms with AI and your history will appear here as a detailed timeline
                                                </p>
                                            </div>
                                            <motion.a
                                                href={ROUTES.HOME}
                                                whileHover={{ scale: 1.03, y: -2 }}
                                                whileTap={{ scale: 0.97 }}
                                                className={`mt-2 px-8 py-3 rounded-full text-sm font-bold transition-all shadow-lg ${isDark
                                                    ? 'bg-emerald-500 text-white shadow-emerald-500/20 hover:shadow-emerald-500/40'
                                                    : 'bg-zinc-900 text-white shadow-zinc-900/20 hover:shadow-zinc-900/40'
                                                    }`}
                                            >
                                                Fill your first form →
                                            </motion.a>
                                        </div>
                                    ) : (
                                        <>
                                            {/* Timeline Items */}
                                            <div className="space-y-3">
                                                {paginatedHistory.map((item, idx) => {
                                                    const ratingEmojis = ["😔", "😕", "😐", "🙂", "😍"];
                                                    const localFeedback = JSON.parse(localStorage.getItem('form_feedback_history') || '{}');
                                                    const feedback = localFeedback[item.form_url];
                                                    const emoji = feedback ? ratingEmojis[feedback.rating - 1] : null;
                                                    const isSuccess = item.status === 'Success';

                                                    // Parse domain for display
                                                    let domain = item.form_url;
                                                    try { domain = new URL(item.form_url).hostname.replace('www.', ''); } catch(e) {}

                                                    // Time ago
                                                    const timeAgo = (() => {
                                                        const diff = Date.now() - new Date(item.timestamp).getTime();
                                                        const mins = Math.floor(diff / 60000);
                                                        if (mins < 60) return `${mins}m ago`;
                                                        const hrs = Math.floor(mins / 60);
                                                        if (hrs < 24) return `${hrs}h ago`;
                                                        const days = Math.floor(hrs / 24);
                                                        return `${days}d ago`;
                                                    })();

                                                    return (
                                                        <motion.div
                                                            key={item.id}
                                                            initial={{ opacity: 0, y: 12 }}
                                                            animate={{ opacity: 1, y: 0 }}
                                                            transition={{ delay: idx * 0.06, ease: [0.16, 1, 0.3, 1] }}
                                                            className={`
                                                                group relative flex items-center gap-4 p-4 rounded-2xl transition-all duration-300 border
                                                                ${isDark
                                                                    ? 'bg-white/[0.015] border-white/[0.04] hover:bg-white/[0.04] hover:border-white/[0.08]'
                                                                    : 'bg-zinc-50/50 border-zinc-100 hover:bg-white hover:border-zinc-200 hover:shadow-lg hover:shadow-zinc-100/50'
                                                                }
                                                            `}
                                                        >
                                                            {/* Left Accent Border */}
                                                            <div className={`absolute left-0 top-3 bottom-3 w-[3px] rounded-full transition-all duration-300 ${isSuccess
                                                                ? isDark ? 'bg-emerald-500/40 group-hover:bg-emerald-400' : 'bg-emerald-400 group-hover:bg-emerald-500'
                                                                : isDark ? 'bg-red-500/40 group-hover:bg-red-400' : 'bg-red-400 group-hover:bg-red-500'
                                                                }`} />

                                                            {/* Status Icon */}
                                                            <div className={`w-11 h-11 rounded-xl flex items-center justify-center border shrink-0 transition-all duration-300 ${isSuccess
                                                                ? isDark
                                                                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 group-hover:bg-emerald-500/20 group-hover:shadow-[0_0_15px_rgba(16,185,129,0.15)]'
                                                                    : 'bg-emerald-50 text-emerald-600 border-emerald-200 group-hover:bg-emerald-100'
                                                                : isDark
                                                                    ? 'bg-red-500/10 text-red-400 border-red-500/20 group-hover:bg-red-500/20'
                                                                    : 'bg-red-50 text-red-600 border-red-200 group-hover:bg-red-100'
                                                                }`}>
                                                                {isSuccess ? <CheckCircle2 className="h-5 w-5" /> : <XCircle className="h-5 w-5" />}
                                                            </div>

                                                            {/* Content */}
                                                            <div className="flex-1 min-w-0">
                                                                <div className="flex items-center gap-2 mb-1">
                                                                    <span className={`font-semibold text-sm truncate group-hover:text-emerald-400 transition-colors ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                                                                        {domain}
                                                                    </span>
                                                                    {emoji && (
                                                                        <span title={`Rated: ${feedback.rating}/5`} className={`text-sm w-6 h-6 rounded-lg flex items-center justify-center shrink-0 ${isDark ? 'bg-white/[0.06]' : 'bg-zinc-100'}`}>
                                                                            {emoji}
                                                                        </span>
                                                                    )}
                                                                    <span className={`ml-auto text-[10px] font-bold uppercase tracking-widest px-2.5 py-0.5 rounded-full border shrink-0 ${isSuccess
                                                                        ? isDark ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                                                        : isDark ? 'bg-red-500/10 text-red-400 border-red-500/20' : 'bg-red-50 text-red-700 border-red-200'
                                                                        }`}>
                                                                        {isSuccess ? 'Success' : 'Failed'}
                                                                    </span>
                                                                </div>
                                                                <div className={`flex items-center gap-3 text-xs ${isDark ? 'text-white/30' : 'text-zinc-400'}`}>
                                                                    <span className="font-mono truncate max-w-[250px] md:max-w-[400px]">{item.form_url}</span>
                                                                    <span className={`shrink-0 ${isDark ? 'text-white/15' : 'text-zinc-300'}`}>·</span>
                                                                    <span className="flex items-center gap-1 shrink-0 font-medium">
                                                                        <Clock className="h-3 w-3" />
                                                                        {timeAgo}
                                                                    </span>
                                                                </div>
                                                            </div>

                                                            {/* Action */}
                                                            <a
                                                                href={item.form_url}
                                                                target="_blank"
                                                                rel="noreferrer"
                                                                className={`p-2.5 rounded-xl transition-all shrink-0 opacity-0 group-hover:opacity-100 ${isDark
                                                                    ? 'hover:bg-white/10 text-white/40 hover:text-emerald-400'
                                                                    : 'hover:bg-zinc-100 text-zinc-400 hover:text-emerald-600'
                                                                    }`}
                                                                title="Open original form"
                                                            >
                                                                <ExternalLink className="h-4 w-4" />
                                                            </a>
                                                        </motion.div>
                                                    );
                                                })}
                                            </div>

                                            {/* Pagination — Elegant */}
                                            {history.length > ITEMS_PER_PAGE && (
                                                <div className={`flex items-center justify-between pt-8 mt-8 border-t ${isDark ? 'border-white/[0.06]' : 'border-zinc-200/50'}`}>
                                                    <button
                                                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                                        disabled={currentPage === 1}
                                                        className={`px-5 py-2.5 text-xs font-bold uppercase tracking-widest rounded-full transition-all border ${isDark
                                                            ? 'bg-white/[0.04] border-white/[0.08] hover:bg-white/[0.08] disabled:opacity-20 text-white/60'
                                                            : 'bg-zinc-50 border-zinc-200 hover:bg-zinc-100 disabled:opacity-20 text-zinc-600'
                                                            }`}
                                                    >
                                                        ← Prev
                                                    </button>

                                                    {/* Page Dots */}
                                                    <div className="flex items-center gap-2">
                                                        {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                                                            <button
                                                                key={page}
                                                                onClick={() => setCurrentPage(page)}
                                                                className={`w-8 h-8 rounded-full text-xs font-bold transition-all duration-300 ${page === currentPage
                                                                    ? isDark
                                                                        ? 'bg-white text-black shadow-lg shadow-white/10'
                                                                        : 'bg-zinc-900 text-white shadow-lg shadow-zinc-900/20'
                                                                    : isDark
                                                                        ? 'text-white/30 hover:text-white/60 hover:bg-white/[0.05]'
                                                                        : 'text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100'
                                                                    }`}
                                                            >
                                                                {page}
                                                            </button>
                                                        ))}
                                                    </div>

                                                    <button
                                                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                                        disabled={currentPage === totalPages}
                                                        className={`px-5 py-2.5 text-xs font-bold uppercase tracking-widest rounded-full transition-all border ${isDark
                                                            ? 'bg-white/[0.04] border-white/[0.08] hover:bg-white/[0.08] disabled:opacity-20 text-white/60'
                                                            : 'bg-zinc-50 border-zinc-200 hover:bg-zinc-100 disabled:opacity-20 text-zinc-600'
                                                            }`}
                                                    >
                                                        Next →
                                                    </button>
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            </BentoCard>
                        </motion.div>
                    )}

                    {/* ── Plugins Tab — Full Architecture View ──────────────────── */}
                    {activeTab === 'plugins' && (
                        <motion.div
                            key="plugins"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.4 }}
                            className="space-y-8"
                        >
                            {/* Plugins Header Section */}
                            <div className="relative overflow-hidden">
                                {/* Ambient Glow */}
                                {isDark && (
                                    <div className="absolute top-0 right-0 w-[500px] h-[300px] bg-emerald-500/5 rounded-[100%] blur-[120px] pointer-events-none" />
                                )}

                                <BentoCard size="lg" glow className="relative">
                                    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                                        <div className="flex items-start gap-4">
                                            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center border shrink-0 ${isDark
                                                ? 'bg-gradient-to-br from-emerald-500/20 to-teal-500/10 border-emerald-500/20 shadow-[0_0_25px_rgba(16,185,129,0.15)]'
                                                : 'bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200 shadow-lg shadow-emerald-100/50'
                                                }`}>
                                                <Puzzle className={`w-7 h-7 ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`} />
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-3 mb-1">
                                                    <h2 className={`text-2xl font-semibold tracking-tight ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                                                        Plugin Architecture
                                                    </h2>
                                                    <span className={`text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border ${isDark
                                                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                                        : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                                        }`}>
                                                        SDK v2
                                                    </span>
                                                </div>
                                                <p className={`text-sm max-w-lg leading-relaxed ${isDark ? 'text-white/40' : 'text-zinc-500'}`}>
                                                    Create, manage, and deploy voice-powered data collection plugins. Each plugin connects to your database for real-time form submissions.
                                                </p>
                                            </div>
                                        </div>

                                        {/* Quick Stats */}
                                        <div className={`flex items-center gap-1 p-1.5 rounded-2xl border shrink-0 ${isDark
                                            ? 'bg-white/[0.02] border-white/[0.05]'
                                            : 'bg-zinc-50 border-zinc-200'
                                            }`}>
                                            {[
                                                { label: 'Endpoints', icon: Zap },
                                                { label: 'Real-time', icon: Activity },
                                                { label: 'Secure', icon: Trophy },
                                            ].map((feat, i) => (
                                                <div
                                                    key={feat.label}
                                                    className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-[10px] font-bold uppercase tracking-widest ${isDark
                                                        ? 'text-white/40'
                                                        : 'text-zinc-500'
                                                        }`}
                                                >
                                                    <feat.icon className={`w-3.5 h-3.5 ${isDark ? 'text-emerald-500/60' : 'text-emerald-500'}`} />
                                                    {feat.label}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </BentoCard>
                            </div>

                            {/* Plugin Dashboard Content */}
                            <PluginDashboard />
                        </motion.div>
                    )}

                    {/* ── Profile Tab ───────────────────────────────────────────── */}
                    {activeTab === 'profile' && (
                        <motion.div
                            key="profile"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.3 }}
                        >
                            <ProfileSettings />
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}
