import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Lock, CheckCircle, AlertCircle, Sun, Moon, ArrowRight } from 'lucide-react';
import apiClient from '@/api/client';

export default function SetPasswordPage() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const token = searchParams.get('token');

    const [password, setPassword] = useState('');
    const [confirm, setConfirm] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [darkMode, setDarkMode] = useState(localStorage.getItem('theme') === 'dark');

    useEffect(() => {
        if (darkMode) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    }, [darkMode]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (password !== confirm) {
            setError("Passwords do not match");
            return;
        }

        setLoading(true);
        try {
            await apiClient.post('/users/setup-password', { token, password });
            alert("Password set! You can now login.");
            navigate('/login');
        } catch (err) {
            setError("Invalid or expired token.");
        } finally {
            setLoading(false);
        }
    };

    if (!token) return <div className="p-10 text-center text-red-500">Invalid Link</div>;

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 transition-colors duration-300">
            {/* Theme Toggle */}
            <div className="fixed top-6 right-6">
                <button
                    onClick={() => setDarkMode(!darkMode)}
                    className="p-2.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
                >
                    {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>
            </div>
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <h2 className="text-center text-3xl font-extrabold text-slate-900 dark:text-white">
                    Set Your Password
                </h2>
                <p className="mt-2 text-center text-sm text-slate-500 dark:text-slate-400">
                    Welcome to AutoRec. Please secure your account.
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white dark:bg-slate-900 py-8 px-4 shadow-xl sm:rounded-2xl sm:px-10 border border-slate-200 dark:border-slate-800">
                    <form className="space-y-6" onSubmit={handleSubmit}>
                        {error && (
                            <div className="bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/30 text-red-600 dark:text-red-400 px-4 py-3 rounded-xl text-sm flex items-center font-medium">
                                <AlertCircle className="w-4 h-4 mr-2" /> {error}
                            </div>
                        )}
                        <div>
                            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300">New Password</label>
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className="mt-1 block w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm outline-none focus:ring-2 focus:ring-primary-500 text-slate-900 dark:text-white transition-all"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300">Confirm Password</label>
                            <input
                                type="password"
                                required
                                value={confirm}
                                onChange={(e) => setConfirm(e.target.value)}
                                placeholder="••••••••"
                                className="mt-1 block w-full px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-sm outline-none focus:ring-2 focus:ring-primary-500 text-slate-900 dark:text-white transition-all"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-white bg-primary-600 hover:bg-primary-700 transition-all disabled:bg-slate-400 dark:disabled:bg-slate-800"
                        >
                            {loading ? 'Saving...' : 'Set Password & Login'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
