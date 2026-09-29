// Research credentials apply only to this configured analysis backend.
export function apiFetch(url, options = {}) {
  const target = new URL(url, window.location.origin);
  if (!(target.origin === window.location.origin && target.pathname.startsWith('/api/')) && target.origin !== 'http://localhost:8000') {
    throw new Error('Research credential is restricted to the configured local analysis API.');
  }
  const headers = new Headers(options.headers);
  const key = sessionStorage.getItem('privacyguard-research-key');
  if (key) headers.set('X-Research-Key', key);
  return fetch(url, { ...options, headers });
}
