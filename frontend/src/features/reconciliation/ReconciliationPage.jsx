import React, { useEffect, useState } from 'react';
import { RefreshCw, ArrowRight, Building, Landmark, Trash2, AlertCircle } from 'lucide-react';
import apiClient from '@/api/client';
import FileUploader from '@/features/upload/FileUploader';
import { useAuth } from '@/features/auth/AuthContext';

export default function ReconciliationPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('bank');
    const [bankData, setBankData] = useState([]);
    const [ledgerData, setLedgerData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    const [clearing, setClearing] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                if (activeTab === 'bank') {
                    const res = await apiClient.get('/statements/');
                    setBankData(res.data);
                } else {
                    const res = await apiClient.get('/ledger/');
                    setLedgerData(res.data);
                }
            } catch (err) {
                console.error("Failed to fetch data", err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [refreshTrigger, activeTab]);

    const handleRefresh = () => setRefreshTrigger(prev => prev + 1);

    const [showClearModal, setShowClearModal] = useState(false);

    const handleClearClick = () => {
        setShowClearModal(true);
    };

    const confirmClear = async () => {
        setClearing(true);
        try {
            await apiClient.delete('/reconcile/clear');
            // alert("System cleared. You can start over."); // Optional: remove alert for smoother UX
            handleRefresh();
        } catch (err) {
            alert("Failed to clear data.");
        } finally {
            setClearing(false);
            setShowClearModal(false);
        }
    };

    // --- PREPARE DATA FOR TABLE ---
    // Flatten bank data or use ledger data directly
    const allRows = activeTab === 'bank'
        ? bankData.flatMap(s => s.transactions.map(t => ({ ...t, source: s.bank_name })))
        : ledgerData;

    // Slice for Top 10
    const displayedRows = allRows.slice(0, 10);
    const totalCount = allRows.length;

    return (
        <div className="space-y-6 relative">
            {/* Custom Modal Overlay */}
            {showClearModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
                        <div className="flex items-start mb-4">
                            <div className="bg-red-100 p-3 rounded-full mr-4">
                                <AlertCircle className="w-6 h-6 text-red-600" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">Clear All Data?</h3>
                                <p className="text-gray-500 text-sm mt-1">
                                    This action cannot be undone. It will permanently delete all:
                                </p>
                                <ul className="list-disc list-inside text-gray-500 text-sm mt-2 ml-1">
                                    <li>Uploaded Bank Statements</li>
                                    <li>Internal Ledger Entries</li>
                                    <li>Reconciliation Matches</li>
                                </ul>
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 mt-6">
                            <button
                                onClick={() => setShowClearModal(false)}
                                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmClear}
                                disabled={clearing}
                                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium flex items-center shadow-sm disabled:opacity-50 transition-colors"
                            >
                                {clearing ? (
                                    <>
                                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                                        Clearing...
                                    </>
                                ) : (
                                    <>
                                        <Trash2 className="w-4 h-4 mr-2" />
                                        Yes, Clear Everything
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Statement Upload</h1>
                    <p className="text-gray-500 text-sm">Manage Bank Statements and Internal Ledgers</p>
                </div>

                <div className="flex flex-wrap gap-3">
                    <button
                        onClick={handleClearClick}
                        disabled={clearing}
                        className="flex items-center px-4 py-2 bg-red-50 text-red-600 border border-red-200 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors disabled:opacity-50"
                    >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Clear Data
                    </button>

                    <button
                        onClick={handleRefresh}
                        className="flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                </div>
            </div>

            <div className="flex space-x-4 border-b border-gray-200">
                <button
                    onClick={() => setActiveTab('bank')}
                    className={`pb-2 px-4 flex items-center font-medium text-sm transition-colors border-b-2 ${activeTab === 'bank' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                >
                    <Landmark className="w-4 h-4 mr-2" /> Bank Statements
                </button>
                <button
                    onClick={() => setActiveTab('ledger')}
                    className={`pb-2 px-4 flex items-center font-medium text-sm transition-colors border-b-2 ${activeTab === 'ledger' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                >
                    <Building className="w-4 h-4 mr-2" /> Internal Ledger
                </button>
            </div>



            {
                user?.role === 'superuser' && (
                    <FileUploader
                        key={activeTab}
                        endpoint={activeTab === 'bank' ? '/statements/upload' : '/ledger/upload'}
                        label={activeTab === 'bank' ? 'Upload Bank Statement (PDF/CSV)' : 'Upload Ledger Export (CSV)'}
                        onUploadSuccess={handleRefresh}
                    />
                )
            }

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mt-8">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                    <h3 className="font-semibold text-gray-800">
                        {activeTab === 'bank' ? 'Uploaded Bank Transactions' : 'Internal Ledger Records'}
                    </h3>
                    <div className="flex items-center gap-2">
                        {totalCount > 10 && (
                            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                                Showing top 10 of {totalCount}
                            </span>
                        )}
                        <span className="text-xs font-medium bg-indigo-100 text-indigo-800 px-2.5 py-0.5 rounded-full">Live Data</span>
                    </div>
                </div>

                {loading ? (
                    <div className="p-8 text-center text-gray-500">Loading...</div>
                ) : totalCount === 0 ? (
                    <div className="p-12 text-center">
                        <div className="mx-auto h-12 w-12 text-gray-300 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                            <ArrowRight className="h-6 w-6" />
                        </div>
                        <h3 className="text-lg font-medium text-gray-900">No Data Yet</h3>
                        <p className="text-gray-500">Upload a file above to populate this table.</p>
                    </div>
                ) : (
                    <>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                                        {activeTab === 'bank' && <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Bank</th>}
                                        {activeTab === 'ledger' && <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">GL Code</th>}
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {displayedRows.map((row, idx) => (
                                        <tr key={row.id || idx} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{row.date}</td>
                                            <td className="px-6 py-4 text-sm text-gray-900 font-medium">{row.description}</td>
                                            <td className={`px-6 py-4 whitespace-nowrap text-sm font-bold ${row.amount < 0 ? 'text-red-600' : 'text-green-600'}`}>
                                                ${parseFloat(row.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                                            </td>
                                            {activeTab === 'bank' && <td className="px-6 py-4 text-sm text-gray-500">{row.source}</td>}
                                            {activeTab === 'ledger' && <td className="px-6 py-4 text-sm text-gray-500">{row.gl_code || 'N/A'}</td>}
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                                                    Pending
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        {totalCount > 10 && (
                            <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-center text-xs text-gray-500">
                                ... and {totalCount - 10} more records
                            </div>
                        )}
                    </>
                )}
            </div>
        </div >
    );
}