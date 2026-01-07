import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart3, Search, Plus, ExternalLink } from 'lucide-react'
import { workspaceAPI, dashboardAPI } from '../services/api'
import { metabaseService } from '../services/metabase'
import { useAuth } from '../context/AuthContext'
import Loading from '../components/Common/Loading'
import DashboardCard from '../components/Dashboard/DashboardCard'
import DashboardViewer from '../components/Dashboard/DashboardViewer'
import Modal from '../components/Common/Modal'
import toast from 'react-hot-toast'

export default function DashboardsPage() {
  const [workspaces, setWorkspaces] = useState([])
  const [selectedWorkspace, setSelectedWorkspace] = useState(null)
  const [dashboards, setDashboards] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [viewingDashboard, setViewingDashboard] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [creating, setCreating] = useState(false)
  const [newDashboard, setNewDashboard] = useState({ name: '' })
  const { user } = useAuth()

  useEffect(() => {
    loadWorkspaces()
  }, [])

  useEffect(() => {
    if (selectedWorkspace) {
      loadDashboards()
    }
  }, [selectedWorkspace])

  const loadWorkspaces = async () => {
    try {
      const response = await workspaceAPI.getAll()
      const workspaceData = response.data
      setWorkspaces(workspaceData)
      if (workspaceData.length > 0) {
        setSelectedWorkspace(workspaceData[0])
      }
    } catch (error) {
      toast.error('Failed to load workspaces')
    } finally {
      setLoading(false)
    }
  }

  const loadDashboards = async () => {
    if (!selectedWorkspace) return

    try {
      const response = await dashboardAPI.getAll(selectedWorkspace.id)
      setDashboards(response.data)
    } catch (error) {
      toast.error('Failed to load dashboards')
    }
  }

  const handleViewDashboard = async (dashboard) => {
    try {
      const response = await dashboardAPI.getById(dashboard.id)
      setViewingDashboard(response.data)
    } catch (error) {
      toast.error('Failed to load dashboard details')
    }
  }

  const handleCreateDashboard = async (e) => {
    e.preventDefault()
    setCreating(true)

    try {
      await dashboardAPI.create({
        workspace_id: selectedWorkspace.id,
        name: newDashboard.name,
      })
      toast.success('Dashboard created successfully!')
      setShowCreateModal(false)
      setNewDashboard({ name: '' })
      loadDashboards()
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create dashboard')
    } finally {
      setCreating(false)
    }
  }

  const handleOpenInMetabase = async () => {
    if (!selectedWorkspace) return

    try {
      const urlResult = await metabaseService.getWorkspaceUrl(selectedWorkspace.id, user.token)
      if (urlResult.success) {
        metabaseService.openMetabaseWorkspace(urlResult.data.url)
        toast.success('Opening Metabase...')
      } else {
        toast.error(urlResult.error)
      }
    } catch (error) {
      toast.error('Failed to open Metabase')
    }
  }

  const filteredDashboards = dashboards.filter((dashboard) =>
    (dashboard.metabase_dashboard_name || dashboard.name || '')
      .toLowerCase()
      .includes(searchQuery.toLowerCase())
  )

  if (loading) {
    return <Loading fullScreen={false} />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboards</h1>
          <p className="text-gray-600 mt-1">
            View and manage all your analytics dashboards
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleOpenInMetabase}
            className="btn-secondary flex items-center space-x-2"
          >
            <ExternalLink className="w-5 h-5" />
            <span>Open Metabase</span>
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center space-x-2"
            disabled={!selectedWorkspace}
          >
            <Plus className="w-5 h-5" />
            <span>New Dashboard</span>
          </button>
        </div>
      </div>

      {/* Workspace Selector */}
      {workspaces.length > 0 && (
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Workspace
          </label>
          <select
            value={selectedWorkspace?.id || ''}
            onChange={(e) => {
              const workspace = workspaces.find(
                (w) => w.id === parseInt(e.target.value)
              )
              setSelectedWorkspace(workspace)
            }}
            className="input-field"
          >
            {workspaces.map((workspace) => (
              <option key={workspace.id} value={workspace.id}>
                {workspace.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Search */}
      {dashboards.length > 0 && (
        <div className="card">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search dashboards..."
              className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
            />
          </div>
        </div>
      )}

      {/* Dashboards Grid */}
      {filteredDashboards.length === 0 ? (
        <div className="card text-center py-16">
          <BarChart3 className="w-20 h-20 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            {searchQuery
              ? 'No dashboards found'
              : 'No dashboards in this workspace'}
          </h3>
          <p className="text-gray-600 mb-6">
            {searchQuery
              ? 'Try adjusting your search query'
              : 'Create your first dashboard or open Metabase to build one'}
          </p>
          <div className="flex items-center justify-center space-x-3">
            <button
              onClick={handleOpenInMetabase}
              className="btn-secondary flex items-center space-x-2"
            >
              <ExternalLink className="w-5 h-5" />
              <span>Open in Metabase</span>
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary flex items-center space-x-2"
            >
              <Plus className="w-5 h-5" />
              <span>Create Dashboard</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDashboards.map((dashboard, index) => (
            <DashboardCard
              key={dashboard.id}
              dashboard={{
                ...dashboard,
                name: dashboard.metabase_dashboard_name || dashboard.name,
              }}
              index={index}
              onView={handleViewDashboard}
            />
          ))}
        </div>
      )}

      {/* Dashboard Viewer Modal */}
      <AnimatePresence>
        {viewingDashboard && (
          <DashboardViewer
            dashboard={viewingDashboard}
            onClose={() => setViewingDashboard(null)}
          />
        )}
      </AnimatePresence>

      {/* Create Dashboard Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Create New Dashboard"
      >
        <form onSubmit={handleCreateDashboard} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dashboard Name
            </label>
            <input
              type="text"
              value={newDashboard.name}
              onChange={(e) => setNewDashboard({ name: e.target.value })}
              className="input-field"
              placeholder="e.g., Sales Report Q1 2024"
              required
            />
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              This will create an empty dashboard in Metabase. You can then open it
              in Metabase to add queries, charts, and visualizations.
            </p>
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="flex-1 btn-secondary"
              disabled={creating}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 btn-primary"
              disabled={creating}
            >
              {creating ? 'Creating...' : 'Create Dashboard'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}