import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, CheckCircle2, DollarSign, Activity, Loader2, Play, Zap, Maximize2, X, Filter, Database, Save, Trash2 } from 'lucide-react';
import apiClient from '@/api/client';
import { useAuth } from '@/features/auth/AuthContext';

// --- RENDER HELPERS ---
const FeedTable = ({ matches, limit }) => (
    <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b">
                <tr>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Bank Statement</th>
                    <th className="px-4 py-3 text-center">Match</th>
                    <th className="px-4 py-3">Internal Ledger</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                </tr>
            </thead>
            <tbody>
                {matches.length === 0 ? (
                    <tr>
                        <td colSpan="5" className="px-4 py-8 text-center text-gray-500 italic">
                            No matches found matching filters.
                        </td>
                    </tr>
                ) : (
                    matches.slice(0, limit || 100).map((match) => {
                        let badgeColor = '';
                        let badgeText = '';

                        if (match.match_type === 'exact') {
                            badgeColor = 'bg-green-100 text-green-800';
                            badgeText = 'Exact';
                        } else if (match.match_type === 'fuzzy_date' || match.match_type === 'fuzzy_desc') {
                            badgeColor = 'bg-yellow-100 text-yellow-800';
                            badgeText = 'Fuzzy';
                        } else if (match.match_type === 'mismatch') {
                            badgeColor = 'bg-red-100 text-red-800';
                            badgeText = 'No Match';
                        }

                        return (
                            <tr key={match.id} className="border-b last:border-0 hover:bg-gray-50 transition-colors">
                                <td className="px-4 py-3 whitespace-nowrap text-gray-500">{match.date}</td>
                                <td className="px-4 py-3 font-medium text-gray-800 truncate max-w-[150px]" title={match.bank_desc}>
                                    {match.bank_desc}
                                </td>
                                <td className="px-4 py-3 text-center">
                                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${badgeColor}`}>
                                        {badgeText}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-gray-600 truncate max-w-[150px]" title={match.ledger_desc}>
                                    {match.ledger_desc === '-' ? <span className="text-gray-400 italic">N/A</span> : match.ledger_desc}
                                </td>
                                <td className="px-4 py-3 text-right font-bold text-gray-900">
                                    ${Math.abs(match.amount).toLocaleString()}
                                </td>
                            </tr>
                        );
                    })
                )}
            </tbody>
        </table>
    </div>
);

export default function DashboardPage() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [running, setRunning] = useState(false);
    const [stats, setStats] = useState({
        total_transactions: 0,
        total_matches: 0,
        reconciliation_rate: 0
    });
    const [recentMatches, setRecentMatches] = useState([]);

    // UI State
    const [isExpanded, setIsExpanded] = useState(false);
    const [filters, setFilters] = useState({
        exact: true,
        fuzzy: true,
        mismatch: true
    });

    // Custom Success Modal State
    const [showSuccessModal, setShowSuccessModal] = useState(false);
    const [runResults, setRunResults] = useState(null);

    // Save Report State
    const [showSaveModal, setShowSaveModal] = useState(false);
    const [reportName, setReportName] = useState('');
    const [savingReport, setSavingReport] = useState(false);

    // Clear State
    const [showClearModal, setShowClearModal] = useState(false);
    const [clearing, setClearing] = useState(false);

    const handleClearData = async () => {
        setClearing(true);
        try {
            await apiClient.delete('/reconcile/clear');
            setShowClearModal(false);
            loadData();
        } catch (err) {
            console.error("Clear failed", err);
        } finally {
            setClearing(false);
        }
    };

    const handleSaveReport = async () => {
        if (!reportName.trim()) return;
        setSavingReport(true);
        try {
            await apiClient.post('/reconcile/save', { name: reportName });
            setShowSaveModal(false);
            setReportName('');
            navigate('/reports');
        } catch (err) {
            console.error("Save failed", err);
            alert("Failed to save report.");
        } finally {
            setSavingReport(false);
        }
    };

    const loadData = async () => {
        try {
            const [statsRes, activityRes] = await Promise.all([
                apiClient.get('/reconcile/stats'),
                apiClient.get('/reconcile/activity?limit=1000') // Fetch more history to keep feed populated
            ]);
            setStats(statsRes.data);
            setRecentMatches(activityRes.data);
        } catch (error) {
            console.error("Failed to fetch dashboard data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    // --- WEBSOCKET CONNECTION ---
    useEffect(() => {
        // Use VITE_API_URL for production if provided, otherwise default to current host
        const apiUrl = import.meta.env.VITE_API_URL || "";
        let wsUrl;
        
        if (apiUrl) {
            // Construct WS URL from the API URL (replace http with ws)
            wsUrl = apiUrl.replace(/^http/, 'ws') + '/api/v1/reconcile/ws';
        } else {
            const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            const host = window.location.host; 
            wsUrl = `${protocol}//${host}/api/v1/reconcile/ws`;
        }
        // Check if websockets available (simple check)
        let ws;
        try {
            ws = new WebSocket(wsUrl);
            ws.onopen = () => console.log("Connected to Real-Time Reconciliation Feed");
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    // Handle completion event from backend
                    if (data.type === 'complete') {
                        // Clear fallback polling if active
                        if (window._reconcilePollInterval) {
                            clearInterval(window._reconcilePollInterval);
                            window._reconcilePollInterval = null;
                        }
                        setRunning(false);
                        loadData(); // Refresh final stats
                        return;
                    }

                    // Handle system clear event
                    if (data.type === 'clear') {
                        loadData(); // This will fetch empty stats/activity
                        return;
                    }

                    // Handle error event from backend
                    if (data.type === 'error') {
                        setRunning(false);
                        console.error('Reconciliation error:', data.message);
                        return;
                    }

                    // Normal match object
                    setRecentMatches(prev => [data, ...prev]);

                    if (data.match_type !== 'mismatch') {
                        setStats(prev => ({
                            ...prev,
                            total_matches: prev.total_matches + 1,
                            reconciliation_rate: prev.total_transactions > 0
                                ? (((prev.total_matches + 1) / prev.total_transactions) * 100).toFixed(1)
                                : 0
                        }));
                    }
                } catch (e) {
                    console.error("Error parsing WS message", e);
                }
            };
        } catch (e) {
            console.error("WS Create failed", e);
        }

        return () => {
            if (ws) ws.close();
        };
    }, []); // WebSocket connection — no dependencies needed
    // Actually, dependency on isExpanded in setState callback is fine without re-running effect.
    // BUT we need to be careful not to reset connection constantly. removed isExpanded dependency.

    const handleRunReconciliation = async () => {
        setRunning(true);
        try {
            const res = await apiClient.post('/reconcile/run');
            if (res.data.status === "started") {
                console.log("Reconciliation started:", res.data.message);
                // Primary: WS 'complete' event sets running=false
                // Fallback: poll stats every 3s and stop after no change
                let lastMatchCount = stats.total_matches;
                let stableCount = 0;
                const pollInterval = setInterval(async () => {
                    try {
                        const [statsRes, activityRes] = await Promise.all([
                            apiClient.get('/reconcile/stats'),
                            apiClient.get('/reconcile/activity?limit=1000')
                        ]);
                        setStats(statsRes.data);
                        setRecentMatches(activityRes.data);

                        if (statsRes.data.total_matches === lastMatchCount) {
                            stableCount++;
                        } else {
                            stableCount = 0;
                            lastMatchCount = statsRes.data.total_matches;
                        }
                        // If no change for 2 polls (6s), assume done
                        if (stableCount >= 2) {
                            clearInterval(pollInterval);
                            setRunning(false);
                        }
                    } catch (e) { /* ignore poll errors */ }
                }, 3000);
                // Store interval ID so WS complete handler can clear it
                window._reconcilePollInterval = pollInterval;
            }
        } catch (err) {
            console.error(err);
            alert("Failed to start reconciliation. Check console for details.");
            setRunning(false);
        }
    };

    const unmatched = stats.total_transactions - stats.total_matches;

    // Filter Logic
    const filteredMatches = recentMatches.filter(m => {
        if (m.match_type === 'exact' && !filters.exact) return false;
        if (m.match_type === 'fuzzy_date' && !filters.fuzzy) return false;
        if (m.match_type === 'mismatch' && !filters.mismatch) return false;
        return true;
    });

    const statCards = [
        {
            label: 'Reconciliation Rate',
            value: `${stats.reconciliation_rate}%`,
            icon: Activity,
            color: 'text-blue-600',
            bg: 'bg-blue-100'
        },
        {
            label: 'Unmatched Items',
            value: unmatched.toLocaleString(),
            icon: AlertTriangle,
            color: 'text-orange-600',
            bg: 'bg-orange-100'
        },
        {
            label: 'Fully Reconciled',
            value: stats.total_matches.toLocaleString(),
            icon: CheckCircle2,
            color: 'text-green-600',
            bg: 'bg-green-100'
        },
        {
            label: 'Total Volume',
            value: stats.total_transactions.toLocaleString(),
            icon: DollarSign,
            color: 'text-purple-600',
            bg: 'bg-purple-100'
        },
    ];

    if (loading) {
        return <div className="flex h-96 items-center justify-center"><Loader2 className="animate-spin text-indigo-600" /></div>;
    }

    return (
        <div className="space-y-8 relative">
            {/* Modal Overlay for Expanded View */}
            {isExpanded && (
                <div className="fixed inset-0 z-50 bg-white flex flex-col animate-in fade-in zoom-in duration-200">
                    <div className="px-8 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50 shadow-sm">
                        <div className="flex items-center gap-4">
                            <h2 className="text-xl font-bold text-gray-900 flex items-center">
                                <Zap className="w-5 h-5 text-yellow-500 mr-2" />
                                Live Reconciliation Feed
                            </h2>
                            <div className="flex items-center bg-white border border-gray-300 rounded-lg p-1">
                                <label className="flex items-center px-3 py-1 cursor-pointer hover:bg-gray-50 rounded select-none">
                                    <input
                                        type="checkbox"
                                        checked={filters.exact}
                                        onChange={e => setFilters(prev => ({ ...prev, exact: e.target.checked }))}
                                        className="rounded text-indigo-600 focus:ring-indigo-500 mr-2"
                                    />
                                    <span className="text-sm text-gray-700">Exact Matches</span>
                                </label>
                                <div className="w-px h-4 bg-gray-300 mx-1"></div>
                                <label className="flex items-center px-3 py-1 cursor-pointer hover:bg-gray-50 rounded select-none">
                                    <input
                                        type="checkbox"
                                        checked={filters.fuzzy}
                                        onChange={e => setFilters(prev => ({ ...prev, fuzzy: e.target.checked }))}
                                        className="rounded text-indigo-600 focus:ring-indigo-500 mr-2"
                                    />
                                    <span className="text-sm text-gray-700">Fuzzy Matches</span>
                                </label>
                                <div className="w-px h-4 bg-gray-300 mx-1"></div>
                                <label className="flex items-center px-3 py-1 cursor-pointer hover:bg-gray-50 rounded select-none">
                                    <input
                                        type="checkbox"
                                        checked={filters.mismatch}
                                        onChange={e => setFilters(prev => ({ ...prev, mismatch: e.target.checked }))}
                                        className="rounded text-red-600 focus:ring-red-500 mr-2"
                                    />
                                    <span className="text-sm text-gray-700">Mismatches</span>
                                </label>
                            </div>
                        </div>
                        <button
                            onClick={() => setIsExpanded(false)}
                            className="p-2 hover:bg-gray-200 rounded-full transition-colors"
                        >
                            <X className="w-6 h-6 text-gray-500" />
                        </button>
                    </div>
                    <div className="flex-1 overflow-auto p-8 bg-gray-50/50">
                        <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
                            <FeedTable matches={filteredMatches} limit={filteredMatches.length} />
                        </div>
                    </div>
                </div>
            )}

            {/* Reconciliation Success Modal */}
            {showSuccessModal && runResults && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
                        <div className="text-center mb-6">
                            <div className="mx-auto bg-green-100 p-4 rounded-full w-16 h-16 flex items-center justify-center mb-4">
                                <CheckCircle2 className="w-8 h-8 text-green-600" />
                            </div>
                            <h3 className="text-2xl font-bold text-gray-900">Reconciliation Complete</h3>
                            <p className="text-gray-500 text-sm mt-1">
                                Engine has processed all pending transactions.
                            </p>
                        </div>

                        <div className="bg-gray-50 rounded-lg p-4 space-y-3 mb-6 border border-gray-100">
                            <div className="flex justify-between items-center text-sm">
                                <span className="text-gray-600">Items Scanned</span>
                                <span className="font-bold text-gray-900">{runResults.bank_items_scanned}</span>
                            </div>
                            <div className="h-px bg-gray-200"></div>
                            <div className="flex justify-between items-center text-sm text-green-700">
                                <span className="flex items-center"><Zap className="w-3 h-3 mr-1" /> Exact Matches</span>
                                <span className="font-bold">{runResults.exact_matches}</span>
                            </div>
                            <div className="flex justify-between items-center text-sm text-yellow-700">
                                <span className="flex items-center"><Activity className="w-3 h-3 mr-1" /> Fuzzy Matches</span>
                                <span className="font-bold">{runResults.fuzzy_matches}</span>
                            </div>
                        </div>

                        <button
                            onClick={() => setShowSuccessModal(false)}
                            className="w-full py-3 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 transition-colors shadow-md"
                        >
                            View Results
                        </button>
                    </div>
                </div>
            )
            }

            {/* Save Report Modal */}
            {showSaveModal && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 animate-in fade-in slide-in-from-bottom-4 duration-300">
                        <div className="text-center mb-6">
                            <div className="mx-auto bg-indigo-100 p-4 rounded-full w-16 h-16 flex items-center justify-center mb-4 text-indigo-600">
                                <Save className="w-8 h-8" />
                            </div>
                            <h3 className="text-2xl font-bold text-gray-900">Finalize Reconciliation</h3>
                            <p className="text-gray-500 text-sm mt-1">
                                Give this reconciliation run a name to save it to your history.
                            </p>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase mb-1 ml-1">Report Name</label>
                                <input 
                                    autoFocus
                                    type="text" 
                                    value={reportName}
                                    onChange={e => setReportName(e.target.value)}
                                    placeholder="e.g., Monthly Close - April 2026"
                                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none transition-all font-medium"
                                />
                            </div>
                            
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setShowSaveModal(false)}
                                    className="flex-1 py-3 bg-gray-100 text-gray-600 rounded-xl font-bold hover:bg-gray-200 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSaveReport}
                                    disabled={savingReport || !reportName.trim()}
                                    className="flex-[2] py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-colors shadow-lg disabled:opacity-50"
                                >
                                    {savingReport ? 'Saving...' : 'Confirm & Save'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Clear Data Confirmation Modal */}
            {showClearModal && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 animate-in fade-in scale-in duration-200">
                        <div className="text-center mb-6">
                            <div className="mx-auto bg-red-100 p-4 rounded-full w-16 h-16 flex items-center justify-center mb-4 text-red-600">
                                <Trash2 className="w-8 h-8" />
                            </div>
                            <h3 className="text-2xl font-bold text-gray-900">Clear Active Data?</h3>
                            <p className="text-gray-500 text-sm mt-1">
                                This will remove all currently unmatched items and pending results.
                                <span className="block mt-2 font-bold text-red-600">Saved reports will NOT be affected.</span>
                            </p>
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowClearModal(false)}
                                className="flex-1 py-3 bg-gray-100 text-gray-600 rounded-xl font-bold hover:bg-gray-200 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleClearData}
                                disabled={clearing}
                                className="flex-1 py-3 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 transition-colors shadow-lg disabled:opacity-50"
                            >
                                {clearing ? 'Clearing...' : 'Yes, Clear'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Executive Reconciliation Overview</h1>
                    <p className="text-gray-500 text-sm mt-1">Live financial health status</p>
                </div>

                {user?.role === 'superuser' && (
                    <div className="flex gap-3">
                        {/* Save Button: only if there are active matches (no report_id) */}
                        {recentMatches.length > 0 && recentMatches.some(m => !m.report_id) && !running && (
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setShowClearModal(true)}
                                    className="flex items-center px-4 py-3 bg-red-50 text-red-600 border border-red-200 rounded-xl font-medium hover:bg-red-100 transition-colors"
                                >
                                    <Trash2 className="w-4 h-4 mr-2" />
                                    Clear Active
                                </button>
                                
                                <button
                                    onClick={() => setShowSaveModal(true)}
                                    className="flex items-center px-6 py-3 bg-white border-2 border-indigo-600 text-indigo-600 rounded-xl font-bold shadow-sm hover:bg-indigo-50 transition-all"
                                >
                                    <Database className="w-5 h-5 mr-2" />
                                    Save as Report
                                </button>
                            </div>
                        )}

                        <button
                            onClick={handleRunReconciliation}
                            disabled={running}
                            className="flex items-center px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium shadow-md hover:bg-indigo-700 hover:shadow-lg transition-all disabled:bg-indigo-400 disabled:shadow-none"
                        >
                            {running ? (
                                <>
                                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <Play className="w-5 h-5 mr-2 fill-current" />
                                    Run Reconciliation Engine
                                </>
                            )}
                        </button>
                    </div>
                )}
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {statCards.map((stat, index) => (
                    <div key={index} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex items-center hover:shadow-md transition-shadow">
                        <div className={`p-3 rounded-lg ${stat.bg} mr-4`}>
                            <stat.icon className={`w-6 h-6 ${stat.color}`} />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-gray-500">{stat.label}</p>
                            <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                        </div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                {/* Live Reconciliation Feed */}
                <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col h-full">
                    <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                        <h3 className="font-bold text-gray-800 flex items-center">
                            <Zap className="w-4 h-4 text-yellow-500 mr-2" />
                            Live Reconciliation Feed
                        </h3>
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-medium text-gray-500 bg-white px-2 py-1 rounded border border-gray-200 shadow-sm">
                                {isExpanded ? 'Full History' : 'Recent Matches'}
                            </span>
                            <button
                                onClick={() => setIsExpanded(true)}
                                className="p-1 hover:bg-gray-200 rounded transition-colors text-gray-500"
                                title="Expand View"
                            >
                                <Maximize2 className="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    <FeedTable matches={filteredMatches} limit={10} />
                </div>

                {/* Right Column: Alerts / Actions */}
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <h3 className="font-bold text-gray-800 mb-4">System Health</h3>
                    <div className="space-y-4">
                        <div className="flex items-center p-3 bg-green-50 text-green-700 rounded-lg text-sm">
                            <CheckCircle2 className="w-5 h-5 mr-3" />
                            <div>
                                <span className="font-bold">System Operational</span>
                                <p className="text-xs opacity-80">Database connected</p>
                            </div>
                        </div>

                        {unmatched > 0 && (
                            <div className="flex items-center p-3 bg-orange-50 text-orange-700 rounded-lg text-sm">
                                <AlertTriangle className="w-5 h-5 mr-3" />
                                <div>
                                    <span className="font-bold">{unmatched} Unmatched Items</span>
                                    <p className="text-xs opacity-80">Action required</p>
                                </div>
                            </div>
                        )}

                        <div className="mt-4 pt-4 border-t border-gray-100">
                            <p className="text-xs text-gray-400 uppercase font-bold mb-2">Last Run</p>
                            <p className="text-sm text-gray-600">Just now</p>
                        </div>
                    </div>
                </div>
            </div>
        </div >
    );
}