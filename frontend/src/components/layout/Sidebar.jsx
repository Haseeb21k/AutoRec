import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Database, FileText, Users, LayoutDashboard, LogOut } from 'lucide-react';
import { useAuth } from '@/features/auth/AuthContext';

export default function Sidebar() {
    const location = useLocation();
    const { user, logout } = useAuth();
    const isActive = (path) => location.pathname === path;

    const navClass = (path) => `
    w-full flex items-center p-3 rounded-lg transition-colors mb-1
    ${isActive(path) ? 'bg-indigo-700 text-white' : 'text-indigo-200 hover:bg-indigo-800'}
  `;

    return (
        <div className="w-64 bg-indigo-900 text-white flex flex-col h-screen fixed left-0 top-0 border-r border-indigo-800">
            {/* Logo Area */}
            <div className="p-6 border-b border-indigo-800">
                <div className="flex items-center gap-2 font-bold text-xl tracking-tight">
                    <Database className="h-6 w-6 text-indigo-400" />
                    <span>AutoRec</span>
                </div>
                <div className="text-xs text-indigo-400 mt-1 uppercase tracking-wider font-semibold">
                    Enterprise Edition
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 p-4">
                <Link to="/" className={navClass('/')}>
                    <LayoutDashboard className="w-5 h-5 mr-3" />
                    Reconciliation
                </Link>

                <Link to="/reconcile" className={navClass('/reconcile')}>
                    <FileText className="w-5 h-5 mr-3" />
                    Statements
                </Link>

                {/* CHECK ROLE HERE: Only show if superuser */}
                {user?.role === 'superuser' && (
                    <Link to="/users" className={navClass('/users')}>
                        <Users className="w-5 h-5 mr-3" />
                        User Management
                    </Link>
                )}
            </nav>

            {/* User Profile */}
            <div className="p-4 border-t border-indigo-800 bg-indigo-950">
                <div className="flex items-center mb-3">
                    <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-xs font-bold border-2 border-indigo-300">
                        {user?.email?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <div className="ml-3">
                        <div className="text-sm font-medium text-white truncate w-32">{user?.email || 'User'}</div>
                        <div className="text-xs text-indigo-300 capitalize">{user?.role || 'Viewer'}</div>
                    </div>
                </div>

                <button
                    onClick={logout}
                    className="flex items-center text-xs text-red-300 hover:text-red-200 w-full mt-2"
                >
                    <LogOut className="w-3 h-3 mr-2" /> Sign Out
                </button>
            </div>
        </div>
    );
}