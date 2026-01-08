import { motion } from 'framer-motion'
import { BarChart3, Maximize2, Calendar, Hash } from 'lucide-react'
import { formatDate } from '../../utils/helpers'

export default function DashboardCard({ dashboard, index, onView }) {
  // Fallback name if the metabase sync hasn't provided one yet
  const displayName = dashboard.metabase_dashboard_name || dashboard.name || 'Untitled Dashboard';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ y: -4 }}
      className="card hover:shadow-xl transition-all cursor-pointer group border border-transparent hover:border-green-100"
      onClick={() => onView(dashboard)}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-green-700 rounded-2xl flex items-center justify-center group-hover:rotate-3 transition-transform shadow-lg shadow-green-100">
          <BarChart3 className="w-7 h-7 text-white" />
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onView(dashboard);
          }}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
          title="Expand View"
        >
          <Maximize2 className="w-5 h-5 text-gray-400" />
        </button>
      </div>

      <h3 className="text-xl font-bold text-gray-900 mb-2 line-clamp-1 group-hover:text-green-700 transition-colors">
        {displayName}
      </h3>
      
      <div className="space-y-2 mb-6">
        <div className="flex items-center text-sm text-gray-500">
          <Calendar className="w-4 h-4 mr-2 text-gray-400" />
          <span>Created {formatDate(dashboard.created_at)}</span>
        </div>
        <div className="flex items-center text-sm text-gray-500">
          <Hash className="w-4 h-4 mr-2 text-gray-400" />
          <span>Metabase ID: {dashboard.metabase_dashboard_id || 'Pending...'}</span>
        </div>
      </div>

      <button
        onClick={(e) => {
          e.stopPropagation();
          onView(dashboard);
        }}
        className="w-full py-3 px-4 bg-gray-50 hover:bg-green-600 hover:text-white text-gray-700 font-semibold rounded-xl transition-all flex items-center justify-center space-x-2 border border-gray-100 hover:border-green-600"
      >
        <span>View Analytics</span>
      </button>
    </motion.div>
  )
}