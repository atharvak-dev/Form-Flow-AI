import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import Aurora from '@/components/ui/Aurora';
import { Terminal, Cpu, Wifi, Activity } from 'lucide-react';

const AURORA_COLORS = ['#bfe4be', '#69da93', '#86efac'];

import { useTheme } from '@/context/ThemeProvider';

const TerminalLoader = ({ url }) => {
    const { isDark } = useTheme();
    const [progress, setProgress] = useState(0);
    const [timeLeft, setTimeLeft] = useState(25);
    const [logs, setLogs] = useState([]);
    const logsEndRef = useRef(null);
    const processedMilestones = useRef(new Set());

    // Safely extract hostname or use fallback
    const getDisplayHost = () => {
        try {
            return new URL(url).hostname;
        } catch {
            return url || 'document';
        }
    };

    // Dynamic Theme Styles
    const containerClasses = isDark
        ? "bg-black/40 border-white/20 shadow-2xl"
        : "bg-white/80 border-zinc-200 shadow-xl shadow-zinc-200/50";

    const headerClasses = isDark ? "bg-white/5 border-white/10" : "bg-zinc-100/50 border-zinc-200";
    const headerTextClasses = isDark ? "text-white/40" : "text-zinc-400";

    const titleClasses = isDark ? "text-white" : "text-zinc-800";
    const subTitleClasses = isDark ? "text-white/50" : "text-zinc-500";
    const completeTextClasses = isDark ? "text-white/30" : "text-zinc-400";

    const terminalBgClasses = isDark
        ? "bg-black/60 border-white/10 text-green-400/90"
        : "bg-zinc-900 border-zinc-200 text-green-400"; // Keep terminal dark even in light mode for contrast, or make it light? 
    // Terminals are usually dark. Let's keep the terminal window itself dark for "hacker" feel, but the surrounding container light.

    const progressBarBg = isDark ? "bg-white/10" : "bg-zinc-200";

    // ... (rest of logic) ...
    useEffect(() => {
        const totalDuration = 25000;
        const updateInterval = 100;
        const steps = totalDuration / updateInterval;
        let currentStep = 0;

        const timer = setInterval(() => {
            currentStep++;
            const newProgress = Math.min(Math.round((currentStep / steps) * 100), 99);
            setProgress(newProgress);
            if (currentStep % 10 === 0) setTimeLeft(prev => Math.max(prev - 1, 1));

            const tryAddLog = (milestone, message) => {
                if (newProgress >= milestone && !processedMilestones.current.has(milestone)) {
                    addLog(message);
                    processedMilestones.current.add(milestone);
                }
            };

            tryAddLog(2, 'Initialize engine v2.0.4');
            tryAddLog(8, `Target confirmed: ${getDisplayHost()}`);
            tryAddLog(15, 'Handshaking secured connection...');
            tryAddLog(25, 'Parsing DOM structure tree...');
            tryAddLog(38, 'Identifying interactive fields...');
            tryAddLog(50, 'Optimizing context window...');
            tryAddLog(65, 'Generating smart prompts...');
            tryAddLog(80, 'Synthesizing voice layout...');
            tryAddLog(92, 'Finalizing setup sequence...');

        }, updateInterval);

        return () => clearInterval(timer);
    }, [url]);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const addLog = (message) => {
        setLogs(prev => [...prev, { text: message, timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }) }]);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-hidden font-sans">
            <div className={`max-w-3xl w-full backdrop-blur-2xl rounded-2xl relative z-50 overflow-hidden flex flex-col h-[70vh] max-h-[700px] border ${containerClasses}`}>

                {/* Window Header */}
                <div className={`p-4 flex items-center justify-between border-b shrink-0 ${headerClasses}`}>
                    <div className="flex gap-2">
                        <div className="w-3 h-3 rounded-full bg-red-400/80"></div>
                        <div className="w-3 h-3 rounded-full bg-yellow-400/80"></div>
                        <div className="w-3 h-3 rounded-full bg-green-400/80"></div>
                    </div>
                    <div className={`text-xs font-semibold flex items-center gap-2 font-mono uppercase tracking-widest ${headerTextClasses}`}>
                        <Terminal size={12} />
                        analysis_engine.exe
                    </div>
                    <div className="w-14"></div>
                </div>

                {/* Dashboard Header */}
                <div className="px-8 pt-8 pb-6 shrink-0">
                    <div className="flex justify-between items-start">
                        <div>
                            <h2 className={`text-2xl font-bold tracking-tight flex items-center gap-2 drop-shadow-sm ${titleClasses}`}>
                                <Activity className="text-green-400 animate-pulse" />
                                Analyzing Form
                            </h2>
                            <p className={`text-sm mt-1 ${subTitleClasses}`}>
                                Establishing semantic understanding of target URL
                            </p>
                        </div>
                        <div className="text-right">
                            <div className="text-3xl font-bold font-mono text-green-400 tabular-nums">
                                {progress}<span className="text-base align-top opacity-50 text-green-400/50">%</span>
                            </div>
                            <div className={`text-xs uppercase tracking-widest font-semibold mt-1 ${completeTextClasses}`}>
                                Complete
                            </div>
                        </div>
                    </div>
                </div>

                {/* Progress Bar Container */}
                <div className="px-8 pb-8 shrink-0">
                    <div className={`relative h-1 rounded-full overflow-hidden ${progressBarBg}`}>
                        <motion.div
                            className="absolute top-0 left-0 h-full bg-green-400 shadow-[0_0_10px_rgba(74,222,128,0.5)]"
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                            transition={{ duration: 0.1, ease: 'linear' }}
                        />
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent w-full -translate-x-full animate-[shimmer_2s_infinite]"></div>
                    </div>
                </div>

                {/* Terminal Window Area */}
                <div className={`flex-1 mx-8 mb-8 rounded-xl p-4 font-mono text-sm border shadow-inner overflow-hidden flex flex-col relative ${terminalBgClasses}`}>
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:20px_20px] pointer-events-none"></div>

                    <div className="flex justify-between items-center text-xs text-white/30 mb-2 border-b border-white/10 pb-2 shrink-0">
                        <span className="flex items-center gap-1"><Cpu size={10} /> CORE_PROCESS</span>
                        <span className="flex items-center gap-1"><Wifi size={10} /> {timeLeft}s REMAINING</span>
                    </div>

                    <style>{`
                        .no-scrollbar::-webkit-scrollbar { display: none; }
                        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
                    `}</style>
                    <div className="flex-1 overflow-y-auto overflow-x-hidden no-scrollbar relative z-0 flex flex-col justify-start w-full">
                        {logs.map((log, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="flex gap-3 py-1 w-full"
                            >
                                <span className="text-white/30 select-none shrink-0">[{log.timestamp}]</span>
                                <span className="text-green-500 font-bold shrink-0">➜</span>
                                <span className="text-green-200/80 font-mono break-all whitespace-pre-wrap flex-1 min-w-0">{log.text}</span>
                            </motion.div>
                        ))}
                        <div ref={logsEndRef} />
                    </div>

                    <div className="mt-2 flex items-center gap-2 text-green-500 border-t border-white/10 pt-2 shrink-0">
                        <span className="animate-pulse">_</span>
                        <span className="text-xs text-white/30">{getDisplayHost()}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TerminalLoader;
