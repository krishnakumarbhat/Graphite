import { Navigate, Route, Routes, BrowserRouter } from 'react-router-dom';

import { AppWorkspaceShell } from '@/components/workspace/app-workspace-shell';
import { DashboardPage } from '@/components/workspace/dashboard-page';
import { NotesPage } from '@/components/workspace/notes-page';
import ResearchPage from '@/components/workspace/research-page';
import LoginPage from '@/components/auth/login-page';
import { AuthProvider } from '@/lib/auth-context';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppWorkspaceShell />} path="/">
            <Route element={<DashboardPage />} index />
            <Route element={<NotesPage />} path="notes" />
            <Route element={<ResearchPage />} path="research" />
          </Route>
          <Route element={<LoginPage />} path="/login" />
          <Route element={<Navigate replace to="/" />} path="*" />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
