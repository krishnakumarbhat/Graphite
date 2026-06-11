import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Toaster } from '@/components/ui/sonner';
import '@/App.css';
import { BarChart2, FileText, LayoutDashboard, LogIn, LogOut, Moon, SunMedium } from 'lucide-react';
import { NavLink, Outlet, useOutletContext } from 'react-router-dom';
import { useTheme } from 'next-themes';

import { fetchHealth } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

const NAV_ITEMS = [
  { to: '/',         label: 'Workspace', icon: LayoutDashboard },
  { to: '/notes',    label: 'Notes',     icon: FileText },
  { to: '/research', label: 'Research',  icon: BarChart2 },
];

export const useWorkspaceShell = () => useOutletContext();

export function AppWorkspaceShell() {
  const { resolvedTheme, setTheme } = useTheme();
  const { user, logout } = useAuth();
  const [backendHealth, setBackendHealth] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetchHealth()
      .then((payload) => { if (!cancelled) setBackendHealth(payload); })
      .catch(() => { if (!cancelled) setBackendHealth({ status: 'unreachable' }); });
    return () => { cancelled = true; };
  }, []);

  const handleToggleTheme = () => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');

  return (
    <div className="preview-shell min-h-screen flex flex-col">
      {/* Top navigation bar */}
      <header className="sticky top-0 z-40 border-b border-border/80 bg-background/90 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-[1600px] items-center justify-between px-4 sm:px-6">
          {/* Brand */}
          <div className="flex items-center gap-2 shrink-0">
            <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center text-primary-foreground font-bold text-sm select-none">
              G
            </div>
            <span className="font-semibold text-base hidden sm:block">Graphite</span>
          </div>

          {/* Nav tabs */}
          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  [
                    'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-secondary text-foreground'
                      : 'text-muted-foreground hover:bg-secondary/60 hover:text-foreground',
                  ].join(' ')
                }
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </NavLink>
            ))}
          </nav>

          {/* Right actions */}
          <div className="flex items-center gap-2 shrink-0">
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={handleToggleTheme}>
              {resolvedTheme === 'dark'
                ? <SunMedium className="h-4 w-4" />
                : <Moon className="h-4 w-4" />}
            </Button>

            {user ? (
              <Button variant="ghost" size="sm" onClick={logout} className="text-muted-foreground text-xs gap-1">
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">{user.email?.split('@')[0]}</span>
              </Button>
            ) : (
              <Button variant="outline" size="sm" asChild className="text-xs gap-1">
                <NavLink to="/login">
                  <LogIn className="h-3.5 w-3.5" />
                  Sign in
                </NavLink>
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1 mx-auto w-full max-w-[1600px] px-3 py-4 sm:px-4 lg:px-6">
        <Outlet context={{ backendHealth, onToggleTheme: handleToggleTheme, resolvedTheme }} />
      </main>

      <Toaster closeButton richColors position="bottom-right" />
    </div>
  );
}
