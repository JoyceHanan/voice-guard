import React from 'react';
import { Activity, UserCheck, AlertTriangle, CheckCircle2, XCircle, Info } from 'lucide-react';

export default function EvidenceBreakdown({
  evidenceBreakdown = [],
  voiceResult,
  audioQuality,
  speakerSimilarity,
  riskReason,
  duration,
  threshold = 2.10,
}) {
  const getQualityBadge = () => {
    if (!audioQuality) return null;
    const label = audioQuality.label || 'GOOD';
    const snr = audioQuality.snr_db !== undefined ? audioQuality.snr_db.toFixed(1) : null;

    if (label === 'GOOD') {
      return (
        <span className="px-2 py-0.5 rounded-[4px] bg-[#30d158]/10 text-[#30d158] border border-[#30d158]/30 text-[10px] font-mono uppercase">
          [QUALITY: GOOD {snr && `(${snr} dB)`}]
        </span>
      );
    }
    if (label === 'MODERATE') {
      return (
        <span className="px-2 py-0.5 rounded-[4px] bg-[#ff9f0a]/10 text-[#ff9f0a] border border-[#ff9f0a]/30 text-[10px] font-mono uppercase" title="Dynamic margin widened (1.2)">
          [QUALITY: MODERATE {snr && `(${snr} dB)`} — WIDENED MARGIN]
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded-[4px] bg-[#ff3b30]/10 text-[#ff3b30] border border-[#ff3b30]/30 text-[10px] font-mono uppercase">
        [QUALITY: POOR {snr && `(${snr} dB)`} — DEGRADED]
      </span>
    );
  };

  const getVoiceResultBadge = () => {
    if (!voiceResult) return null;
    const res = voiceResult.toUpperCase();
    if (res === 'REAL') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] bg-[#30d158]/10 text-[#30d158] border border-[#30d158]/30 text-[10px] font-mono uppercase">
          <CheckCircle2 className="w-3 h-3 text-[#30d158]" />
          <span>[VOICE: REAL (BONAFIDE)]</span>
        </span>
      );
    }
    if (res === 'FAKE') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] bg-[#ff3b30]/10 text-[#ff3b30] border border-[#ff3b30]/30 text-[10px] font-mono uppercase animate-pulse">
          <XCircle className="w-3 h-3 text-[#ff3b30]" />
          <span>[VOICE: FAKE (SYNTHETIC)]</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[4px] bg-[#f8f7f7] text-[#646262] border border-[rgba(15,0,0,0.12)] text-[10px] font-mono uppercase">
        <AlertTriangle className="w-3 h-3 text-[#ff9f0a]" />
        <span>[VOICE: INCONCLUSIVE]</span>
      </span>
    );
  };

  return (
    <div className="bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] rounded-none p-5 md:p-6 font-mono flex flex-col justify-between w-full">
      <div>
        {/* TUI Card Header */}
        <div className="flex flex-wrap items-center justify-between border-b border-[rgba(15,0,0,0.12)] pb-3 mb-4 gap-2">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#30d158]" />
            <h3 className="text-sm font-bold text-[#201d1d] tracking-wider">[EVIDENCE & ANOMALY MATRIX]</h3>
          </div>
          {getQualityBadge()}
        </div>

        {/* Primary Signals Summary Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
          <div className="bg-[#f8f7f7] p-3 rounded-none border border-[rgba(15,0,0,0.12)]">
            <span className="text-[11px] text-[#646262] font-semibold block mb-1">AASIST-L Detector Result</span>
            <div className="mt-1 flex items-center justify-between">
              {getVoiceResultBadge() || <span className="text-xs text-[#646262]">[UNEVALUATED]</span>}
              {duration && <span className="text-[11px] text-[#646262] font-mono">{duration.toFixed(1)}s audio</span>}
            </div>
          </div>

          <div className="bg-[#f8f7f7] p-3 rounded-none border border-[rgba(15,0,0,0.12)]">
            <span className="text-[11px] text-[#646262] font-semibold block mb-1">ECAPA-TDNN Speaker Match</span>
            <div className="mt-1 flex items-center justify-between">
              {speakerSimilarity !== null && speakerSimilarity !== undefined ? (
                <span className={`text-xs font-mono font-bold ${speakerSimilarity >= 0.75 ? 'text-[#30d158]' : 'text-[#ff9f0a]'}`}>
                  SIMILARITY: {(speakerSimilarity * 100).toFixed(1)}%
                </span>
              ) : (
                <span className="text-xs text-[#646262]">[NO ENROLLMENT CLAIM]</span>
              )}
              <UserCheck className="w-4 h-4 text-[#646262]" />
            </div>
          </div>
        </div>

        {/* Contributing Risk Factors List with OpenCode List-Row Bracket Pattern */}
        <div className="space-y-2.5">
          <span className="text-[11px] font-bold text-[#646262] uppercase tracking-wider block mb-2">
            [MULTI-FACTOR RISK CONTRIBUTIONS]
          </span>

          {(() => {
            const items = Array.isArray(evidenceBreakdown)
              ? evidenceBreakdown
              : typeof evidenceBreakdown === 'object' && evidenceBreakdown !== null
              ? Object.entries(evidenceBreakdown).map(([key, val]) => {
                  let name = key.replace(/_/g, ' ').toUpperCase();
                  if (key === 'voice_spoof_risk') name = 'AASIST-L Voice Spoof Signal';
                  else if (key === 'speaker_mismatch_risk') name = 'Biometric Speaker Match';
                  else if (key === 'transaction_context_risk') name = 'Transaction & Call Context';

                  const weight = val.weighted_contribution !== undefined ? val.weighted_contribution : val.contribution || val.weight || 0;
                  let details = val.status || '';
                  if (key === 'voice_spoof_risk' && val.raw_score !== undefined) {
                    details = `Raw logit: ${val.raw_score} (Norm risk: ${val.normalized_risk_score}%)`;
                  } else if (key === 'transaction_context_risk' && val.caller_category) {
                    details = `Category: ${val.caller_category}, Beneficiary: ${val.new_beneficiary ? 'NEW' : 'VERIFIED'}, Urgency: ${val.urgency ? 'HIGH' : 'NORMAL'}`;
                  }

                  return { factor: name, contribution: weight, details: details };
                })
              : [];

            if (items.length === 0) {
              return (
                <div className="bg-[#f8f7f7] p-4 rounded-none border border-[rgba(15,0,0,0.12)] text-center text-xs text-[#646262] italic font-mono">
                  [NO BREAKDOWN ANALYSIS AVAILABLE — UPLOAD AUDIO OR START LIVE STREAM]
                </div>
              );
            }

            return items.map((item, idx) => {
              const factorName = item.factor || item.name || `Factor ${idx + 1}`;
              const weight = item.contribution !== undefined ? item.contribution : item.weight || item.score || 0;
              const details = item.details || item.description || '';

              // ASCII bar fill
              const totalBlocks = 16;
              const filled = Math.round((Math.min(100, Math.max(0, weight)) / 100) * totalBlocks);
              const asciiFill = '█'.repeat(filled) + '░'.repeat(totalBlocks - filled);

              let prefixMarker = '[+]';
              let textColor = 'text-[#30d158]';
              if (weight > 30) {
                prefixMarker = '[x]';
                textColor = 'text-[#ff3b30]';
              } else if (weight > 15) {
                prefixMarker = '[-]';
                textColor = 'text-[#ff9f0a]';
              }

              return (
                <div key={idx} className="bg-[#f8f7f7] p-3 rounded-none border border-[rgba(15,0,0,0.12)]">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold text-[#201d1d] flex items-center gap-1.5">
                      <span className={`font-bold ${textColor}`}>{prefixMarker}</span>
                      <span>{factorName}</span>
                    </span>
                    <span className={`font-mono font-bold ${textColor}`}>
                      +{typeof weight === 'number' ? weight.toFixed(0) : weight}%
                    </span>
                  </div>
                  {/* ASCII Terminal Bar */}
                  <div className="text-xs font-mono tracking-tight" style={{ color: weight > 30 ? '#ff3b30' : weight > 15 ? '#ff9f0a' : '#30d158' }}>
                    [{asciiFill}]
                  </div>
                  {details && <p className="text-[11px] text-[#646262] mt-1 font-mono">{details}</p>}
                </div>
              );
            });
          })()}
        </div>
      </div>

      {/* Risk Reason Summary Footer */}
      {riskReason && (
        <div className="mt-4 pt-3 border-t border-[rgba(15,0,0,0.12)] flex items-start gap-2 text-xs text-[#201d1d] bg-[#f8f7f7] p-2.5 rounded-none border border-[rgba(15,0,0,0.12)]">
          <Info className="w-4 h-4 text-[#007aff] shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-[#201d1d]">[RATIONALE]: </span>
            <span className="text-[#424245]">{riskReason}</span>
          </div>
        </div>
      )}
    </div>
  );
}
