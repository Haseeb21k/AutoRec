import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/features/auth/AuthContext';
import LoginPage from '@/features/auth/LoginPage';
import SetPasswordPage from '@/features/auth/SetPasswordPage';
import Sidebar from '@/components/layout/Sidebar';
import ReconciliationPage from '@/features/reconciliation/ReconciliationPage';
import DashboardPage from '@/features/dashboard/DashboardPage';
import UserManagementPage from '@/features/users/UserManagementPage';

// --- Protected Route Wrapper ---
const PrivateRoute = ({ children, adminOnly = false }) => {
  const { user } = useAuth();

  if (!user) return <Navigate to="/login" />;

  if (adminOnly && user.role !== 'superuser') {
    return <div className="p-8 text-center text-gray-500">Access Denied: Admins Only</div>;
  }

  return (
    <div className="flex min-h-screen bg-gray-50 font-sans text-gray-900">
      <Sidebar />
      <main className="flex-1 ml-64 p-8 overflow-y-auto">
        {children}
      </main>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/setup-password" element={<SetPasswordPage />} />

          {/* Protected Routes */}
          <Route path="/" element={
            <PrivateRoute>
              <DashboardPage />
            </PrivateRoute>
          } />

          <Route path="/reconcile" element={
            <PrivateRoute>
              <ReconciliationPage />
            </PrivateRoute>
          } />

          {/* Admin Only Route */}
          <Route path="/users" element={
            <PrivateRoute adminOnly={true}>
              <UserManagementPage />
            </PrivateRoute>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}