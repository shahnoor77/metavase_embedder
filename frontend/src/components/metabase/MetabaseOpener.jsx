import { useState } from 'react'
import { ExternalLink, AlertCircle } from 'lucide-react'
import { metabaseService } from '../../services/metabase'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'

export default function MetabaseOpener({ workspace, buttonText = "Open in Metabase", className = "" }) {
  const [loading, setLoading] = useState(false)
  const { user } = useAuth()

  const handleOpen = async () => {
    setLoading(true)

    try {
      // Get workspace URL
      const urlResult = await metabaseService.getWorkspaceUrl(workspace.id, user.token)
      
      if (urlResult.success) {
        // Open Metabase
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
    <button
      onClick={handleOpen}
      disabled={loading}
      className={`${className} disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      {loading ? (
        <span>Opening...</span>
      ) : (
        <>
          <ExternalLink className="w-5 h-5 mr-2 inline" />
          {buttonText}
        </>
      )}
    </button>
  )
}