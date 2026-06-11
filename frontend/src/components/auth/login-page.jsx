import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../lib/auth-context';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';

export default function LoginPage() {
  const { login, signup, user } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);
    try {
      const fn = mode === 'login' ? login : signup;
      const { error: err } = await fn(email, password);
      if (err) {
        setError(err.message);
      } else if (mode === 'signup') {
        setSuccessMsg('Check your email for a confirmation link.');
      }
    } catch (ex) {
      setError(ex.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  if (user) {
    return <Navigate replace to="/notes" />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-sm shadow-lg">
        <CardHeader className="space-y-1 text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold text-sm">G</div>
            <span className="font-semibold text-lg">Graphite</span>
          </div>
          <CardTitle className="text-xl">
            {mode === 'login' ? 'Welcome back' : 'Create account'}
          </CardTitle>
          <CardDescription>
            {mode === 'login'
              ? 'Sign in for unlimited notes & features'
              : 'Get unlimited notes and AI features'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
            </div>

            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
            {successMsg && (
              <p className="text-sm text-green-600 dark:text-green-400">{successMsg}</p>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
          </form>

          <div className="mt-4 text-center text-sm text-muted-foreground">
            {mode === 'login' ? (
              <>Don't have an account?{' '}
                <button onClick={() => setMode('signup')} className="text-primary underline underline-offset-4" type="button">
                  Sign up
                </button>
              </>
            ) : (
              <>Already have an account?{' '}
                <button onClick={() => setMode('login')} className="text-primary underline underline-offset-4" type="button">
                  Sign in
                </button>
              </>
            )}
          </div>

          <div className="mt-3 text-center text-xs text-muted-foreground">
            <a href="/" className="text-primary underline underline-offset-4">Continue as guest (5 notes max)</a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
