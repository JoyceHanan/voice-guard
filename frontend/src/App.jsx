import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import CorrelationBanner from './components/CorrelationBanner';
import CallerPanel from './components/CallerPanel';
import RiskMeter from './components/RiskMeter';
import EvidenceBreakdown from './components/EvidenceBreakdown';
import TransactionForm from './components/TransactionForm';
import ActionBanner from './components/ActionBanner';
import ChallengeModal from './components/ChallengeModal';
import EnrollmentForm from './components/EnrollmentForm';

import { 
  Upload, 
  Mic, 
  Square, 
  Play, 
  Activity, 
  AlertCircle, 
  RefreshCw,
  Radio
} from 'lucide-react';
import { API_BASE_URL, API_KEY, getWsUrl, getAuthHeaders } from './config';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'enrollment'

  // Context & Call State
  const [callerNumber, setCallerNumber] = useState('');
  const [claimedIdentity, setClaimedIdentity] = useState('');
  const [newBeneficiary, setNewBeneficiary] = useState(false);
  const [urgency, setUrgency] = useState(false);
  const [transactionAmount, setTransactionAmount] = useState('');

  // Enrolled speakers list (for identity picker)
  const [enrolledList, setEnrolledList] = useState([]);

  // File Upload Mode State
  const [file, setFile] = useState(null);
  const [analyzingFile, setAnalyzingFile] = useState(false);

  // Live Stream Mode State
  const [isStreaming, setIsStreaming] = useState(false);
  const [wsStatus, setWsStatus] = useState('disconnected'); // 'disconnected' | 'connecting' | 'connected' | 'error'
  const wsRef = useRef(null);
  const mediaRecorderRef = useRef(null);

  // Challenge Modal State
  const [isChallengeOpen, setIsChallengeOpen] = useState(false);

  // Analysis Results State
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);

  // Fetch enrolled speakers for selection
  const fetchEnrolled = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/enrolled`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setEnrolledList(data.enrolled_speakers || []);
      }
    } catch (err) {
      console.error('Error fetching enrolled speakers in App:', err);
    }
  };

  useEffect(() => {
    fetchEnrolled();
  }, [activeTab]);

  // Clean up WebSocket & MediaRecorder on unmount
  useEffect(() => {
    return () => {
      stopLiveStreaming();
    };
  }, []);

  // --- POST /analyze Audio File Flow ---
  const handleAnalyzeFile = async () => {
    if (!file) {
      setError('Please select an audio file first.');
      return;
    }

    setAnalyzingFile(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    if (claimedIdentity) formData.append('claimed_identity', claimedIdentity);
    if (callerNumber) formData.append('caller_number', callerNumber);
    formData.append('new_beneficiary', newBeneficiary ? 'true' : 'false');
    formData.append('urgency', urgency ? 'true' : 'false');
    if (transactionAmount) formData.append('transaction_amount', transactionAmount);

    try {
      const res = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Analysis request failed.');
      }

      setAnalysisResult(data);
    } catch (err) {
      console.error('Analysis error:', err);
      setError(err.message || 'Failed to analyze audio.');
    } finally {
      setAnalyzingFile(false);
    }
  };

  // --- WebSocket Real-Time Audio Streaming Flow ---
  const startLiveStreaming = async () => {
    setError(null);
    setWsStatus('connecting');

    try {
      // 1. Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // 2. Build WS URL with parameters
      const params = new URLSearchParams({
        api_key: API_KEY,
        ...(claimedIdentity && { claimed_identity: claimedIdentity }),
        ...(callerNumber && { caller_number: callerNumber }),
        new_beneficiary: newBeneficiary ? 'true' : 'false',
        urgency: urgency ? 'true' : 'false',
        transaction_amount: transactionAmount || '0',
      });

      const wsUrl = `${getWsUrl('/ws/analyze')}?${params.toString()}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsStatus('connected');
        setIsStreaming(true);

        // Start MediaRecorder capturing 2-second binary chunks
        const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) {
            ws.send(e.data);
          }
        };

        // Slice audio every 2000ms (2s)
        mediaRecorder.start(2000);
      };

      ws.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);
          if (update.error) {
            setError(update.error);
            stopLiveStreaming();
            return;
          }

          // Map WebSocket update payload to standard result schema
          setAnalysisResult({
            risk_score: update.risk_score !== undefined ? update.risk_score : Math.round((update.smoothed_score || update.raw_score || 0) * 100),
            risk_tier: update.risk_tier || 'INCONCLUSIVE',
            risk_reason: update.risk_reason || update.result || 'Real-time WebSocket stream evaluation',
            voice_result: update.result || update.voice_result || 'INCONCLUSIVE',
            score: update.smoothed_score || update.raw_score || 0,
            duration: update.duration || 4.0,
            speaker_similarity: update.speaker_similarity,
            audio_quality: update.audio_quality || { label: 'GOOD', snr_db: 25.0 },
            caller_classification: update.caller_classification || { category: 'unknown_neutral', name: null, reason: 'Live call' },
            recommended_action: update.recommended_action || { tier: update.risk_tier, action: 'MONITOR_CALL', message: 'Monitoring ongoing stream...' },
            evidence_breakdown: update.evidence_breakdown || [],
            threshold: update.threshold || 2.1,
          });
        } catch (err) {
          console.error('Error parsing WS message:', err);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
        setWsStatus('error');
        setError('WebSocket connection error.');
      };

      ws.onclose = () => {
        setWsStatus('disconnected');
        setIsStreaming(false);
      };

    } catch (err) {
      console.error('Failed to start streaming:', err);
      setError('Could not access microphone for live streaming.');
      setWsStatus('disconnected');
    }
  };

  const stopLiveStreaming = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      if (mediaRecorderRef.current.stream) {
        mediaRecorderRef.current.stream.getTracks().forEach((t) => t.stop());
      }
    }
    if (wsRef.current) {
      wsRef.current.close();
    }
    setIsStreaming(false);
    setWsStatus('disconnected');
  };

  const handleReset = () => {
    setAnalysisResult(null);
    setFile(null);
    setError(null);
    if (isStreaming) {
      stopLiveStreaming();
    }
  };

  return (
    <div className="min-h-screen bg-[#fdfcfc] text-[#201d1d] flex flex-col font-mono antialiased">
      {/* Persistent Navigation */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Multi-Call Correlation Persistent Banner */}
      <CorrelationBanner />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 font-mono space-y-6">
        {activeTab === 'enrollment' ? (
          <EnrollmentForm />
        ) : (
          <div className="space-y-6">
            {/* Caller Identification Panel (Top) */}
            <CallerPanel
              callerNumber={callerNumber}
              callerClassification={analysisResult?.caller_classification}
              claimedIdentity={claimedIdentity}
            />

            {/* Audio Input Controls Bar */}
            <div className="bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] rounded-none p-4 flex flex-col md:flex-row items-center justify-between gap-4 font-mono">
              <div className="flex items-center space-x-3 w-full md:w-auto">
                <div className="p-2 bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] rounded-[4px] text-[#201d1d]">
                  <Radio className="w-4 h-4 text-[#007aff]" />
                </div>
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-[#646262]">[AUDIO EVALUATION MODE]</span>
                  <p className="text-xs text-[#201d1d]">Select File Upload or Real-Time Mic Stream</p>
                </div>
              </div>

              <div className="flex items-center space-x-2.5 w-full md:w-auto justify-end">
                {/* File Upload Selector & Trigger */}
                <label className="flex items-center space-x-2 bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] hover:border-[#646262] px-3 py-2 rounded-[4px] text-xs font-mono text-[#201d1d] cursor-pointer transition-colors">
                  <Upload className="w-3.5 h-3.5 text-[#646262]" />
                  <span className="truncate max-w-[120px]">{file ? file.name : '[CHOOSE FILE]'}</span>
                  <input
                    type="file"
                    accept="audio/*"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        setFile(e.target.files[0]);
                      }
                    }}
                  />
                </label>

                <button
                  onClick={handleAnalyzeFile}
                  disabled={analyzingFile || !file || isStreaming}
                  className={`px-3.5 py-2 rounded-[4px] text-xs font-mono font-bold transition-all flex items-center space-x-1.5 ${
                    analyzingFile || !file || isStreaming
                      ? 'bg-[#f1eeee] text-[#9a9898] border border-[rgba(15,0,0,0.12)] cursor-not-allowed'
                      : 'bg-[#201d1d] hover:bg-[#0f0000] text-[#fdfcfc]'
                  }`}
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>{analyzingFile ? '[ANALYZING...]' : '[ANALYZE FILE]'}</span>
                </button>

                <div className="h-5 w-[1px] bg-[rgba(15,0,0,0.12)] mx-1 hidden sm:block" />

                {/* Live Mic Streaming Toggle */}
                {isStreaming ? (
                  <button
                    onClick={stopLiveStreaming}
                    className="px-3.5 py-2 rounded-[4px] text-xs font-mono font-bold bg-[#ff3b30] hover:bg-[#d70015] text-[#fdfcfc] transition-all flex items-center space-x-1.5"
                  >
                    <Square className="w-3.5 h-3.5 fill-current" />
                    <span>[STOP STREAM]</span>
                  </button>
                ) : (
                  <button
                    onClick={startLiveStreaming}
                    disabled={analyzingFile}
                    className="px-3.5 py-2 rounded-[4px] text-xs font-mono font-bold bg-[#f8f7f7] hover:bg-[#f1eeee] border border-[rgba(15,0,0,0.12)] text-[#201d1d] transition-all flex items-center space-x-1.5"
                  >
                    <Mic className="w-3.5 h-3.5 text-[#30d158]" />
                    <span>[START STREAM]</span>
                  </button>
                )}

                {/* Reset button */}
                {analysisResult && (
                  <button
                    onClick={handleReset}
                    className="p-2 text-[#646262] hover:text-[#201d1d] hover:bg-[#f1eeee] rounded-[4px] transition-colors"
                    title="Reset Analysis"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* Connection / Stream Status Indicator */}
            {wsStatus !== 'disconnected' && (
              <div className="flex items-center justify-between bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] px-4 py-2 rounded-none text-xs font-mono">
                <div className="flex items-center space-x-2">
                  <span className={`w-2 h-2 rounded-full ${
                    wsStatus === 'connected' ? 'bg-[#30d158] animate-ping' : wsStatus === 'connecting' ? 'bg-[#ff9f0a] animate-pulse' : 'bg-[#ff3b30]'
                  }`} />
                  <span className="text-[#646262]">
                    WEBSOCKET STATUS: <strong className="text-[#201d1d] uppercase">[{wsStatus}]</strong>
                  </span>
                </div>
                {isStreaming && (
                  <span className="text-[11px] text-[#646262] flex items-center space-x-1.5 font-mono">
                    <Activity className="w-3.5 h-3.5 text-[#30d158] animate-pulse" />
                    <span>Streaming 2-second PCM chunks...</span>
                  </span>
                )}
              </div>
            )}

            {/* Error Notification */}
            {error && (
              <div className="flex items-center space-x-2 text-xs text-[#ff3b30] bg-[#ff3b30]/10 border border-[#ff3b30]/30 rounded-none p-4 font-mono">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>[{error}]</span>
              </div>
            )}

            {/* Center Area: Risk Meter (Left) + Evidence Breakdown (Right) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Center-Left: Risk Meter */}
              <div className="lg:col-span-5 flex">
                <RiskMeter
                  riskScore={analysisResult?.risk_score}
                  riskTier={analysisResult?.risk_tier}
                  riskReason={analysisResult?.risk_reason}
                  rawScore={analysisResult?.score}
                />
              </div>

              {/* Center-Right: Evidence Breakdown */}
              <div className="lg:col-span-7 flex">
                <EvidenceBreakdown
                  evidenceBreakdown={analysisResult?.evidence_breakdown}
                  audioQuality={analysisResult?.audio_quality}
                  voiceResult={analysisResult?.voice_result}
                  speakerSimilarity={analysisResult?.speaker_similarity}
                  claimedIdentity={claimedIdentity}
                  threshold={analysisResult?.threshold}
                  riskReason={analysisResult?.risk_reason}
                  duration={analysisResult?.duration}
                />
              </div>
            </div>

            {/* Below: Transaction & Call Context Form */}
            <TransactionForm
              callerNumber={callerNumber}
              setCallerNumber={setCallerNumber}
              claimedIdentity={claimedIdentity}
              setClaimedIdentity={setClaimedIdentity}
              newBeneficiary={newBeneficiary}
              setNewBeneficiary={setNewBeneficiary}
              urgency={urgency}
              setUrgency={setUrgency}
              transactionAmount={transactionAmount}
              setTransactionAmount={setTransactionAmount}
              enrolledList={enrolledList}
            />

            {/* Bottom: Prominent Action Banner */}
            <ActionBanner
              recommendedAction={analysisResult?.recommended_action}
              riskTier={analysisResult?.risk_tier}
              onOpenChallenge={() => setIsChallengeOpen(true)}
            />
          </div>
        )}
      </main>

      {/* Challenge Modal */}
      <ChallengeModal
        isOpen={isChallengeOpen}
        onClose={() => setIsChallengeOpen(false)}
        claimedIdentity={claimedIdentity}
      />
    </div>
  );
}
