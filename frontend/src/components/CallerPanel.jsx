import React from 'react';
import { Phone, UserCheck, AlertTriangle, HelpCircle, ShieldAlert } from 'lucide-react';

export default function CallerPanel({ callerNumber, claimedIdentity, callerClassification }) {
  // Classification badge rendering logic
  const renderBadge = () => {
    if (!callerClassification) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] text-[11px] font-mono uppercase text-[#646262]">
          <HelpCircle className="w-3.5 h-3.5 text-[#646262]" />
          <span>[AWAITING ANALYSIS]</span>
        </span>
      );
    }

    const type = callerClassification.category || callerClassification.type || '';
    const name = callerClassification.name || callerClassification.details?.name || callerClassification.details || '';

    if (type === 'known' || type === 'KNOWN_CONTACT' || type === 'KNOWN CONTACT') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] bg-[#30d158]/10 border border-[#30d158]/30 text-[11px] font-mono text-[#30d158]">
          <UserCheck className="w-3.5 h-3.5 text-[#30d158]" />
          <span>[+ KNOWN CONTACT: <strong className="text-[#201d1d] uppercase font-bold">{name || 'Enrolled Contact'}</strong>]</span>
        </span>
      );
    }

    if (type === 'flagged' || type === 'FLAGGED' || type === 'FLAGGED_NUMBER' || type === 'BLOCKLISTED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] bg-[#ff3b30]/10 border border-[#ff3b30]/30 text-[11px] font-mono text-[#ff3b30] animate-pulse">
          <ShieldAlert className="w-3.5 h-3.5 text-[#ff3b30]" />
          <span>[x ⚠ FLAGGED NUMBER: <strong className="text-[#201d1d] uppercase font-bold">{name || 'Blocklisted'}</strong>]</span>
        </span>
      );
    }

    // Default Unknown Number
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] bg-[#ff9f0a]/10 border border-[#ff9f0a]/30 text-[11px] font-mono text-[#ff9f0a]">
        <AlertTriangle className="w-3.5 h-3.5 text-[#ff9f0a]" />
        <span>[- UNKNOWN NUMBER: {callerNumber || 'Unverified'}]</span>
      </span>
    );
  };

  return (
    <div className="bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] rounded-none p-4 md:p-5 font-mono">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-[4px] bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] flex items-center justify-center text-[#201d1d]">
            <Phone className="w-4 h-4 text-[#201d1d]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-[#646262] uppercase tracking-wider font-bold">[CALLER IDENTIFIER]</span>
              <span className="font-mono text-sm font-bold text-[#201d1d]">
                {callerNumber || '+1 (555) 019-2834'}
              </span>
            </div>
            <p className="text-xs text-[#646262] mt-0.5">
              Claimed Identity: <span className="text-[#201d1d] font-medium">{claimedIdentity || 'Not specified'}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {renderBadge()}
        </div>
      </div>
    </div>
  );
}
