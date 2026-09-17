import React from 'react';
import { DollarSign, User, Phone, Zap, UserPlus } from 'lucide-react';
import * as Switch from '@radix-ui/react-switch';

export default function TransactionForm({
  callerNumber,
  setCallerNumber,
  claimedIdentity,
  setClaimedIdentity,
  transactionAmount,
  setTransactionAmount,
  amount,
  setAmount,
  newBeneficiary,
  setNewBeneficiary,
  urgency,
  setUrgency,
  enrolledList = [],
}) {
  const currentAmount = transactionAmount !== undefined ? transactionAmount : (amount || '');
  const handleAmountChange = (val) => {
    if (setTransactionAmount) setTransactionAmount(val);
    if (setAmount) setAmount(val);
  };

  return (
    <div className="bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] rounded-none p-5 md:p-6 font-mono">
      <h3 className="text-xs font-bold text-[#646262] uppercase tracking-wider mb-4 flex items-center gap-2">
        <DollarSign className="w-4 h-4 text-[#30d158]" />
        <span>[TRANSACTION CONTEXT & CALL PARAMETERS]</span>
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Caller Number Input */}
        <div>
          <label className="block text-xs font-semibold text-[#302c2c] mb-1.5 flex items-center gap-1.5">
            <Phone className="w-3.5 h-3.5 text-[#646262]" />
            <span>Caller Phone Number</span>
          </label>
          <input
            type="text"
            value={callerNumber || ''}
            onChange={(e) => setCallerNumber && setCallerNumber(e.target.value)}
            placeholder="+1 (555) 019-2834"
            className="w-full bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] rounded-[4px] px-3.5 py-2 text-xs text-[#201d1d] placeholder-[#9a9898] focus:outline-none focus:border-[#201d1d] font-mono transition-colors"
          />
        </div>

        {/* Claimed Identity Selection / Input */}
        <div>
          <label className="block text-xs font-semibold text-[#302c2c] mb-1.5 flex items-center gap-1.5">
            <User className="w-3.5 h-3.5 text-[#646262]" />
            <span>Claimed Identity (Voiceprint)</span>
          </label>
          <div className="relative">
            <input
              type="text"
              list="enrolled-speakers-list"
              value={claimedIdentity || ''}
              onChange={(e) => setClaimedIdentity && setClaimedIdentity(e.target.value)}
              placeholder="Select or enter speaker ID..."
              className="w-full bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] rounded-[4px] px-3.5 py-2 text-xs text-[#201d1d] placeholder-[#9a9898] focus:outline-none focus:border-[#201d1d] font-mono transition-colors"
            />
            {enrolledList && enrolledList.length > 0 && (
              <datalist id="enrolled-speakers-list">
                {enrolledList.map((spk, idx) => (
                  <option key={idx} value={spk} />
                ))}
              </datalist>
            )}
          </div>
        </div>

        {/* Transaction Amount ($) Input */}
        <div>
          <label className="block text-xs font-semibold text-[#302c2c] mb-1.5 flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-[#646262]" />
            <span>Transfer Amount ($ USD)</span>
          </label>
          <input
            type="number"
            value={currentAmount}
            onChange={(e) => handleAmountChange(e.target.value)}
            placeholder="50000"
            className="w-full bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] rounded-[4px] px-3.5 py-2 text-xs text-[#201d1d] placeholder-[#9a9898] focus:outline-none focus:border-[#201d1d] font-mono transition-colors"
          />
        </div>
      </div>

      {/* Context Toggles Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4 pt-4 border-t border-[rgba(15,0,0,0.12)]">
        {/* New Beneficiary Toggle */}
        <div className="flex items-center justify-between bg-[#f8f7f7] p-3 rounded-none border border-[rgba(15,0,0,0.12)]">
          <div className="flex items-center gap-3">
            <UserPlus className={`w-4 h-4 ${newBeneficiary ? 'text-[#ff9f0a]' : 'text-[#646262]'}`} />
            <div>
              <span className="text-xs font-semibold text-[#201d1d] block">New / Unrecognized Beneficiary</span>
              <span className="text-[11px] text-[#646262]">First-time wire recipient or unverified account</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-[#646262]">{newBeneficiary ? '[ENABLED]' : '[DISABLED]'}</span>
            <Switch.Root
              checked={!!newBeneficiary}
              onCheckedChange={(val) => setNewBeneficiary && setNewBeneficiary(val)}
              className={`w-9 h-5 rounded-[4px] relative transition-colors focus:outline-none border ${
                newBeneficiary ? 'bg-[#ff9f0a]/20 border-[#ff9f0a]' : 'bg-[#f1eeee] border-[rgba(15,0,0,0.12)]'
              }`}
            >
              <Switch.Thumb
                className={`block w-3.5 h-3.5 rounded-[4px] bg-white transition-transform transform translate-x-0.5 mt-0.5 ${
                  newBeneficiary ? 'translate-x-4 bg-[#ff9f0a]' : 'translate-x-0.5 bg-[#646262]'
                }`}
              />
            </Switch.Root>
          </div>
        </div>

        {/* Urgency / High Pressure Toggle */}
        <div className="flex items-center justify-between bg-[#f8f7f7] p-3 rounded-none border border-[rgba(15,0,0,0.12)]">
          <div className="flex items-center gap-3">
            <Zap className={`w-4 h-4 ${urgency ? 'text-[#ff3b30]' : 'text-[#646262]'}`} />
            <div>
              <span className="text-xs font-semibold text-[#201d1d] block">Caller Urgency & Pressure</span>
              <span className="text-[11px] text-[#646262]">High pressure request to bypass security protocol</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-[#646262]">{urgency ? '[ENABLED]' : '[DISABLED]'}</span>
            <Switch.Root
              checked={!!urgency}
              onCheckedChange={(val) => setUrgency && setUrgency(val)}
              className={`w-9 h-5 rounded-[4px] relative transition-colors focus:outline-none border ${
                urgency ? 'bg-[#ff3b30]/20 border-[#ff3b30]' : 'bg-[#f1eeee] border-[rgba(15,0,0,0.12)]'
              }`}
            >
              <Switch.Thumb
                className={`block w-3.5 h-3.5 rounded-[4px] bg-white transition-transform transform translate-x-0.5 mt-0.5 ${
                  urgency ? 'translate-x-4 bg-[#ff3b30]' : 'translate-x-0.5 bg-[#646262]'
                }`}
              />
            </Switch.Root>
          </div>
        </div>
      </div>
    </div>
  );
}
