import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import Aurora from '@/components/ui/Aurora';
import { Terminal, Cpu, Wifi, Activity } from 'lucide-react';

const AURORA_COLORS = ['#bfe4be', '#69da93', '#86efac'];

const TerminalLoader = ({ url }) => {
    const [progress, setProgress] = useState(0);
    const [timeLeft, setTimeLeft] = useState(25);
    const [logs, setLogs] = useState([]);

    // Simulated progress and logs
    useEffect(() => {
        const totalDuration = 25000; // 25 seconds simulated
        const updateInterval = 100;
        const steps = totalDuration / updateInterval;
        let currentStep = 0;

        const timer = setInterval(() => {
            currentStep++;
            const newProgress = Math.min(Math.round((currentStep / steps) * 100), 99);

            setProgress(newProgress);

            // Update time left roughly every second
            if (currentStep % 10 === 0) {
                setTimeLeft(prev => Math.max(prev - 1, 1));
            }

            // Simulated logs
            if (newProgress === 2) addLog('Initialize engine v2.0.4');
            if (newProgress === 8) addLog(`Target confirmed: ${new URL(url).hostname}`);
            if (newProgress === 15) addLog('Handshaking secured connection...');
            if (newProgress === 25) addLog('Parsing DOM structure tree...');
            if (newProgress === 38) addLog('Identifying interactive fields...');
            if (newProgress === 50) addLog('Optimizing context window...');
            if (newProgress === 65) addLog(' generating smart prompts...');
            if (newProgress === 80) addLog('Synthesizing voice layout...');
            if (newProgress === 92) addLog('Finalizing setup sequence...');

        }, updateInterval);

        return () => clearInterval(timer);
    }, [url]);

    const addLog = (message) => {
        setLogs(prev => [...prev, { text: message, timestamp: new Date().toLocaleTimeString('en-US', { hour12: false }) }]);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-hidden font-sans">
            {/* Background Layer (Aurora matches App.jsx) */}
            {/* We don't need another Aurora here if App.jsx has one globally, but for z-index safety we keep it or rely on parent. 
                Since this is a loader often used in isolation/overlay, keeping it is safer but ensure z-index.
            */}


            {/* Main Window Container - Dark Glass */}
            <div className="max-w-3xl w-full bg-black/40 backdrop-blur-2xl rounded-2xl shadow-2xl border border-white/20 relative z-50 overflow-hidden flex flex-col h-[70vh] max-h-[700px]">

                {/* Window Header */}
                <div className="bg-white/5 p-4 flex items-center justify-between border-b border-white/10 shrink-0">
                    <div className="flex gap-2">
                        <div className="w-3 h-3 rounded-full bg-red-400/80"></div>
                        <div className="w-3 h-3 rounded-full bg-yellow-400/80"></div>
                        <div className="w-3 h-3 rounded-full bg-green-400/80"></div>
                    </div>
                    <div className="text-xs font-semibold text-white/40 flex items-center gap-2 font-mono uppercase tracking-widest">
                        <Terminal size={12} />
                        analysis_engine.exe
                    </div>
                    <div className="w-14"></div> {/* Spacer */}
                </div>

                {/* Dashboard Header */}
                <div className="px-8 pt-8 pb-6 shrink-0 text-white">
                    <div className="flex justify-between items-start">
                        <div>
                            <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2 drop-shadow-lg">
                                <Activity className="text-green-400 animate-pulse" />
                                Analyzing Form
                            </h2>
                            <p className="text-white/50 text-sm mt-1">
                                Establishing semantic understanding of target URL
                            </p>
                        </div>
                        <div className="text-right">
                            <div className="text-3xl font-bold font-mono text-green-400 tabular-nums">
                                {progress}<span className="text-base align-top opactiy-50 text-green-400/50">%</span>
                            </div>
                            <div className="text-xs text-white/30 uppercase tracking-widest font-semibold mt-1">
                                Complete
                            </div>
                        </div>
                    </div>
                </div>

                {/* Progress Bar Container */}
                <div className="px-8 pb-8 shrink-0">
                    <div className="relative h-1 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                            className="absolute top-0 left-0 h-full bg-green-400 shadow-[0_0_10px_rgba(74,222,128,0.5)]"
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                            transition={{ duration: 0.1, ease: 'linear' }}
                        />
                        {/* Shimmer effect */}
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent w-full -translate-x-full animate-[shimmer_2s_infinite]"></div>
                    </div>
                </div>

                {/* Terminal Window Area */}
                <div className="flex-1 mx-8 mb-8 bg-black/60 rounded-xl p-4 font-mono text-sm border border-white/10 shadow-inner overflow-hidden flex flex-col relative text-green-400/90">
                    {/* Static Background Grid */}
                    <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:20px_20px] pointer-events-none"></div>

                    {/* Terminal Header */}
                    <div className="flex justify-between items-center text-xs text-white/30 mb-2 border-b border-white/10 pb-2 shrink-0">
                        <span className="flex items-center gap-1"><Cpu size={10} /> CORE_PROCESS</span>
                        <span className="flex items-center gap-1"><Wifi size={10} /> {timeLeft}s REMAINING</span>
                    </div>

                    {/* Scrolling Logs */}
                    <div className="flex-1 overflow-hidden flex flex-col-reverse relative z-0">
                        {logs.map((log, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="flex gap-3 py-1"
                            >
                                <span className="text-white/30 select-none">[{log.timestamp}]</span>
                                <span className="text-green-500 font-bold">➜</span>
                                <span className="text-green-200/80">{log.text}</span>
                            </motion.div>
                        ))}
                    </div>

                    <div className="mt-2 flex items-center gap-2 text-green-500 border-t border-white/10 pt-2 shrink-0">
                        <span className="animate-pulse">_</span>
                        <span className="text-xs text-white/30">{new URL(url).hostname}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TerminalLoader;
