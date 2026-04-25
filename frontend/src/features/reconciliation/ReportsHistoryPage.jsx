import React, { useEffect, useState } from 'react';
import { Database, Calendar, FileText, CheckCircle2, ChevronRight, ArrowLeft, Loader2, Search, Trash2, AlertTriangle } from 'lucide-react';
import apiClient from '@/api/client';

// Simple match table for the detail view
const ReportMatchTable = ({ matches }) => (
    <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
            <thead className="text-xs text-slate-500 dark:text-slate-400 uppercase bg-slate-50 dark:bg-slate-800/50 border-b dark:border-slate-700">
                <tr>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Bank Item</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Ledger Item</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                </tr>
            </thead>
            <tbody className="divide-y dark:divide-slate-800">
                {matches.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="px-4 py-3 whitespace-nowrap text-slate-500 dark:text-slate-400">{m.date}</td>
                        <td className="px-4 py-3 font-medium text-slate-800 dark:text-white">{m.bank_desc}</td>
                        <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                m.match_type === 'exact' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                                m.match_type === 'fuzzy_date' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                                'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                            }`}>
                                {m.match_type.replace('_', ' ')}
                            </span>
                        </td>
                        <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{m.ledger_desc}</td>
                        <td className="px-4 py-3 text-right font-bold text-slate-900 dark:text-white">${Math.abs(m.amount).toLocaleString()}</td>
                    </tr>
                ))}
            </tbody>
        </table>
    </div>
);

