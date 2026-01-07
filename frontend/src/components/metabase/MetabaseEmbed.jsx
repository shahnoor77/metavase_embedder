import { useState, useEffect } from 'react'
import { AlertCircle, Maximize2, ExternalLink } from 'lucide-react'
import Loading from '../Common/Loading'

export default function MetabaseEmbed({ embedUrl, title }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    setLoading(true)
    setError(false)
  }, [embedUrl])

  const handleLoad = () => {
    setLoading(false)
  }

  const handleError = () => {
    setLoading(false)
    setError(true)
  }

  if (!embedUrl) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-lg">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No embed URL available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full h-full min-h-[600px] bg-white rounded-lg overflow-hidden border border-gray-200">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
          <Loading fullScreen={false} />
        </div>
      )}
      
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">Failed to load dashboard</p>
            <button 
              onClick={() => window.location.reload()} 
              className="btn-primary"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between p-3 bg-gray-50 border-b border-gray-200">
        <h3 className="font-medium text-gray-900">{title || 'Dashboard'}</h3>
        <div className="flex items-center space-x-2">
          
            href={embedUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
            title="Open in new tab"
          >
            <ExternalLink className="w-4 h-4 text-gray-600" />
          </a>
        </div>
      </div>

      <iframe
        src={embedUrl}
        className="w-full h-[calc(100%-56px)]"
        frameBorder="0"
        allowFullScreen
        onLoad={handleLoad}
        onError={handleError}
        title={title || 'Metabase Dashboard'}
      />
    </div>
  )
}