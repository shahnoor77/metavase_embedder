import React, { useState } from 'react';
import { UserPlus, Mail, Shield, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function WorkspaceMember({ workspaceId }) {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('viewer');
  const [inviting, setInviting] = useState(false);

  const handleInvite = async (e) => {
    e.preventDefault();
    setInviting(true);
    
    try {
      // Logic for adding a member (Backend should handle syncing to Metabase Group)
      // await workspaceAPI.addMember(workspaceId, { email, role });
      toast.success(`Invitation sent to ${email}`);
      setEmail('');
    } catch (error) {
      toast.error('Failed to invite member');
    } finally {
      setInviting(false);
    }
  };

  return (
    <div className="card border border-gray-100">
      <div className="flex items-center space-x-3 mb-6">
        <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
          <UserPlus className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-gray-900">Invite Team Member</h3>
      </div>

      <form onSubmit={handleInvite} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Email Address</label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field pl-10"
              placeholder="teammate@company.com"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Workspace Role</label>
          <div className="relative">
            <Shield className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="input-field pl-10 appearance-none"
            >
              <option value="viewer">Viewer (Read Only)</option>
              <option value="editor">Editor (Can create Dashboards)</option>
              <option value="admin">Admin (Manage Workspace)</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={inviting}
          className="w-full btn-primary py-3 flex items-center justify-center space-x-2"
        >
          {inviting ? <Loader2 className="w-5 h-5 animate-spin" /> : <span>Send Invite</span>}
        </button>
      </form>
    </div>
  );
}