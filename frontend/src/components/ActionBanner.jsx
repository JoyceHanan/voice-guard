import React from 'react';
import { ShieldCheck, Eye, ShieldAlert, AlertOctagon, ArrowRight } from 'lucide-react';

export default function ActionBanner({ recommendedAction, riskTier, onOpenChallenge }) {
  const normAction = (recommendedAction?.action || 'ALLOW').toUpperCase();
  const message = recommendedAction?.message || 'No action needed. Call may proceed normally.';
  const tier = (riskTier || 'LOW').toUpperCase();

  const isCritical = tier === 'CRITICAL' || normAction === 'ESCALATE';

  // Action style mapping (OpenCode AI TUI Protocol Bar Pattern)
  const ACTION_STYLES = {
    ALLOW: {
      bg: 'bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] border-l-4 border-l-[#30d158] text-[#201d1d]',
      badge: 'bg-[#30d158]/10 text-[#30d158] border border-[#30d158]/30',
      icon: ShieldCheck,
      iconColor: 'text-[#30d158]',
    },
    MONITOR: {
      bg: 'bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] border-l-4 border-l-[#ff9f0a] text-[#201d1d]',
      badge: 'bg-[#ff9f0a]/10 text-[#ff9f0a] border border-[#ff9f0a]/30',
      icon: Eye,
      iconColor: 'text-[#ff9f0a]',
    },
    VERIFY: {
      bg: 'bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] border-l-4 border-l-[#ff9f0a] text-[#201d1d]',
      badge: 'bg-[#ff9f0a]/10 text-[#ff9f0a] border border-[#ff9f0a]/30 animate-pulse',
      icon: ShieldAlert,
      iconColor: 'text-[#ff9f0a]',
    },
    ESCALATE: {
      bg: 'bg-[#201d1d] border border-[#201d1d] text-[#fdfcfc]',
      badge: 'bg-[#ff3b30] text-[#fdfcfc] border border-[#ff3b30] animate-pulse',
      icon: AlertOctagon,
      iconColor: 'text-[#ff3b30]',
    },
  };

  const currentStyle = ACTION_STYLES[normAction] || ACTION_STYLES.ALLOW;
  const ActionIcon = currentStyle.icon;

  const showChallengeButton = tier === 'HIGH' || tier === 'CRITICAL' || normAction === 'VERIFY' || normAction === 'ESCALATE';

  return (
    <div
      className={`rounded-none p-5 md:p-6 transition-all duration-200 font-mono flex flex-wrap items-center justify-between gap-4 ${
        isCritical
          ? 'bg-[#201d1d] border border-[#201d1d] text-[#fdfcfc]'
          : currentStyle.bg
      }`}
    >
      <div className="flex items-center gap-4 max-w-3xl">
        <div className={`p-3 rounded-[4px] shrink-0 ${
          isCritical
            ? 'bg-[#302c2c] border border-[#646262] text-[#ff3b30]'
            : 'bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)]'
        }`}>
          <ActionIcon className={`w-6 h-6 ${isCritical ? 'text-[#ff3b30]' : currentStyle.iconColor}`} />
        </div>

        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[11px] font-bold uppercase tracking-wider ${isCritical ? 'text-[#9a9898]' : 'text-[#646262]'}`}>
              RECOMMENDED PROTOCOL ACTION
            </span>
            <span className={`px-2 py-0.5 rounded-[4px] text-[10px] uppercase font-mono font-bold ${
              isCritical ? 'bg-[#ff3b30] text-[#fdfcfc]' : currentStyle.badge
            }`}>
              ACTION: {normAction}
            </span>
          </div>
          <p className={`text-sm font-semibold leading-relaxed font-mono ${isCritical ? 'text-[#fdfcfc]' : 'text-[#201d1d]'}`}>
            {message}
          </p>
        </div>
      </div>

      {/* Verification Challenge Trigger Button */}
      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={onOpenChallenge}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-[4px] text-xs font-mono font-bold transition-all ${
            isCritical
              ? 'bg-[#ff3b30] hover:bg-[#d70015] text-[#fdfcfc]'
              : showChallengeButton
              ? 'bg-[#201d1d] hover:bg-[#0f0000] text-[#fdfcfc]'
              : 'bg-[#f8f7f7] hover:bg-[#f1eeee] text-[#201d1d] border border-[rgba(15,0,0,0.12)]'
          }`}
        >
          <ShieldAlert className={`w-4 h-4 ${isCritical ? 'text-[#fdfcfc]' : 'text-[#30d158]'}`} />
          <span>ISSUE VERIFICATION CHALLENGE</span>
          <ArrowRight className="w-3.5 h-3.5 opacity-70" />
        </button>
      </div>
    </div>
  );
}
