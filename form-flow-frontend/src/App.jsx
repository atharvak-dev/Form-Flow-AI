import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navigation } from '@/components/layout';
import { Aurora } from '@/components/ui';
import { ErrorBoundary } from '@/components/common';
import { ROUTES, AURORA_COLORS } from '@/constants';

// Page components
import HomePage from '@/pages/HomePage';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import DashboardPage from '@/pages/DashboardPage';

import { useTheme } from '@/context/ThemeProvider';

function App() {
  const { isDark } = useTheme();

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <div className={`relative min-h-screen font-sans transition-colors duration-500
          ${isDark ? 'bg-[#09090b] selection:bg-green-900/30' : 'bg-white selection:bg-green-100'}`}>

          {/* Global WEBGL Background */}
          <div className="fixed inset-0 z-0 pointer-events-none">
            <Aurora
              colorStops={isDark ? ['#064e3b', '#065f46', '#059669'] : AURORA_COLORS}
              amplitude={isDark ? 0.8 : 1.0}
              blend={isDark ? 0.6 : 0.5}
              speed={0.4}
            />
          </div>

          {/* Content Layer */}
          <div className="relative z-10 w-full min-h-screen">

            {/* Logo Brand */}
            {/* Logo Brand */}
            <a href={ROUTES.HOME} className="fixed top-6 left-8 z-[100] flex items-center gap-3 bg-white/40 dark:bg-gray-800/40 backdrop-blur-xl pr-6 pl-2 py-2 rounded-full border border-white/20 dark:border-gray-700/30 shadow-lg shadow-black/5 hover:bg-white/60 dark:hover:bg-gray-700/60 transition-all group">
              <div className="w-10 h-10 rounded-full bg-white dark:bg-gray-900 flex items-center justify-center overflow-hidden shadow-sm border border-black/5 dark:border-white/10 p-1">
                <img src="/logo.png" alt="Form Flow AI" className="w-full h-full object-contain" />
              </div>
              <span className="font-semibold text-lg tracking-tight text-gray-800 dark:text-gray-100 group-hover:text-black dark:group-hover:text-white transition-colors hidden sm:block">
                Form Flow AI
              </span>
            </a>

            <Navigation />

            <Routes>
              <Route path={ROUTES.HOME} element={<HomePage />} />
              <Route path={ROUTES.REGISTER} element={<RegisterPage />} />
              <Route path={ROUTES.LOGIN} element={<LoginPage />} />
              <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />
            </Routes>
          </div>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
