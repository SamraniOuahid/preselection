// src/context/AuthContext.jsx
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import API, { clearSession, getStoredTokens, storeTokens } from '../api/axios';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  // Vérifier la session au chargement
  useEffect(() => {
    const tokens = getStoredTokens();
    if (!tokens?.access) {
      clearSession();
      setUser(null);
      setLoading(false);
      return;
    }

    API.get('/auth/me/')
      .then(({ data }) => {
        setUser(data);
        localStorage.setItem('user', JSON.stringify(data));
      })
      .catch(() => {
        clearSession();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email, password) => {
    clearSession();
    const { data } = await API.post('/auth/login/', {
      email: email.trim().toLowerCase(),
      password,
    });

    storeTokens(data);

    const userData = data.user ?? (await API.get('/auth/me/')).data;
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    return userData;
  }, []);

  const register = useCallback(async (formData) => {
    const { data } = await API.post('/auth/register/', formData);
    storeTokens(data.tokens ?? data);
    const userData = data.user ?? (await API.get('/auth/me/')).data;
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
    return userData;
  }, []);

  const updateUser = useCallback((userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  }, []);

  const logout = useCallback(async () => {
    try {
      const tokens = getStoredTokens();
      if (tokens?.refresh) {
        await API.post('/auth/logout/', { refresh: tokens.refresh });
      }
    } catch {
      // ignore
    } finally {
      clearSession();
      setUser(null);
    }
  }, []);

  const isCandidat = user?.role === 'CANDIDAT';
  const isResponsable = user?.role === 'RESPONSABLE';
  const isAdmin = user?.role === 'ADMIN';
  const isStaff = isResponsable || isAdmin;

  return (
    <AuthContext.Provider value={{
      user, loading, login, register, logout, updateUser,
      isCandidat, isResponsable, isAdmin, isStaff,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