export default function ReportsHistoryPage() {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedReport, setSelectedReport] = useState(null);
    const [reportDetails, setReportDetails] = useState(null);
    const [loadingDetails, setLoadingDetails] = useState(false);
    
    // Delete state
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [reportToDelete, setReportToDelete] = useState(null);
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        fetchReports();
    }, []);

    const fetchReports = async () => {
        setLoading(true);
        try {
            const res = await apiClient.get('/reconcile/reports');
            setReports(res.data);
        } catch (err) {
            console.error("Failed to fetch reports", err);
        } finally {
            setLoading(false);
        }
    };

    const handleViewDetails = async (report) => {
        setSelectedReport(report);
        setLoadingDetails(true);
        try {
            const res = await apiClient.get(`/reconcile/reports/${report.id}`);
            setReportDetails(res.data);
        } catch (err) {
            console.error("Failed to fetch report details", err);
        } finally {
            setLoadingDetails(false);
        }
    };

    const handleDeleteClick = (e, report) => {
        e.stopPropagation(); // Don't trigger "view details"
        setReportToDelete(report);
        setShowDeleteModal(true);
    };

    const confirmDelete = async () => {
        if (!reportToDelete) return;
        setDeleting(true);
        try {
            await apiClient.delete(`/reconcile/reports/${reportToDelete.id}`);
            setShowDeleteModal(false);
            setReportToDelete(null);
            fetchReports(); // Refresh list
        } catch (err) {
            alert("Failed to delete report.");
        } finally {
            setDeleting(false);
        }
    };

    if (loading) return <div className="flex h-64 items-center justify-center"><Loader2 className="animate-spin text-primary-600" /></div>;

    if (selectedReport) {
        return (
            <div className="space-y-6">
                <button 
                    onClick={() => { setSelectedReport(null); setReportDetails(null); }}
                    className="flex items-center text-sm text-primary-600 hover:text-primary-800 font-medium"
                >
                    <ArrowLeft className="w-4 h-4 mr-1" /> Back to Saved Reports
                </button>

                <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{selectedReport.name}</h1>
                            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                                Created on {new Date(selectedReport.created_at).toLocaleString()}
                            </p>
                        </div>
                        <div className="bg-primary-50 dark:bg-primary-900/20 px-4 py-2 rounded-lg text-right">
                            <div className="text-xs text-primary-600 dark:text-primary-400 font-bold uppercase tracking-wider">Total Value</div>
                            <div className="text-xl font-black text-primary-900 dark:text-primary-200">${parseFloat(selectedReport.total_amount).toLocaleString()}</div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                        <div className="border border-slate-100 dark:border-slate-800 rounded-lg p-3 bg-slate-50 dark:bg-slate-800/50">
                            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Total Items</div>
                            <div className="text-lg font-bold text-slate-900 dark:text-white">{selectedReport.total_transactions}</div>
                        </div>
                        <div className="border border-green-100 dark:border-green-900/30 rounded-lg p-3 bg-green-50 dark:bg-green-900/20">
                            <div className="text-xs text-green-600 dark:text-green-400 font-medium">Matched</div>
                            <div className="text-lg font-bold text-green-700 dark:text-green-400">{selectedReport.matched_count}</div>
                        </div>
                        <div className="border border-red-100 dark:border-red-900/30 rounded-lg p-3 bg-red-50 dark:bg-red-900/20">
                            <div className="text-xs text-red-600 dark:text-red-400 font-medium">Mismatches</div>
                            <div className="text-lg font-bold text-red-700 dark:text-red-400">{selectedReport.total_transactions - selectedReport.matched_count}</div>
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
                        <h3 className="font-bold text-slate-800 dark:text-white">Reconciliation Breakdown</h3>
                        {reportDetails && (
                            <span className="text-xs text-slate-500 dark:text-slate-400">{reportDetails.matches.length} items</span>
                        )}
                    </div>
                    {loadingDetails ? (
                        <div className="p-12 text-center text-slate-500 dark:text-slate-400"><Loader2 className="animate-spin inline mr-2" /> Loading records...</div>
                    ) : reportDetails ? (
                        <ReportMatchTable matches={reportDetails.matches} />
                    ) : (
                        <div className="p-12 text-center text-red-500">Failed to load details.</div>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Saved Reports</h1>
                    <p className="text-slate-500 dark:text-slate-400 text-sm">Audit history of finalized reconciliations</p>
                </div>
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input 
                        type="text" 
                        placeholder="Search reports..." 
                        className="pl-10 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none w-64 text-slate-900 dark:text-white"
                    />
                </div>
            </div>

            {reports.length === 0 ? (
                <div className="bg-white dark:bg-slate-900 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800 p-12 text-center">
                    <div className="mx-auto w-16 h-16 bg-slate-50 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
                        <Database className="w-8 h-8 text-slate-300 dark:text-slate-600" />
                    </div>
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">No Saved Reports</h3>
                    <p className="text-slate-500 dark:text-slate-400 max-w-sm mx-auto mt-2">
                        Complete a reconciliation run and save the results to see them here for future auditing.
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {reports.map((report) => (
                        <div 
                            key={report.id} 
                            onClick={() => handleViewDetails(report)}
                            className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm hover:shadow-md transition-all cursor-pointer group border-l-4 border-l-primary-500"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-2 bg-primary-50 dark:bg-primary-900/30 rounded-lg group-hover:bg-primary-100 transition-colors">
                                    <FileText className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest flex items-center">
                                        <Calendar className="w-3 h-3 mr-1" />
                                        {new Date(report.created_at).toLocaleDateString()}
                                    </span>
                                    <button 
                                        onClick={(e) => handleDeleteClick(e, report)}
                                        className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-md transition-all opacity-0 group-hover:opacity-100"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-primary-600 transition-colors mb-1 truncate">
                                {report.name}
                            </h3>
                            <div className="mt-4 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                                        {report.matched_count} matches / {report.total_transactions} items
                                    </span>
                                </div>
                                <div className="text-primary-600 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <ChevronRight className="w-5 h-5" />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {showDeleteModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
                        <div className="flex items-start mb-4">
                            <div className="bg-red-100 p-3 rounded-full mr-4 text-red-600">
                                <AlertTriangle className="w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-slate-900 dark:text-white">Delete Report?</h3>
                                <p className="text-gray-500 text-sm mt-1">
                                    Are you sure you want to delete <span className="font-bold">"{reportToDelete?.name}"</span>? 
                                    This will also permanently delete all associated match data for this audit.
                                </p>
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 mt-6">
                            <button
                                onClick={() => setShowDeleteModal(false)}
                                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmDelete}
                                disabled={deleting}
                                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium flex items-center shadow-sm disabled:opacity-50 transition-colors"
                            >
                                {deleting ? 'Deleting...' : 'Yes, Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
