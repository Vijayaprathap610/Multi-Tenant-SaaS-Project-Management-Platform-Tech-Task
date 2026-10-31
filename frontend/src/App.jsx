import { Navigate, Route, Routes } from "react-router";
import { AppLayout, ProtectedRoute } from "./components/layouts";
import { AcceptInvite, ForgotPassword, Login, Register, ResetPassword } from "./pages/auth";
import BillingPage from "./pages/BillingPage";
import Dashboard from "./pages/Dashboard";
import Landing from "./pages/Landing";
import NotFound from "./pages/NotFound";
import NotificationsPage from "./pages/NotificationsPage";
import Onboarding from "./pages/Onboarding";
import { PlatformAdminDashboard, PlatformAdminLogin } from "./pages/platformAdmin";
import ProfilePage from "./pages/ProfilePage";
import ProjectLayout from "./pages/project/ProjectLayout";
import BoardPage from "./pages/project/BoardPage";
import IssuesPage from "./pages/project/IssuesPage";
import IssueDetailPage from "./pages/project/IssueDetailPage";
import SprintsPage from "./pages/project/SprintsPage";
import WorkflowPage from "./pages/project/WorkflowPage";
import ProjectMembersPage from "./pages/project/ProjectMembersPage";
import ReportsPage from "./pages/project/ReportsPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/accept-invite" element={<AcceptInvite />} />
      <Route path="/platform-admin/login" element={<PlatformAdminLogin />} />
      <Route path="/platform-admin" element={<PlatformAdminDashboard />} />
      <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
      <Route path="/app" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="projects/:projectId" element={<ProjectLayout />}>
          <Route index element={<Navigate to="board" replace />} />
          <Route path="board" element={<BoardPage />} />
          <Route path="issues" element={<IssuesPage />} />
          <Route path="issues/:issueId" element={<IssueDetailPage />} />
          <Route path="sprints" element={<SprintsPage />} />
          <Route path="workflow" element={<WorkflowPage />} />
          <Route path="members" element={<ProjectMembersPage />} />
          <Route path="reports" element={<ReportsPage />} />
        </Route>
        <Route path="settings" element={<SettingsPage />} />
        <Route path="billing" element={<BillingPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="*" element={<NotFound inApp />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
