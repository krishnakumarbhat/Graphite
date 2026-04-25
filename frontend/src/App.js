import { Navigate, Route, Routes, BrowserRouter } from 'react-router-dom';

import { AppWorkspaceShell } from '@/components/workspace/app-workspace-shell';
import { DashboardPage } from '@/components/workspace/dashboard-page';
import { NotesPage } from '@/components/workspace/notes-page';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppWorkspaceShell />} path="/">
          <Route element={<DashboardPage />} index />
          <Route element={<NotesPage />} path="notes" />
        </Route>
        <Route element={<Navigate replace to="/" />} path="*" />
      </Routes>
    </BrowserRouter>
  );
}
