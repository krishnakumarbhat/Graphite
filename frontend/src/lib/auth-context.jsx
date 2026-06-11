import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from './supabase';

const AuthContext = createContext(null);
const authUnavailable = { error: { message: 'Supabase auth is not configured.' } };

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined); // undefined = loading

  useEffect(() => {
    if (!supabase) {
      setUser(null);
      return;
    }
    supabase.auth.getSession().then(({ data }) => {
      setUser(data.session?.user ?? null);
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });
    return () => subscription.unsubscribe();
  }, []);

  const login = (email, password) => {
    if (!supabase) {
      return Promise.resolve(authUnavailable);
    }
    return supabase.auth.signInWithPassword({ email, password });
  };

  const signup = (email, password) => {
    if (!supabase) {
      return Promise.resolve(authUnavailable);
    }
    return supabase.auth.signUp({ email, password });
  };

  const logout = () => {
    if (!supabase) {
      return Promise.resolve();
    }
    return supabase.auth.signOut();
  };

  const loginWithGoogle = () => {
    if (!supabase) {
      return Promise.resolve(authUnavailable);
    }
    return supabase.auth.signInWithOAuth({ provider: 'google' });
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loginWithGoogle }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
