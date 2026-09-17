import React, { useState, useEffect, useRef } from 'react';
import { 
  UserPlus, 
  Mic, 
  Square, 
  Upload, 
  Users, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  RefreshCw, 
  Volume2,
  ShieldCheck,
  FileAudio
} from 'lucide-react';
import { API_BASE_URL, getAuthHeaders } from '../config';

export default function EnrollmentForm() {
  const [speakerId, setSpeakerId] = useState('');
  const [file, setFile] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordTime, setRecordTime] = useState(0);
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const [enrolledList, setEnrolledList] = useState([]);
  const [fetchingList, setFetchingList] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  useEffect(() => {
    fetchEnrolledSpeakers();
  }, []);

  const fetchEnrolledSpeakers = async () => {
    setFetchingList(true);
    try {
      const res = await fetch(`${API_BASE_URL}/enrolled`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setEnrolledList(data.enrolled_speakers || []);
      } else {
        console.error('Failed to fetch enrolled speakers');
      }
    } catch (err) {
      console.error('Error fetching enrolled speakers:', err);
    } finally {
      setFetchingList(false);
    }
  };

  const startRecording = async () => {
    setError(null);
    setMessage(null);
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
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setRecordedBlob(audioBlob);
        setFile(null); // Clear file selection if mic was used
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordTime(0);

      timerRef.current = setInterval(() => {
        setRecordTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Microphone error:', err);
      setError('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setRecordedBlob(null);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!speakerId.trim()) {
      setError('Please provide a speaker name or ID.');
      return;
    }

    const audioToUpload = file || (recordedBlob ? new File([recordedBlob], 'enrollment_mic.wav', { type: 'audio/wav' }) : null);

    if (!audioToUpload) {
      setError('Please upload an audio file or record a voice sample.');
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    const formData = new FormData();
    formData.append('speaker_id', speakerId.trim());
    formData.append('file', audioToUpload);

    try {
      const res = await fetch(`${API_BASE_URL}/enroll`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Enrollment failed.');
      }

      setMessage(`Successfully enrolled reference voice for "${speakerId.trim()}"`);
      setSpeakerId('');
      setFile(null);
      setRecordedBlob(null);
      setRecordTime(0);
      fetchEnrolledSpeakers();
    } catch (err) {
      console.error('Enrollment error:', err);
      setError(err.message || 'An error occurred during enrollment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 font-mono">
      {/* Top Header Card */}
      <div className="bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] rounded-none p-5 md:p-6">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-[#30d158]/10 text-[#30d158] rounded-[4px] border border-[#30d158]/30">
            <UserPlus className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-[#201d1d] tracking-wider">[SPEAKER VOICE ENROLLMENT PROTOCOL]</h2>
            <p className="text-xs text-[#646262] mt-0.5">
              Register verified voiceprints to enable automatic biometric identity verification & ECAPA-TDNN match scoring.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Enrollment Form Panel */}
        <div className="lg:col-span-7 bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] rounded-none p-5 md:p-6">
          <h3 className="text-xs font-bold text-[#646262] uppercase tracking-wider mb-4 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#30d158]" />
            <span>[NEW SPEAKER REGISTRATION]</span>
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Speaker ID input */}
            <div>
              <label className="block text-xs font-semibold text-[#646262] uppercase tracking-wider mb-1.5">
                Speaker Name / Unique ID <span className="text-[#30d158]">*</span>
              </label>
              <input
                type="text"
                value={speakerId}
                onChange={(e) => setSpeakerId(e.target.value)}
                placeholder="e.g. CEO - Jane Doe or CustID-99412"
                className="w-full bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] rounded-[4px] px-3.5 py-2 text-xs text-[#201d1d] placeholder-[#9a9898] focus:outline-none focus:border-[#201d1d] font-mono transition-colors"
                required
              />
            </div>

            {/* Audio Source Selection */}
            <div>
              <label className="block text-xs font-semibold text-[#646262] uppercase tracking-wider mb-1.5">
                Reference Audio Sample <span className="text-[#30d158]">*</span>
              </label>

              <div className="grid grid-cols-2 gap-3 mb-3">
                {/* Option A: Microphone */}
                <div 
                  className={`border rounded-[4px] p-4 cursor-pointer transition-all flex flex-col items-center justify-center text-center font-mono ${
                    isRecording 
                      ? 'border-[#ff3b30] bg-[#ff3b30]/10 text-[#ff3b30]' 
                      : recordedBlob 
                      ? 'border-[#30d158]/40 bg-[#30d158]/10 text-[#30d158]' 
                      : 'border-[rgba(15,0,0,0.12)] bg-[#f8f7f7] hover:border-[#646262] text-[#201d1d]'
                  }`}
                  onClick={isRecording ? stopRecording : startRecording}
                >
                  <div className={`p-2.5 rounded-[4px] mb-2 ${
                    isRecording ? 'bg-[#ff3b30]/20 text-[#ff3b30] animate-pulse' : 'bg-[#f1eeee] text-[#30d158]'
                  }`}>
                    {isRecording ? <Square className="w-4 h-4 fill-current text-[#ff3b30]" /> : <Mic className="w-4 h-4" />}
                  </div>
                  <span className="text-xs font-semibold">
                    {isRecording ? `[RECORDING... ${recordTime}s]` : recordedBlob ? '[AUDIO CAPTURED ✓]' : '[RECORD MIC]'}
                  </span>
                  <span className="text-[11px] text-[#646262] mt-0.5">
                    {isRecording ? 'Click to finish' : 'Click to record sample'}
                  </span>
                </div>

                {/* Option B: File Upload */}
                <label className={`border rounded-[4px] p-4 cursor-pointer transition-all flex flex-col items-center justify-center text-center font-mono ${
                  file ? 'border-[#30d158]/40 bg-[#30d158]/10 text-[#30d158]' : 'border-[rgba(15,0,0,0.12)] bg-[#f8f7f7] hover:border-[#646262] text-[#201d1d]'
                }`}>
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <div className="p-2.5 rounded-[4px] bg-[#f1eeee] text-[#30d158] mb-2">
                    <Upload className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-semibold truncate max-w-[140px]">
                    {file ? `[${file.name}]` : '[UPLOAD FILE]'}
                  </span>
                  <span className="text-[11px] text-[#646262] mt-0.5">.wav, .mp3, .flac</span>
                </label>
              </div>

              {/* Status indicator for selected audio */}
              {(file || recordedBlob) && (
                <div className="flex items-center space-x-2 text-xs text-[#30d158] bg-[#30d158]/10 border border-[#30d158]/30 rounded-[4px] p-2.5 font-mono">
                  <FileAudio className="w-4 h-4 shrink-0" />
                  <span className="truncate">
                    READY TO ENROLL: {file ? file.name : `MIC RECORDING (${recordTime}s)`}
                  </span>
                </div>
              )}
            </div>

            {/* Error / Success Notifications */}
            {error && (
              <div className="flex items-center space-x-2 text-xs text-[#ff3b30] bg-[#ff3b30]/10 border border-[#ff3b30]/30 rounded-none p-3 font-mono">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>[{error}]</span>
              </div>
            )}

            {message && (
              <div className="flex items-center space-x-2 text-xs text-[#30d158] bg-[#30d158]/10 border border-[#30d158]/30 rounded-none p-3 font-mono">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>[{message}]</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || (!file && !recordedBlob) || !speakerId.trim()}
              className={`w-full py-2.5 px-4 rounded-[4px] font-bold text-xs font-mono transition-all flex items-center justify-center space-x-2 ${
                loading || (!file && !recordedBlob) || !speakerId.trim()
                  ? 'bg-[#f1eeee] text-[#9a9898] border border-[rgba(15,0,0,0.12)] cursor-not-allowed'
                  : 'bg-[#201d1d] hover:bg-[#0f0000] text-[#fdfcfc]'
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#007aff]" />
                  <span>[EXTRACTING EMBEDDINGS & ENROLLING...]</span>
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  <span>[-&gt;] ENROLL REFERENCE SPEAKER</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Enrolled Speakers Directory Panel */}
        <div className="lg:col-span-5 bg-[#fdfcfc] border border-[rgba(15,0,0,0.12)] rounded-none p-5 md:p-6 flex flex-col font-mono">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-bold text-[#201d1d] uppercase tracking-wider flex items-center gap-2">
              <Users className="w-4 h-4 text-[#30d158]" />
              <span>[ENROLLED DIRECTORY]</span>
            </h3>
            <button
              onClick={fetchEnrolledSpeakers}
              disabled={fetchingList}
              className="p-1.5 text-[#646262] hover:text-[#201d1d] hover:bg-[#f1eeee] rounded-[4px] transition-colors"
              title="Refresh Directory"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${fetchingList ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto max-h-[380px] space-y-2 pr-1 custom-scrollbar">
            {fetchingList && enrolledList.length === 0 ? (
              <div className="py-8 text-center text-xs text-[#646262] flex items-center justify-center space-x-2 font-mono">
                <Loader2 className="w-4 h-4 animate-spin text-[#30d158]" />
                <span>Loading directory...</span>
              </div>
            ) : enrolledList.length === 0 ? (
              <div className="py-10 text-center border border-dashed border-[rgba(15,0,0,0.12)] rounded-none font-mono">
                <Volume2 className="w-7 h-7 text-[#646262] mx-auto mb-2 opacity-50" />
                <p className="text-xs text-[#646262] font-semibold">[NO SPEAKERS ENROLLED YET]</p>
                <p className="text-[11px] text-[#9a9898] mt-0.5">Register a speaker using the form on the left.</p>
              </div>
            ) : (
              enrolledList.map((id, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-[#f8f7f7] border border-[rgba(15,0,0,0.12)] rounded-none hover:border-[#646262] transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-[4px] bg-[#30d158]/10 text-[#30d158] flex items-center justify-center text-xs font-bold border border-[#30d158]/30">
                      {id.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#201d1d]">{id}</div>
                      <div className="text-[10px] text-[#646262]">ECAPA-TDNN Embedding Stored</div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono uppercase bg-[#30d158]/10 text-[#30d158] border border-[#30d158]/30 px-2 py-0.5 rounded-[4px]">
                    [ACTIVE]
                  </span>
                </div>
              ))
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-[rgba(15,0,0,0.12)] flex items-center justify-between text-[11px] text-[#646262]">
            <span>Total Enrolled: {enrolledList.length}</span>
            <span>Encrypted Vectors</span>
          </div>
        </div>
      </div>
    </div>
  );
}
