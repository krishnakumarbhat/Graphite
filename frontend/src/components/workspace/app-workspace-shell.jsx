import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Toaster } from '@/components/ui/sonner';
import '@/App.css';
import { Database, FileText, LayoutDashboard, Moon, Sparkles, SunMedium } from 'lucide-react';
import { NavLink, Outlet, useLocation, useOutletContext } from 'react-router-dom';
import { useTheme } from 'next-themes';

import { fetchHealth } from '@/lib/api';

const NAV_ITEMS = [
  {
    to: '/',
    label: 'Workspace',
    description: 'Agents, workflows, memory, and system status.',
    icon: LayoutDashboard,
  },
  {
    to: '/notes',
    label: 'Notes',
    description: 'SQLite-backed pages, markdown import, and AI drafting.',
    icon: FileText,
  },
];

const renderNavItem = ({ to, label, description, icon: Icon }) => (
  <NavLink
    key={to}
    className={({ isActive }) =>
      [
        'workspace-nav-link rounded-2xl border px-4 py-3 transition-colors',
        isActive
          ? 'border-primary/30 bg-primary/10 text-foreground shadow-sm'
          : 'border-border/70 bg-background/65 text-muted-foreground hover:bg-secondary/70',
      ].join(' ')
    }
    end={to === '/'}
    to={to}
  >
    <div className="flex items-center gap-3">
      <div className="rounded-xl bg-secondary/80 p-2 text-foreground">
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <p className="font-medium text-sm text-foreground">{label}</p>
        <p className="text-xs leading-5 text-muted-foreground">{description}</p>
      </div>
    </div>
  </NavLink>
);

export const useWorkspaceShell = () => useOutletContext();

export function AppWorkspaceShell() {
  const location = useLocation();
  const { resolvedTheme, setTheme } = useTheme();
  const [backendHealth, setBackendHealth] = useState(null);

  useEffect(() => {
    let cancelled = false;

    fetchHealth()
      .then((payload) => {
        if (!cancelled) {
          setBackendHealth(payload);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setBackendHealth({ status: 'unreachable' });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const handleToggleTheme = () => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');

  return (
    <div className="preview-shell min-h-screen overflow-hidden">
      <div className="mx-auto flex min-h-screen w-full max-w-[1600px] gap-4 px-3 py-4 sm:px-4 lg:px-6">
        <aside className="workspace-sidebar hidden w-[304px] shrink-0 flex-col justify-between rounded-[30px] border border-border/80 bg-background/85 p-5 shadow-[var(--shadow-soft)] backdrop-blur-xl lg:flex">
          <div className="space-y-5">
            <div className="space-y-3">
              <Badge className="bg-primary/12 text-primary hover:bg-primary/12">
                Graphite System
              </Badge>
              <div>
                <p className="font-display text-2xl font-semibold tracking-tight text-foreground">
                  Local-first agent workspace
                </p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Routed web shell for the agent dashboard and the new `/notes` workspace.
                </p>
              </div>
            </div>

            <nav className="space-y-3">{NAV_ITEMS.map(renderNavItem)}</nav>

            <Card className="rounded-[24px] border-border/80 bg-card/90 shadow-none">
              <CardContent className="space-y-4 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
                      Environment
                    </p>
                    <p className="text-sm text-muted-foreground">Backend and local note storage</p>
                  </div>
                  <Button className="rounded-xl" onClick={handleToggleTheme} size="icon" variant="outline">
                    {resolvedTheme === 'dark' ? <SunMedium className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                  </Button>
                </div>

                <div className="space-y-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">API</span>
                    <Badge variant={backendHealth?.status === 'ok' ? 'default' : 'secondary'}>
                      {backendHealth?.status === 'ok' ? 'Connected' : 'Offline'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Gemini</span>
                    <Badge variant={backendHealth?.geminiConfigured ? 'default' : 'secondary'}>
                      {backendHealth?.geminiConfigured ? 'Configured' : 'Missing key'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">Supabase</span>
                    <Badge variant={backendHealth?.supabaseConfigured ? 'default' : 'secondary'}>
                      {backendHealth?.supabaseConfigured ? 'Mirroring' : 'Local only'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-muted-foreground">SQLite</span>
                    <Badge className="bg-secondary text-secondary-foreground">
                      Ready
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="rounded-[24px] border-border/80 bg-card/92 shadow-none">
            <CardContent className="space-y-3 p-4">
              <div className="flex items-center gap-2 text-sm text-foreground">
                <Sparkles className="h-4 w-4 text-primary" />
                <span className="font-medium">Current route</span>
              </div>
              <p className="text-xs leading-6 text-muted-foreground">{location.pathname}</p>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Database className="h-3.5 w-3.5" />
                <span>{backendHealth?.notesDatabasePath || 'backend/data/graphite.sqlite3'}</span>
              </div>
            </CardContent>
          </Card>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col gap-4">
          <header className="flex items-center justify-between rounded-[24px] border border-border/80 bg-background/80 px-4 py-3 shadow-[var(--shadow-soft)] backdrop-blur-xl lg:hidden">
            <div>
              <p className="font-display text-lg font-semibold text-foreground">Graphite</p>
              <p className="text-xs text-muted-foreground">Workspace and notes</p>
            </div>
            <div className="flex items-center gap-2">
              {NAV_ITEMS.map(({ to, label }) => (
                <Button asChild className="rounded-xl" key={to} size="sm" variant="outline">
                  <NavLink end={to === '/'} to={to}>
                    {label}
                  </NavLink>
                </Button>
              ))}
            </div>
          </header>

          <Outlet
            context={{
              backendHealth,
              onToggleTheme: handleToggleTheme,
              resolvedTheme,
            }}
          />
        </div>
      </div>
      <Toaster closeButton richColors position="bottom-right" />
    </div>
  );
}