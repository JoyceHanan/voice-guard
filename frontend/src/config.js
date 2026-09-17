// Configuration for VoiceGuard Frontend

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
export const API_KEY = import.meta.env.VITE_VOICEGUARD_API_KEY || 'vg_secret_key_12345';

export const getWsUrl = (claimedIdentity = '') => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = API_BASE_URL.replace(/^https?:\/\//, '');
  let url = `${wsProtocol}//${host}/ws/analyze?api_key=${encodeURIComponent(API_KEY)}`;
  if (claimedIdentity) {
    url += `&claimed_identity=${encodeURIComponent(claimedIdentity)}`;
  }
  return url;
};

export const getAuthHeaders = () => ({
  'X-API-Key': API_KEY,
});
