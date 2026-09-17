import React from 'react';
import { AlertOctagon, ShieldCheck, ShieldAlert, AlertTriangle, HelpCircle } from 'lucide-react';

export default function RiskMeter({ riskScore = 0, riskTier = 'LOW', rawScore = null, riskReason = null }) {
  const normTier = (riskTier || 'LOW').toUpperCase();

  // Tier configuration dictionary (OpenCode AI Apple-style HIG semantic colors)
  const TIER_CONFIG = {
    LOW: {
      color: '#30d158', // Apple Green
      badgeClass: 'bg-[#30d158]/10 text-[#30d158] border-[#30d158]/30',
      icon: ShieldCheck,
      description: 'Low fraud probability. Synthetic and context signals normal.',
    },
    MEDIUM: {
      color: '#ff9f0a', // Apple Amber
      badgeClass: 'bg-[#ff9f0a]/10 text-[#ff9f0a] border-[#ff9f0a]/30',
      icon: AlertTriangle,
      description: 'Moderate risk. Elevated urgency or unverified contact parameters.',
    },
    HIGH: {
      color: '#ff9f0a', // Apple Orange/Amber
      badgeClass: 'bg-[#ff9f0a]/10 text-[#ff9f0a] border-[#ff9f0a]/40',
      icon: ShieldAlert,
      description: 'High risk detected. Voice anomaly or cumulative context weight flagged.',
    },
    CRITICAL: {
      color: '#ff3b30', // Apple Red
      badgeClass: 'bg-[#ff3b30]/10 text-[#ff3b30] border-[#ff3b30]/40 animate-pulse',
      icon: AlertOctagon,
      description: 'CRITICAL THREAT: Deepfake voice synthesis or multi-factor attack detected!',
    },
    INCONCLUSIVE: {
      color: '#646262', // Mute Stone
      badgeClass: 'bg-[#f8f7f7] text-[#646262] border border-[rgba(15,0,0,0.12)]',
      icon: HelpCircle,
      description: 'Insufficient audio duration or degraded signal quality.',
    },
  };

  const config = TIER_CONFIG[normTier] || TIER_CONFIG.INCONCLUSIVE;
  const TierIcon = config.icon;

  // SVG Arc Calculation (270 degree arc)
  const size = 190;
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75;
  const safeScore = Math.min(100, Math.max(0, riskScore));
  const dashoffset = arcLength - (safeScore / 100) * arcLength;

  // ASCII Progress Bar generator
  const totalBlocks = 20;
  const filledBlocks = Math.round((safeScore / 100) * totalBlocks);
  const asciiBar = '█'.repeat(filledBlocks) + '░'.repeat(totalBlocks - filledBlocks);

  return (
    <div className="bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] rounded-none p-5 md:p-6 flex flex-col items-center justify-between text-center font-mono w-full">
      {/* TUI Card Header */}
      <div className="w-full flex items-center justify-between text-xs border-b border-[rgba(15,0,0,0.12)] pb-3 mb-4">
        <span className="font-bold uppercase tracking-wider text-[#646262] text-[11px]">[REAL-TIME RISK METER]</span>
        {rawScore !== null && rawScore !== undefined && (
          <span className="font-mono text-[11px] text-[#646262]" title="Raw AASIST-L logit score">
            LOGIT: <strong className="text-[#201d1d]">{typeof rawScore === 'number' ? rawScore.toFixed(3) : rawScore}</strong>
          </span>
        )}
      </div>

      {/* SVG Arc Gauge */}
      <div className="relative flex items-center justify-center my-1">
        <svg width={size} height={size} className="transform -rotate-225">
          {/* Track Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(15,0,0,0.12)"
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeLinecap="square"
          />
          {/* Progress Arc with 300ms transition */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={config.color}
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeDashoffset={dashoffset}
            strokeLinecap="square"
            className="transition-all duration-300 ease-out"
          />
        </svg>

        {/* Inner Score Display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-4xl font-extrabold font-mono text-[#201d1d]">
            {Math.round(safeScore)}
          </span>
          <span className="text-[10px] font-mono text-[#646262] uppercase tracking-wider mt-0.5">[SCORE / 100]</span>
        </div>
      </div>

      {/* ASCII Terminal Bar Readout */}
      <div className="my-2 bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] px-3 py-1.5 rounded-[4px] text-xs text-[#646262] font-mono">
        <span style={{ color: config.color }}>[{asciiBar}]</span>
        <span className="ml-2 text-[#201d1d] font-bold">{Math.round(safeScore)}%</span>
      </div>

      {/* Risk Tier Bracketed Badge */}
      <div className="mt-3 w-full flex flex-col items-center gap-2">
        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-[4px] border text-xs font-mono font-bold tracking-wider uppercase transition-all duration-300 ${config.badgeClass}`}>
          <TierIcon className="w-3.5 h-3.5" />
          <span>[{normTier} RISK TIER]</span>
        </div>
        <p className="text-xs text-[#424245] max-w-xs leading-relaxed mt-1 font-mono">
          {riskReason || config.description}
        </p>
      </div>
    </div>
  );
}
