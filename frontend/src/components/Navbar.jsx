import React from 'react';
import { Shield, Radio, UserCheck, RefreshCw, KeyRound } from 'lucide-react';
import { API_KEY } from '../config';

export default function Navbar({ activeTab, setActiveTab, backendStatus, onRefreshStatus }) {
  return (
    <header className="sticky top-0 z-30 bg-[#fdfcfc] border-b border-[rgba(15,0,0,0.12)] px-4 lg:px-8 py-3 font-mono text-caption-md">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Logo & Brand */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-[4px] bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] flex items-center justify-center text-[#201d1d]">
            <Shield className="w-4 h-4 text-[#201d1d]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-body-strong tracking-wider text-[#201d1d]">Voiceguard</span>
              <span className="text-[11px] font-mono text-[#646262] bg-[#f1eeee] border border-[rgba(15,0,0,0.12)] px-1.5 py-0.5 rounded-[4px]">
                v1.6
              </span>
            </div>
            <p className="text-caption-md text-[#646262] font-normal">Real-Time Call Fraud Protection Platform</p>
          </div>
        </div>

        {/* Navigation Tabs (OpenCode AI Button Tabs) */}
        <div className="flex items-center bg-[#f8f7f7] p-1 rounded-[4px] border border-[rgba(15,0,0,0.12)]">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-[4px] text-caption-md font-mono transition-colors ${activeTab === 'dashboard'
              ? 'bg-[#201d1d] text-[#fdfcfc] font-medium'
              : 'text-[#646262] hover:text-[#201d1d] hover:bg-[#f1eeee]'
              }`}
          >
            <Radio className="w-3.5 h-3.5 text-[#007aff]" />
            <span>LIVE DASHBOARD</span>
          </button>
          <button
            onClick={() => setActiveTab('enrollment')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-[4px] text-caption-md font-mono transition-colors ${activeTab === 'enrollment'
              ? 'bg-[#201d1d] text-[#fdfcfc] font-medium'
              : 'text-[#646262] hover:text-[#201d1d] hover:bg-[#f1eeee]'
              }`}
          >
            <UserCheck className="w-3.5 h-3.5 text-[#30d158]" />
            <span>VOICE DIRECTORY</span>
          </button>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 text-caption-md text-[#646262] bg-[#f8f7f7] px-3 py-1.5 rounded-[4px] border border-[rgba(15,0,0,0.12)]">
            <KeyRound className="w-3.5 h-3.5 text-[#6e6e73]" />
            <span className="font-mono text-caption-md text-[#201d1d]">KEY: {API_KEY ? `${API_KEY.slice(0, 8)}...` : 'vg_secret...'}</span>
          </div>

          <button
            onClick={onRefreshStatus}
            className="flex items-center gap-2 text-caption-md px-3 py-1.5 rounded-[4px] bg-[#f8f7f7] hover:bg-[#f1eeee] border border-[rgba(15,0,0,0.12)] text-[#201d1d] transition-colors"
            title="Refresh backend status"
          >
            <span className={`w-2 h-2 rounded-full ${backendStatus === 'online' ? 'bg-[#30d158]' : 'bg-[#ff3b30]'}`} />
            <span className="uppercase text-caption-md font-semibold">{`● ${backendStatus || 'ONLINE'}`}</span>
            <RefreshCw className="w-3 h-3 text-[#646262]" />
          </button>
        </div>
      </div>
    </header>
  );
}
