const rawApiBase = (process.env.REACT_APP_API_BASE || '').trim();

function normalizeApiBase(value) {
  if (!value) return '';
  if (/^https?:\/\//i.test(value)) {
    return value.replace(/\/+$/, '');
  }
  return `https://${value.replace(/\/+$/, '')}`;
}

export const API_BASE = normalizeApiBase(rawApiBase);
