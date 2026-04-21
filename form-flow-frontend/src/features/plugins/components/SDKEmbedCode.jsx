/**
 * SDK Embed Code Component
 * Premium SaaS redesign matching modern, dark dashboard aesthetics (Vercel/Linear style)
 */
import { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Copy, Check, ExternalLink, Terminal, AlertCircle, Info, Blocks } from 'lucide-react';
import { useTheme } from '@/context/ThemeProvider';
import toast from 'react-hot-toast';

// Simple syntax highlighting for code blocks
const highlightCode = (code, language) => {
    return code
        .replace(/(const|let|var|function|import|export|from|return|async|await)/g, '<span class="text-purple-400 font-medium">$1</span>')
        .replace(/('.*?'|".*?"|`.*?`)/g, '<span class="text-emerald-400">$1</span>')
        .replace(/(\{|\}|\(|\)|\[|\])/g, '<span class="text-zinc-500">$1</span>')
        .replace(/(\/\/.*$)/gm, '<span class="text-zinc-500 italic">$1</span>');
};

export function SDKEmbedCode({ plugin, apiKey }) {
    const { isDark } = useTheme();
    const [activeTab, setActiveTab] = useState('react');
    const [copied, setCopied] = useState(false);

    // Generate code examples
    const codeExamples = useMemo(() => ({
        html: `<!-- Add FormFlow Voice Widget -->
<script src="https://cdn.formflow.ai/v1/sdk.min.js"></script>
<div id="formflow-widget"></div>

<script>
  FormFlow.init({
    apiKey: '${apiKey || 'YOUR_API_KEY'}',
    pluginId: '${plugin.id}',
    apiBase: 'http://localhost:8001', // Local backend URL
    theme: 'auto',
    onComplete: (data) => console.log('Data collected:', data),
    onError: (error) => console.error('Error:', error)
  });
</script>`,
        react: `import { FormFlowWidget, useFormFlowPlugin } from '@formflow/react';

function MyForm() {
  const { startSession } = useFormFlowPlugin({
    apiKey: '${apiKey || 'YOUR_API_KEY'}',
    pluginId: '${plugin.id}',
    apiBase: 'http://localhost:8001',
    onComplete: (data) => console.log('Data collected:', data),
  });

  return (
    <FormFlowWidget
      theme="auto"
      position="bottom-right"
      welcomeMessage="Hi! Let me help you fill this form."
    />
  );
}

export default MyForm;`,
        vanilla: `// Vanilla JavaScript integration
const formflow = new FormFlow({
  apiKey: '${apiKey || 'YOUR_API_KEY'}',
  pluginId: '${plugin.id}',
  apiBase: 'http://localhost:8001',
  container: document.getElementById('formflow-widget'),
});

// Start a voice session
formflow.start();

// Listen for events
formflow.on('complete', (data) => {
  console.log('Data collected:', data);
});`,
        curl: `# Test your plugin API
curl -X POST http://localhost:8001/plugins/sessions \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: ${apiKey || 'YOUR_API_KEY'}" \\
  -H "X-Plugin-ID: ${plugin.id}" \\
  -d '{"source_url": "http://localhost"}'`
    }), [plugin.id, apiKey]);

    // Copy to clipboard
    const handleCopy = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(codeExamples[activeTab]);
            setCopied(true);
            toast.success('Copied to clipboard!', { style: { background: '#333', color: '#fff', fontSize: '13px' } });
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            toast.error('Failed to copy');
        }
    }, [codeExamples, activeTab]);

    const tabs = [
        { id: 'react', label: 'React' },
        { id: 'html', label: 'HTML' },
        { id: 'vanilla', label: 'Vanilla JS' },
        { id: 'curl', label: 'cURL' },
    ];

    return (
        <div className="max-w-5xl mx-auto space-y-6 w-full">
            
            {/* Header Block */}
            <div className="mb-8">
                <h2 className={`text-2xl font-semibold tracking-tight ${isDark ? 'text-zinc-100' : 'text-zinc-900'}`}>
                    Embed Code
                </h2>
                <p className={`mt-1.5 text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>
                    Easily integrate FormFlow into your application using our drop-in snippets.
                </p>
            </div>

            {/* Main Content Area */}
            <div className={`rounded-2xl border overflow-hidden transition-all ${isDark ? 'bg-zinc-900/40 border-white/[0.06]' : 'bg-white border-zinc-200 shadow-sm'}`}>
                
                {/* Integration Header inside the card */}
                <div className={`px-6 py-5 border-b flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${isDark ? 'border-white/[0.04]' : 'border-zinc-100'}`}>
                    <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${isDark ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-emerald-50 border-emerald-100 text-emerald-600'}`}>
                            <Blocks className="w-5 h-5" />
                        </div>
                        <div>
                            <h3 className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-zinc-900'}`}>
                                SDK Integration
                            </h3>
                            <p className={`text-[13px] mt-0.5 ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>
                                Select your framework to get the ready-to-use snippet.
                            </p>
                        </div>
                    </div>
                    <a
                        href="https://docs.formflow.ai/sdk"
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors border ${
                            isDark 
                                ? 'bg-white/[0.03] border-white/[0.05] text-zinc-300 hover:text-white hover:bg-white/[0.06]' 
                                : 'bg-zinc-50 border-zinc-200 text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100'
                        }`}
                    >
                        View Documentation <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                </div>

                <div className="p-6 space-y-6">
                    {/* Modern Tabs */}
                    <div className={`flex items-center gap-2 border-b ${isDark ? 'border-white/[0.06]' : 'border-zinc-200'}`}>
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`relative px-4 py-3 text-[13px] font-medium transition-colors ${
                                    activeTab === tab.id
                                        ? (isDark ? 'text-white' : 'text-zinc-900')
                                        : (isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-zinc-500 hover:text-zinc-700')
                                }`}
                            >
                                {tab.label}
                                {activeTab === tab.id && (
                                    <motion.div
                                        layoutId="activeTabIndicator"
                                        className="absolute bottom-0 left-0 right-0 h-[2px] bg-emerald-500"
                                        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                                    />
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Code Block Container */}
                    <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-white/[0.08] bg-black/40' : 'border-zinc-200/80 bg-zinc-900'}`}>
                        {/* Code Header */}
                        <div className={`flex items-center justify-between px-4 py-3 border-b ${isDark ? 'border-white/[0.05] bg-white/[0.02]' : 'border-zinc-800 bg-zinc-900/50'}`}>
                            <div className="flex items-center gap-2">
                                <Terminal className={`w-4 h-4 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`} />
                                <span className={`text-[13px] font-mono ${isDark ? 'text-zinc-400' : 'text-zinc-300'}`}>
                                    {activeTab === 'html' ? 'index.html' : activeTab === 'react' ? 'App.tsx' : activeTab === 'curl' ? 'terminal' : 'app.js'}
                                </span>
                            </div>
                            <button
                                onClick={handleCopy}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                                    copied 
                                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                                        : (isDark ? 'text-zinc-400 border border-transparent hover:text-zinc-200 hover:bg-white/[0.05]' : 'text-zinc-400 border border-transparent hover:text-white hover:bg-white/10')
                                }`}
                            >
                                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                                {copied ? 'Copied' : 'Copy Code'}
                            </button>
                        </div>
                        
                        {/* Source Code */}
                        <div className="p-5 overflow-x-auto text-[13px] leading-relaxed custom-scrollbar">
                            <pre>
                                <code
                                    className={`font-mono block min-w-full ${isDark ? 'text-zinc-300' : 'text-zinc-300'}`}
                                    dangerouslySetInnerHTML={{
                                        __html: highlightCode(codeExamples[activeTab], activeTab)
                                    }}
                                />
                            </pre>
                        </div>
                    </div>

                    {/* API Key Missing System Message - Minimal Alert */}
                    <AnimatePresence>
                        {!apiKey && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                                className={`flex items-start gap-3 p-4 rounded-lg border-l-2 ${
                                    isDark 
                                        ? 'bg-amber-500/5 border-l-amber-500/50 border-amber-500/10 text-amber-200/90' 
                                        : 'bg-amber-50/50 border-l-amber-400 border-amber-200/50 text-amber-800'
                                }`}
                            >
                                <AlertCircle className={`w-5 h-5 shrink-0 mt-0.5 ${isDark ? 'text-amber-500/80' : 'text-amber-500'}`} />
                                <div className="text-[13px] leading-relaxed">
                                    <span className="font-semibold block mb-0.5">Missing API Key</span>
                                    <span className="opacity-80">Generate an API Key in your dashboard settings to test this live code.</span>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            {/* Quick Tips Section */}
            <div className={`p-6 rounded-2xl border ${isDark ? 'bg-white/[0.02] border-white/[0.04]' : 'bg-zinc-50 border-zinc-200/60'}`}>
                <div className="flex items-center gap-2.5 mb-4">
                    <Info className={`w-4 h-4 ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`} />
                    <h5 className={`text-[13px] font-semibold tracking-wide uppercase ${isDark ? 'text-zinc-400' : 'text-zinc-700'}`}>
                        Implementation Tips
                    </h5>
                </div>
                <div className="grid sm:grid-cols-2 gap-x-8 gap-y-3">
                    {[
                        "Load the SDK before closing body tag for optimal performance",
                        "The widget is fully responsive and auto-detects mobile devices",
                        "Use theme: 'auto' to inherently match the user's system OS preference",
                        "All data ingestion is end-to-end encrypted automatically"
                    ].map((tip, i) => (
                        <div key={i} className={`text-[13px] leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
                            <span className={`mr-2 font-black ${isDark ? 'text-zinc-700' : 'text-zinc-300'}`}>•</span>
                            {tip}
                        </div>
                    ))}
                </div>
            </div>
            
        </div>
    );
}

export default SDKEmbedCode;
