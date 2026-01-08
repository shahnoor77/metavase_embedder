import { useState, useEffect } from 'react'
import { AlertCircle, ExternalLink, Loader2 } from 'lucide-react'

export default function MetabaseEmbed({ embedUrl, title }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  // Reset states when the URL changes
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
      <div className="flex items-center justify-center h-96 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 font-medium">No dashboard URL provided</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full h-full min-h-[600px] bg-white rounded-xl overflow-hidden border border-gray-200 shadow-sm">
      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-white z-10">
          <Loader2 className="w-10 h-10 text-green-600 animate-spin mb-4" />
          <p className="text-gray-500 text-sm font-medium">Connecting to Metabase...</p>
        </div>
      )}
      
      {/* Error Overlay */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 z-20">
          <div className="text-center p-6">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-bold text-red-900 mb-2">Load Failed</h3>
            <p className="text-red-700 mb-6">We couldn't reach the dashboard server.</p>
            <button 
              onClick={() => window.location.reload()} 
              className="btn-primary bg-red-600 hover:bg-red-700 border-none"
            >
              Retry Connection
            </button>
          </div>
        </div>
      )}

      {/* Header / Toolbar */}
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b border-gray-200">
        <h3 className="font-bold text-gray-800">{title || 'Dashboard View'}</h3>
        <div className="flex items-center">
          <a
            href={embedUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 hover:bg-white hover:text-green-600 rounded-lg transition-all border border-transparent hover:border-gray-200"
            title="Open Fullscreen in New Tab"
          >
            <ExternalLink className="w-5 h-5" />
          </a>
        </div>
      </div>

      {/* The Metabase Iframe */}
      <iframe
        src={embedUrl}
        className="w-full h-[calc(100%-60px)]"
        frameBorder="0"
        allowFullScreen
        onLoad={handleLoad}
        onError={handleError}
        title={title || 'Metabase Dashboard'}
      />
    </div>
  )
}