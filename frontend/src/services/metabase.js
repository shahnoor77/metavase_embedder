import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const metabaseService = {
  // Get Metabase session for a workspace
  getWorkspaceSession: async (workspaceId, token) => {
    try {
      const response = await axios.post(
        `${API_URL}/api/metabase/session/${workspaceId}`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to get session',
      }
    }
  },

  // Get workspace URL
  getWorkspaceUrl: async (workspaceId, token) => {
    try {
      const response = await axios.get(
        `${API_URL}/api/metabase/workspace/${workspaceId}/url`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )
      return { success: true, data: response.data }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to get URL',
      }
    }
  },

  // Open Metabase workspace in new window
  openMetabaseWorkspace: (workspaceUrl) => {
    const metabaseWindow = window.open(
      workspaceUrl,
      '_blank',
      'noopener,noreferrer'
    )
    
    if (!metabaseWindow) {
      return {
        success: false,
        error: 'Please allow popups for this site',
      }
    }
    
    return { success: true }
  },
}