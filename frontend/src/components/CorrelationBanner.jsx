import React, { useState, useEffect } from 'react';
import { AlertTriangle, RefreshCw, X } from 'lucide-react';
import { API_BASE_URL, getAuthHeaders } from '../config';

export default function CorrelationBanner() {
  const [correlationData, setCorrelationData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const fetchCorrelation = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/correlation/check`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setCorrelationData(data);
        if (data.alert) {
          setDismissed(false);
        }
      }
    } catch (err) {
      console.error('Correlation check error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCorrelation();
    const interval = setInterval(fetchCorrelation, 30000); // 30s polling
    return () => clearInterval(interval);
  }, []);

  if (!correlationData || !correlationData.alert || dismissed) {
    return null;
  }

  return (
    <div className="bg-[#f8f7f7] border-b border-[rgba(15,0,0,0.12)] px-4 py-2.5 text-[#ff9f0a] font-mono text-caption-md transition-colors">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-1 rounded-[4px] bg-[#ff9f0a]/10 border border-[#ff9f0a]/30 text-[#ff9f0a]">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2 font-bold text-[#201d1d]">
              <span>[!] SECURITY ALERT: Multi-Signal Impersonation Cluster</span>
              <span className="px-2 py-0.5 rounded-[4px] bg-[#f1eeee] border border-[#ff9f0a]/40 text-caption-md text-[#ff9f0a]">
                [{correlationData.matched_calls || 0} CALLS LOGGED]
              </span>
            </div>
            <p className="text-[#646262] text-caption-md mt-0.5">
              {correlationData.message || 'Correlated risk signals observed across multiple caller sessions.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {correlationData.signals_matched && correlationData.signals_matched.length > 0 && (
            <div className="hidden md:flex items-center gap-1.5">
              {correlationData.signals_matched.map((sig, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded-[4px] bg-[#f1eeee] border border-[rgba(15,0,0,0.12)] text-caption-md text-[#302c2c]"
                >
                  [{sig}]
                </span>
              ))}
            </div>
          )}

          <button
            onClick={fetchCorrelation}
            disabled={loading}
            className="p-1 rounded-[4px] hover:bg-[#f1eeee] text-[#646262] hover:text-[#201d1d] transition-colors"
            title="Refresh correlation signals"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setDismissed(true)}
            className="p-1 rounded-[4px] hover:bg-[#f1eeee] text-[#646262] hover:text-[#201d1d] transition-colors"
            title="Dismiss notification"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
