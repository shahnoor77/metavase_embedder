import { motion } from 'framer-motion'
import { X, Maximize2, Minimize2, Loader2 } from 'lucide-react'
import { useState, useEffect } from 'react'

export default function DashboardViewer({ dashboard, onClose }) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isIframeLoading, setIsIframeLoading] = useState(true)

  // Sync state if user exits fullscreen via ESC key
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((e) => {
        console.error(`Error attempting to enable full-screen mode: ${e.message}`)
      })
    } else {
      document.exitFullscreen()
    }
  }

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50"
      />

      {/* Modal Container */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="fixed inset-4 md:inset-8 z-50 bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col"
      >
        {/* Toolbar */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-white">
          <div>
            <h2 className="text-xl font-bold text-gray-900 line-clamp-1">
              {dashboard.name}
            </h2>
            <p className="text-xs text-gray-500 font-medium">Securely Embedded via Metabase</p>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={toggleFullscreen}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600"
              title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
            >
              {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
            </button>

            <button
              onClick={onClose}
              className="p-2 hover:bg-red-50 text-gray-400 hover:text-red-600 rounded-lg transition-colors"
              title="Close"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Iframe Viewport */}
        <div className="flex-1 bg-gray-50 relative">
          {isIframeLoading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 z-10">
              <Loader2 className="w-10 h-10 text-primary-600 animate-spin mb-3" />
              <p className="text-sm text-gray-600 animate-pulse font-medium">
                Decrypting secure data session...
              </p>
            </div>
          )}
          
          {dashboard.embed_url ? (
            <iframe
              src={dashboard.embed_url}
              className="w-full h-full border-0"
              onLoad={() => setIsIframeLoading(false)}
              allowTransparency
              allowFullScreen
            />
          ) : (
            <div className="flex items-center justify-center h-full text-center p-6">
              <div>
                <p className="text-gray-500 mb-1 font-medium">No valid embed URL found.</p>
                <p className="text-sm text-gray-400">
                  Please check your Metabase Embedding settings in the admin panel.
                </p>
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </>
  )
}