// src/api/axios.js
import axios from 'axios';

const API = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

const AUTH_SKIP_PATHS = [
  '/auth/login/',
  '/auth/register/',
  '/auth/token/refresh/',
];

const isAuthEndpoint = (url = '') =>
  AUTH_SKIP_PATHS.some((path) => url.includes(path));

export const clearSession = () => {
  localStorage.removeItem('tokens');
  localStorage.removeItem('user');
};

export const getStoredTokens = () => {
  try {
    const raw = localStorage.getItem('tokens');
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    // Support ancien format { tokens: { access, refresh } }
    if (parsed?.tokens?.access) return parsed.tokens;
    if (parsed?.access) return parsed;
    return null;
  } catch {
    clearSession();
    return null;
  }
};

export const storeTokens = (payload) => {
  const tokens = payload?.access ? payload : payload?.tokens;
  if (!tokens?.access) {
    throw new Error('Réponse login invalide : tokens manquants.');
  }
  localStorage.setItem('tokens', JSON.stringify(tokens));
  return tokens;
};

// ── Intercepteur requête : injecte le JWT automatiquement ──
API.interceptors.request.use(
  (config) => {
    const tokens = getStoredTokens();
    config.headers = config.headers || {};
    if (tokens?.access) {
      config.headers.Authorization = `Bearer ${tokens.access}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Intercepteur réponse : refresh automatique si 401 ──
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((p) => {
    if (error) p.reject(error);
    else p.resolve(token);
  });
  failedQueue = [];
};

API.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Ne pas intercepter login/register/refresh (évite boucles et redirections)
    if (!originalRequest || isAuthEndpoint(originalRequest.url)) {
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return API(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const tokens = getStoredTokens();
      if (!tokens?.refresh) {
        isRefreshing = false;
        clearSession();
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post('/api/auth/token/refresh/', {
          refresh: tokens.refresh,
        });
        const newTokens = { ...tokens, access: data.access };
        localStorage.setItem('tokens', JSON.stringify(newTokens));
        processQueue(null, data.access);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return API(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearSession();
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export default API;
