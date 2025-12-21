import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import apiClient from '../../api/client';

export default function FileUploader({
  endpoint = '/statements/upload',
  label = 'Upload Statement',
  onUploadSuccess
}) {
  const [file, setFile] = useState(null);
  const [bankName, setBankName] = useState('');
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus('idle');
      setMessage('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a file.");
      return;
    }
    // Bank name is only required for Bank Statements, not Ledger
    const isBank = endpoint.includes('statements');
    if (isBank && !bankName) {
      setMessage("Please enter a bank name.");
      return;
    }

    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);
    if (isBank) formData.append('bank_name', bankName);

    try {
      // Use the dynamic endpoint prop
      const response = await apiClient.post(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setStatus('success');
      const count = Array.isArray(response.data) ? response.data.length : (response.data.transactions?.length || 0);
      setMessage(`Successfully processed ${count} records!`);
      setFile(null);
      setBankName('');

      if (onUploadSuccess) onUploadSuccess();

    } catch (error) {
      setStatus('error');
      setMessage("Upload failed. Check format.");
    }
  };

  return (
    <div className="max-w-xl mx-auto mt-10 p-6 bg-white rounded-xl shadow-lg border border-gray-100">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
        <Upload className="w-6 h-6 mr-2 text-indigo-600" />
        {label}
      </h2>

      {/* Only show Bank Name input if we are uploading statements */}
      {endpoint.includes('statements') && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Bank Name</label>
          <input
            type="text"
            value={bankName}
            onChange={(e) => setBankName(e.target.value)}
            placeholder="e.g. Chase"
            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
          />
        </div>
      )}

      {/* File Drop Zone */}
      <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:bg-gray-50 transition-colors relative">
        <input
          type="file"
          onChange={handleFileChange}
          accept=".csv,.xlsx,.pdf,.sta,.txt"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <div className="flex flex-col items-center pointer-events-none">
          {file ? (
            <>
              <FileText className="w-12 h-12 text-indigo-500 mb-2" />
              <span className="text-sm font-medium text-gray-900">{file.name}</span>
            </>
          ) : (
            <>
              <Upload className="w-12 h-12 text-gray-400 mb-2" />
              <span className="text-sm text-gray-500">Click to select file</span>
              <span className="text-xs text-gray-400 mt-2">Supports CSV, Excel, PDF, and MT940 (SWIFT)</span>
            </>
          )}
        </div>
      </div>

      <button
        onClick={handleUpload}
        disabled={status === 'uploading' || !file}
        className={`w-full mt-6 py-3 px-4 rounded-lg font-medium flex items-center justify-center transition-all ${status === 'uploading' || !file ? 'bg-gray-300' : 'bg-indigo-600 text-white hover:bg-indigo-700'}`}
      >
        {status === 'uploading' ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" /> Processing...</> : "Upload"}
      </button>

      {message && (
        <div className={`mt-4 p-3 rounded-lg flex items-center text-sm ${status === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {status === 'success' ? <CheckCircle className="w-5 h-5 mr-2" /> : <AlertCircle className="w-5 h-5 mr-2" />}
          {message}
        </div>
      )}
    </div>
  );
}