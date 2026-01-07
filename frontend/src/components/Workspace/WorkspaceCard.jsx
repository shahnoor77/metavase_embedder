import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Briefcase, BarChart3, Users, Calendar, ExternalLink, Settings } from 'lucide-react'
import { dashboardAPI } from '../../services/api'
import { metabaseService } from '../../services/metabase'
import { formatDate } from '../../utils/helpers'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'

export default function WorkspaceCard({ workspace, index }) {
  const [dashboardCount, setDashboardCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const { user } = useAuth()

  useEffect(() => {
    loadDashboardCount()
  }, [])

  const loadDashboardCount = async () => {
    try {
      const response = await dashboardAPI.getAll(workspace.id)
      setDashboardCount(response.data.length)
    } catch (error) {
      console.error('Error loading dashboard count:', error)
    }
  }

  const handleOpenMetabase = async (e) => {
    e.stopPropagation()
    setLoading(true)

    try {
      const urlResult = await metabaseService.getWorkspaceUrl(workspace.id, user.token)
      
      if (urlResult.success) {
        const openResult = metabaseService.openMetabaseWorkspace(urlResult.data.url)
        
        if (openResult.success) {
          toast.success('Opening Metabase workspace...')
        } else {
          toast.error(openResult.error)
        }
      } else {
        toast.error(urlResult.error)
      }
    } catch (error) {
      toast.error('Failed to open Metabase')
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ y: -4 }}
      className="card hover:shadow-lg transition-all group"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="w-14 h-14 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
          <Briefcase className="w-7 h-7 text-white" />
        </div>
        <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleOpenMetabase}
            disabled={loading}
            className="p-2 hover:bg-primary-50 rounded-lg transition-colors text-primary-600 disabled:opacity-50"
            title="Open in Metabase"
          >
            <ExternalLink className="w-5 h-5" />
          </button>
        </div>
      </div>

      <h3 className="text-xl font-bold text-gray-900 mb-2 line-clamp-1">
        {workspace.name}
      </h3>
      {workspace.description && (
        <p className="text-sm text-gray-600 mb-4">{workspace.description}</p>
      )}

      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-gray-600">
          <Calendar className="w-4 h-4 mr-2" />
          <span>Created {formatDate(workspace.created_at)}</span>
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-gray-200 mb-4">
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <div className="flex items-center space-x-1">
            <BarChart3 className="w-4 h-4" />
            <span>{dashboardCount}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Users className="w-4 h-4" />
            <span>1 member</span>
          </div>
        </div>
      </div>

      <button
        onClick={handleOpenMetabase}
        disabled={loading}
        className="w-full btn-primary disabled:opacity-50 flex items-center justify-center"
      >
        {loading ? (
          <span>Opening...</span>
        ) : (
          <>
            <ExternalLink className="w-4 h-4 mr-2" />
            Open in Metabase
          </>
        )}
      </button>
    </motion.div>
  )
}