import { useState, useEffect } from 'react';
import { getCaptchaHealth } from '@/services/api';
import { Shield, ShieldOff } from 'lucide-react';

/**
 * CAPTCHA Status Badge - Shows if auto-solve is configured
 */
export default function CaptchaStatusBadge() {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkStatus = async () => {
            try {
                const health = await getCaptchaHealth();
                setStatus(health);
            } catch (error) {
                setStatus({ auto_solve: false, mode: 'unknown' });
            } finally {
                setLoading(false);
            }
        };
        checkStatus();
    }, []);

    if (loading) return null;

    const isAuto = status?.auto_solve;

    return (
        <div
            className={`
                inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
                transition-all duration-200 cursor-default
                ${isAuto
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                    : 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
                }
            `}
            title={isAuto
                ? `CAPTCHA auto-solve via ${status.provider || '2captcha'}`
                : 'CAPTCHAs require manual solving'
            }
        >
            {isAuto ? (
                <>
                    <Shield size={12} />
                    <span>Auto-solve</span>
                </>
            ) : (
                <>
                    <ShieldOff size={12} />
                    <span>Manual</span>
                </>
            )}
        </div>
    );
}
