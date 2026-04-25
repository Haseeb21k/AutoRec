import React, { useEffect, useState } from 'react';
import { Database, Calendar, FileText, CheckCircle2, ChevronRight, ArrowLeft, Loader2, Search } from 'lucide-react';
import apiClient from '@/api/client';

// Simple match table for the detail view
const ReportMatchTable = ({ matches }) => (
    <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-500 uppercase bg-gray-50 border-b">
                <tr>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Bank Item</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Ledger Item</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                </tr>
            </thead>
            <tbody className="divide-y">
                {matches.map((m) => (
                    <tr key={m.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap text-gray-500">{m.date}</td>
                        <td className="px-4 py-3 font-medium text-gray-800">{m.bank_desc}</td>
                        <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                m.match_type === 'exact' ? 'bg-green-100 text-green-700' :
                                m.match_type === 'fuzzy_date' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-red-100 text-red-700'
                            }`}>
                                {m.match_type.replace('_', ' ')}
                            </span>
                        </td>
                        <td className="px-4 py-3 text-gray-600">{m.ledger_desc}</td>
                        <td className="px-4 py-3 text-right font-bold">${Math.abs(m.amount).toLocaleString()}</td>
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

    if (loading) return <div className="flex h-64 items-center justify-center"><Loader2 className="animate-spin text-indigo-600" /></div>;

    if (selectedReport) {
        return (
            <div className="space-y-6">
                <button 
                    onClick={() => { setSelectedReport(null); setReportDetails(null); }}
                    className="flex items-center text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                >
                    <ArrowLeft className="w-4 h-4 mr-1" /> Back to Saved Reports
                </button>

                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">{selectedReport.name}</h1>
                            <p className="text-sm text-gray-500 mt-1">
                                Created on {new Date(selectedReport.created_at).toLocaleString()}
                            </p>
                        </div>
                        <div className="bg-indigo-50 px-4 py-2 rounded-lg text-right">
                            <div className="text-xs text-indigo-600 font-bold uppercase tracking-wider">Total Value</div>
                            <div className="text-xl font-black text-indigo-900">${parseFloat(selectedReport.total_amount).toLocaleString()}</div>
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 mt-6">
                        <div className="border border-gray-100 rounded-lg p-3 bg-gray-50">
                            <div className="text-xs text-gray-500 font-medium">Total Items</div>
                            <div className="text-lg font-bold">{selectedReport.total_transactions}</div>
                        </div>
                        <div className="border border-gray-100 rounded-lg p-3 bg-green-50">
                            <div className="text-xs text-green-600 font-medium">Matched</div>
                            <div className="text-lg font-bold text-green-700">{selectedReport.matched_count}</div>
                        </div>
                        <div className="border border-gray-100 rounded-lg p-3 bg-red-50">
                            <div className="text-xs text-red-600 font-medium">Mismatches</div>
                            <div className="text-lg font-bold text-red-700">{selectedReport.total_transactions - selectedReport.matched_count}</div>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                        <h3 className="font-bold text-gray-800">Reconciliation Breakdown</h3>
                        {reportDetails && (
                            <span className="text-xs text-gray-500">{reportDetails.matches.length} items</span>
                        )}
                    </div>
                    {loadingDetails ? (
                        <div className="p-12 text-center text-gray-500"><Loader2 className="animate-spin inline mr-2" /> Loading records...</div>
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
                    <h1 className="text-2xl font-bold text-gray-900">Saved Reports</h1>
                    <p className="text-gray-500 text-sm">Audit history of finalized reconciliations</p>
                </div>
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input 
                        type="text" 
                        placeholder="Search reports..." 
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none w-64"
                    />
                </div>
            </div>

            {reports.length === 0 ? (
                <div className="bg-white rounded-2xl border-2 border-dashed border-gray-200 p-12 text-center">
                    <div className="mx-auto w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                        <Database className="w-8 h-8 text-gray-300" />
                    </div>
                    <h3 className="text-lg font-bold text-gray-900">No Saved Reports</h3>
                    <p className="text-gray-500 max-w-sm mx-auto mt-2">
                        Complete a reconciliation run and save the results to see them here for future auditing.
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {reports.map((report) => (
                        <div 
                            key={report.id} 
                            onClick={() => handleViewDetails(report)}
                            className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition-all cursor-pointer group border-l-4 border-l-indigo-500"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-2 bg-indigo-50 rounded-lg group-hover:bg-indigo-100 transition-colors">
                                    <FileText className="w-5 h-5 text-indigo-600" />
                                </div>
                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest flex items-center">
                                    <Calendar className="w-3 h-3 mr-1" />
                                    {new Date(report.created_at).toLocaleDateString()}
                                </span>
                            </div>
                            <h3 className="font-bold text-gray-900 group-hover:text-indigo-600 transition-colors">{report.name}</h3>
                            <div className="mt-4 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <div className="flex -space-x-1">
                                        <div className="w-2 h-2 rounded-full bg-green-500"></div>
                                        <div className="w-2 h-2 rounded-full bg-indigo-300"></div>
                                    </div>
                                    <span className="text-xs text-gray-500 font-medium">
                                        {report.matched_count} matches / {report.total_transactions} items
                                    </span>
                                </div>
                                <div className="text-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <ChevronRight className="w-5 h-5" />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
