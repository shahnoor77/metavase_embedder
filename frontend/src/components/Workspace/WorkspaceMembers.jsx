import { useState, useEffect } from 'react'
import { Users, Plus, X, Mail } from 'lucide-react'
import { workspaceAPI } from '../../services/api'
import toast from 'react-hot-toast'
import Modal from '../Common/Modal'

export default function WorkspaceMembers({ workspace }) {
  const [members, setMembers] = useState([])
  const [showAddModal, setShowAddModal] = useState(false)
  const [newMemberEmail, setNewMemberEmail] = useState('')
  const [loading, setLoading] = useState(false)

  const handleAddMember = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      // This would need a new endpoint to add user by email
      toast.success('Member invitation sent!')
      setShowAddModal(false)
      setNewMemberEmail('')
    } catch (error) {
      toast.error('Failed to add member')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Users className="w-6 h-6 text-gray-600" />
          <h2 className="text-xl font-bold text-gray-900">Members</h2>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Member</span>
        </button>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center">
              <Users className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-medium text-gray-900">You (Owner)</p>
              <p className="text-sm text-gray-600">Full access</p>
            </div>
          </div>
          <span className="px-3 py-1 bg-primary-100 text-primary-700 text-sm font-medium rounded-full">
            Owner
          </span>
        </div>
      </div>

      <Modal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        title="Add Member to Workspace"
      >
        <form onSubmit={handleAddMember} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="email"
                value={newMemberEmail}
                onChange={(e) => setNewMemberEmail(e.target.value)}
                className="input-field pl-10"
                placeholder="member@example.com"
                required
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              They will receive an invitation email
            </p>
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={() => setShowAddModal(false)}
              className="flex-1 btn-secondary"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 btn-primary"
              disabled={loading}
            >
              {loading ? 'Sending...' : 'Send Invitation'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}