import React, { useState, useEffect, useRef } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { ShieldCheck, ShieldAlert, Mic, Square, Upload, X, CheckCircle2, XCircle, RefreshCw } from 'lucide-react';
import { API_BASE_URL, getAuthHeaders } from '../config';

export default function ChallengeModal({ isOpen, onClose, claimedIdentity }) {
  const [challengeData, setChallengeData] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);

  // Audio recording state
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Fetch new challenge when modal opens
  useEffect(() => {
    if (isOpen) {
      generateNewChallenge();
      setVerifyResult(null);
      setAudioBlob(null);
      setAudioFile(null);
    }
  }, [isOpen]);

  const generateNewChallenge = async () => {
    setGenerating(true);
    setVerifyResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/challenge/generate`, {
        method: 'POST',
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setChallengeData(data);
      } else {
        console.error('Failed to generate challenge');
      }
    } catch (err) {
      console.error('Challenge generation error:', err);
    } finally {
      setGenerating(false);
    }
  };

  // Record mic audio
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      alert('Microphone access failed: ' + err.message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Submit response for verification
  const handleVerify = async () => {
    if (!challengeData?.challenge_id) {
      alert('No active challenge');
      return;
    }
    const fileToUpload = audioFile || (audioBlob ? new File([audioBlob], 'response.wav', { type: 'audio/wav' }) : null);
    if (!fileToUpload) {
      alert('Please record or upload caller audio response');
      return;
    }

    setVerifying(true);
    setVerifyResult(null);

    try {
      const formData = new FormData();
      formData.append('challenge_id', challengeData.challenge_id);
      formData.append('file', fileToUpload);

      const res = await fetch(`${API_BASE_URL}/challenge/verify`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setVerifyResult(data);
      } else {
        const errData = await res.json();
        alert(`Verification failed: ${errData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      alert(`Verification error: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => { if (!open) onClose(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-[#201d1d]/60 backdrop-blur-sm z-50 animate-fadeIn" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] rounded-[4px] p-6 shadow-none z-50 text-[#201d1d] font-mono">
          <div className="flex items-center justify-between border-b border-[rgba(15,0,0,0.12)] pb-3 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-[4px] bg-[#ff9f0a]/10 border border-[#ff9f0a]/30 text-[#ff9f0a]">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <Dialog.Title className="text-sm font-bold text-[#201d1d] tracking-wider">
                  CHALLENGE VERIFICATION PROTOCOL
                </Dialog.Title>
                <Dialog.Description className="text-xs text-[#646262]">
                  Interactive phrase challenge to verify live caller authenticity.
                </Dialog.Description>
              </div>
            </div>
            <Dialog.Close asChild>
              <button className="p-1 rounded-[4px] hover:bg-[#f1eeee] text-[#646262] hover:text-[#201d1d] transition-colors">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          {/* Generated Challenge Phrase Display */}
          <div className="bg-[#f8f7f7] p-4 rounded-none border border-[rgba(15,0,0,0.12)] mb-5 text-center">
            <span className="text-[11px] font-semibold text-[#646262] uppercase tracking-wider block mb-1">
              INSTRUCT CALLER TO SPEAK THIS PHRASE:
            </span>
            {generating ? (
              <div className="flex items-center justify-center gap-2 py-3 text-[#30d158] text-sm">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Generating security phrase...</span>
              </div>
            ) : (
              <div className="my-2">
                <p className="text-base font-bold text-[#201d1d] font-mono tracking-wide border-y border-[rgba(15,0,0,0.12)] py-2">
                  "{challengeData?.phrase || 'Swift Crimson Arrow'}"
                </p>
                <p className="text-xs text-[#646262] mt-2 italic">
                  {challengeData?.prompt || 'Please ask the caller to read the phrase above clearly into their microphone.'}
                </p>
              </div>
            )}

            <button
              onClick={generateNewChallenge}
              disabled={generating}
              className="mt-2 text-xs text-[#30d158] hover:underline inline-flex items-center gap-1 font-mono transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              <span>GENERATE DIFFERENT PHRASE</span>
            </button>
          </div>

          {/* Response Audio Input Controls */}
          <div className="space-y-3 mb-5">
            <span className="text-xs font-bold text-[#201d1d] block">CAPTURE CALLER RESPONSE AUDIO:</span>

            <div className="grid grid-cols-2 gap-3">
              {/* Record Microphone */}
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`flex items-center justify-center gap-2 p-3 rounded-[4px] border text-xs font-mono font-bold transition-all ${
                  isRecording
                    ? 'bg-[#ff3b30]/10 border-[#ff3b30] text-[#ff3b30] animate-pulse'
                    : 'bg-[#f8f7f7] border-[rgba(15,0,0,0.12)] hover:border-[#646262] text-[#201d1d]'
                }`}
              >
                {isRecording ? (
                  <>
                    <Square className="w-4 h-4 fill-current text-[#ff3b30]" />
                    <span>STOP RECORDING</span>
                  </>
                ) : (
                  <>
                    <Mic className="w-4 h-4 text-[#30d158]" />
                    <span>{audioBlob ? 'RE-RECORD MIC' : 'RECORD MIC'}</span>
                  </>
                )}
              </button>

              {/* Upload Audio File */}
              <label className="flex items-center justify-center gap-2 p-3 rounded-[4px] bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] hover:border-[#646262] text-[#201d1d] text-xs font-mono font-bold cursor-pointer transition-all">
                <Upload className="w-4 h-4 text-[#30d158]" />
                <span className="truncate">{audioFile ? audioFile.name : 'UPLOAD FILE'}</span>
                <input
                  type="file"
                  accept="audio/*"
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      setAudioFile(e.target.files[0]);
                      setAudioBlob(null);
                    }
                  }}
                  className="hidden"
                />
              </label>
            </div>

            {(audioBlob || audioFile) && (
              <div className="bg-[#f8f7f7] p-2.5 rounded-none border border-[rgba(15,0,0,0.12)] flex items-center justify-between text-xs text-[#201d1d]">
                <span className="truncate font-mono">
                  READY: {audioFile ? audioFile.name : 'RECORDED MIC AUDIO (.WAV)'}
                </span>
                <span className="text-[10px] text-[#30d158] font-bold uppercase px-2 py-0.5 rounded-[4px] bg-[#30d158]/10 border border-[#30d158]/30">
                  CAPTURED
                </span>
              </div>
            )}
          </div>

          {/* Verification Results Panel */}
          {verifyResult && (
            <div className={`p-4 rounded-none border mb-5 animate-fadeIn font-mono ${
              verifyResult.matched
                ? 'bg-[#30d158]/10 border-[#30d158]/30 text-[#30d158]'
                : 'bg-[#ff3b30]/10 border-[#ff3b30]/30 text-[#ff3b30]'
            }`}>
              <div className="flex items-center gap-2 font-bold text-xs mb-2">
                {verifyResult.matched ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-[#30d158]" />
                    <span>✓ VERIFICATION MATCHED — CALLER AUTHENTICATED</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 text-[#ff3b30]" />
                    <span>✗ VERIFICATION FAILED — PHRASE MISMATCH</span>
                  </>
                )}
              </div>

              <div className="space-y-1 text-xs font-mono">
                <div>
                  <span className="text-[#646262]">Transcribed Text: </span>
                  <span className="font-bold text-[#201d1d]">"{verifyResult.transcribed_text || 'Unclear audio'}"</span>
                </div>
                <div>
                  <span className="text-[#646262]">Expected Phrase: </span>
                  <span className="text-[#201d1d]">"{verifyResult.expected_phrase}"</span>
                </div>
                <div>
                  <span className="text-[#646262]">Match Confidence: </span>
                  <span className="font-bold text-[#201d1d]">{((verifyResult.confidence || 0) * 100).toFixed(1)}%</span>
                  <span className="text-[10px] text-[#646262] ml-2">(Threshold: ≥ 85%)</span>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[rgba(15,0,0,0.12)]">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-[4px] bg-[#f8f7f7] hover:bg-[#f1eeee] border border-[rgba(15,0,0,0.12)] text-[#646262] hover:text-[#201d1d] text-xs font-mono transition-colors"
            >
              CLOSE PROTOCOL
            </button>

            <button
              onClick={handleVerify}
              disabled={verifying || (!audioBlob && !audioFile)}
              className="px-5 py-2.5 rounded-[4px] bg-[#201d1d] hover:bg-[#0f0000] text-[#fdfcfc] disabled:opacity-50 text-xs font-mono font-bold transition-all flex items-center gap-2"
            >
              {verifying ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Verifying Audio Response...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>VERIFY CHALLENGE RESPONSE</span>
                </>
              )}
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
