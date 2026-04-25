import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Database, FileText, Users, LayoutDashboard, LogOut, Sun, Moon } from 'lucide-react';
import { useAuth } from '@/features/auth/AuthContext';

export default function Sidebar() {
    const location = useLocation();
    const { user, logout } = useAuth();
    const isActive = (path) => location.pathname === path;
    
    const [isDark, setIsDark] = React.useState(() => {
        return localStorage.getItem('theme') === 'dark' || 
               (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
    });

    React.useEffect(() => {
        if (isDark) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    }, [isDark]);

    const navClass = (path) => `
    w-full flex items-center p-3 rounded-lg transition-colors mb-1
    ${isActive(path) 
        ? 'bg-primary-600 text-white shadow-lg' 
        : 'text-primary-50 hover:bg-primary-800 hover:text-white dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'}
  `;

    return (
        <div className="w-64 bg-primary-700 text-white flex flex-col h-screen fixed left-0 top-0 border-r border-primary-800 dark:bg-slate-950 dark:border-slate-900">
            {/* Logo Area */}
            <div className="p-6 border-b border-primary-800/50">
                <div className="flex items-center gap-2 font-bold text-xl tracking-tight text-white">
                    <Database className="h-6 w-6 text-primary-300" />
                    <span>AutoRec</span>
                </div>
                <div className="text-[10px] text-primary-50 mt-1 uppercase tracking-[0.2em] font-black">
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
                    Upload Statements
                </Link>

                <Link to="/reports" className={navClass('/reports')}>
                    <Database className="w-5 h-5 mr-3" />
                    Saved Reports
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
            <div className="p-4 border-t border-primary-700 bg-primary-700 dark:bg-slate-900 dark:border-slate-800">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center">
                        <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center text-xs font-bold border-2 border-primary-300">
                            {user?.email?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <div className="ml-3">
                            <div className="text-sm font-medium text-white truncate w-24">{user?.email || 'User'}</div>
                            <div className="text-xs text-primary-50 capitalize opacity-70">{user?.role || 'Viewer'}</div>
                        </div>
                    </div>
                    <button 
                        onClick={() => setIsDark(!isDark)}
                        className="p-1.5 rounded-lg bg-primary-800 text-primary-100 hover:bg-primary-900 transition-colors dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700"
                    >
                        {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                    </button>
                </div>

                <button
                    onClick={logout}
                    className="flex items-center text-xs text-red-300 hover:text-red-200 w-full px-1"
                >
                    <LogOut className="w-3 h-3 mr-2" /> Sign Out
                </button>
            </div>
        </div>
    );
}
