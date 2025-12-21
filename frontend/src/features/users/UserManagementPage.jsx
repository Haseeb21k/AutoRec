import React, { useEffect, useState } from 'react';
import { Users, Shield, Mail, CheckCircle, XCircle, Plus, Loader2, Trash2 } from 'lucide-react';
import apiClient from '@/api/client';

export default function UserManagementPage() {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteRole, setInviteRole] = useState('standard');
    const [inviting, setInviting] = useState(false);

    const fetchUsers = async () => {
        try {
            const res = await apiClient.get('/users/');
            setUsers(res.data);
        } catch (err) {
            console.error("Failed to fetch users", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const [inviteSuccessModalOpen, setInviteSuccessModalOpen] = useState(false);
    const [invitedEmailState, setInvitedEmailState] = useState('');

    const handleInvite = async (e) => {
        e.preventDefault();
        if (!inviteEmail) return;
        setInviting(true);
        try {
            await apiClient.post('/users/invite', { email: inviteEmail, role: inviteRole });

            // Success Handling
            setInvitedEmailState(inviteEmail);
            setInviteSuccessModalOpen(true);

            setInviteEmail('');
            fetchUsers();
        } catch (err) {
            alert("Failed to invite user. They might already exist.");
        } finally {
            setInviting(false);
        }
    };

    const toggleStatus = async (userId) => {
        try {
            await apiClient.patch(`/users/${userId}/status`);
            fetchUsers();
        } catch (err) {
            alert("Failed to update status");
        }
    };

    const [deleteModalOpen, setDeleteModalOpen] = useState(false);
    const [userToDelete, setUserToDelete] = useState(null);
    const [deleting, setDeleting] = useState(false);

    const handleDeleteClick = (user) => {
        setUserToDelete(user);
        setDeleteModalOpen(true);
    };

    const confirmDelete = async () => {
        if (!userToDelete) return;
        setDeleting(true);
        try {
            await apiClient.delete(`/users/${userToDelete.id}`);
            fetchUsers();
            setDeleteModalOpen(false);
            setUserToDelete(null);
        } catch (err) {
            alert("Failed to delete user. They might have linked data (uploads).");
        } finally {
            setDeleting(false);
        }
    };

    return (
        <div className="space-y-6 relative">
            {/* Custom Invite Success Modal */}
            {inviteSuccessModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full p-6 animate-in fade-in zoom-in duration-200">
                        <div className="text-center">
                            <div className="mx-auto bg-green-100 p-3 rounded-full w-14 h-14 flex items-center justify-center mb-4">
                                <Mail className="w-6 h-6 text-green-600" />
                            </div>
                            <h3 className="text-xl font-bold text-gray-900">Invite Sent!</h3>
                            <p className="text-gray-500 text-sm mt-2">
                                An invitation has been sent to <br />
                                <span className="font-medium text-gray-900">{invitedEmailState}</span>
                            </p>
                            <button
                                onClick={() => setInviteSuccessModalOpen(false)}
                                className="mt-6 w-full py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors shadow-sm"
                            >
                                Done
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Custom Delete Warning Modal */}
            {deleteModalOpen && userToDelete && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-in fade-in zoom-in duration-200">
                        <div className="flex items-start mb-4">
                            <div className="bg-red-100 p-3 rounded-full mr-4">
                                <Trash2 className="w-6 h-6 text-red-600" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">Delete User?</h3>
                                <p className="text-gray-500 text-sm mt-1">
                                    Are you sure you want to remove <strong>{userToDelete.email}</strong>?
                                </p>
                                <p className="text-red-500 text-xs mt-2 font-medium bg-red-50 p-2 rounded">
                                    Warning: This action cannot be undone.
                                </p>
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 mt-6">
                            <button
                                onClick={() => setDeleteModalOpen(false)}
                                className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmDelete}
                                disabled={deleting}
                                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium flex items-center shadow-sm disabled:opacity-50 transition-colors"
                            >
                                {deleting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Trash2 className="w-4 h-4 mr-2" />}
                                {deleting ? 'Deleting...' : 'Yes, Delete User'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
                    <p className="text-gray-500 text-sm">Control access and roles</p>
                </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <h3 className="text-sm font-bold text-gray-500 uppercase mb-4">Invite New User</h3>
                <form onSubmit={handleInvite} className="flex gap-4 items-center">
                    <div className="flex-1 relative">
                        <Mail className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                        <input
                            type="email"
                            required
                            placeholder="colleague@company.com"
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                            value={inviteEmail}
                            onChange={e => setInviteEmail(e.target.value)}
                        />
                    </div>
                    <select
                        className="border border-gray-300 rounded-lg px-4 py-2 bg-white"
                        value={inviteRole}
                        onChange={e => setInviteRole(e.target.value)}
                    >
                        <option value="standard">Standard User</option>
                        <option value="superuser">Superuser</option>
                    </select>
                    <button
                        type="submit"
                        disabled={inviting}
                        className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-indigo-700 flex items-center disabled:opacity-50"
                    >
                        {inviting ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Plus className="w-4 h-4 mr-2" /> Send Invite</>}
                    </button>
                </form>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {users.map((u) => (
                            <tr key={u.id}>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 font-bold text-xs">
                                            {u.email.charAt(0).toUpperCase()}
                                        </div>
                                        <div className="ml-4 text-sm font-medium text-gray-900">{u.email}</div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${u.role === 'superuser' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                                        }`}>
                                        {u.role}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`flex items-center text-xs font-medium ${u.is_active ? 'text-green-600' : 'text-red-500'}`}>
                                        {u.is_active ? <CheckCircle className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
                                        {u.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <button
                                        onClick={() => toggleStatus(u.id)}
                                        className="text-indigo-600 hover:text-indigo-900 text-xs font-bold mr-4"
                                    >
                                        {u.is_active ? 'Deactivate' : 'Activate'}
                                    </button>
                                    <button
                                        onClick={() => handleDeleteClick(u)}
                                        className="text-red-600 hover:text-red-900 text-xs"
                                        title="Delete User"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}