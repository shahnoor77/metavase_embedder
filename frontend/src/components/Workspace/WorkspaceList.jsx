import React, { useState, useEffect } from 'react';
import { Plus, Folder, Calendar, Users, ExternalLink } from 'lucide-react';
import api from '../services/api';

const WorkspaceList = () => {
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: '',
    description: ''
  });
  const [creating, setCreating] = useState(false);

  // Load workspaces on mount
  useEffect(() => {
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getWorkspaces();
      setWorkspaces(data);
    } catch (err) {
      setError(err.message || 'Failed to load workspaces');
      console.error('Error loading workspaces:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    
    if (!createForm.name.trim()) {
      alert('Please enter a workspace name');
      return;
    }

    try {
      setCreating(true);
      setError(null);
      
      const newWorkspace = await api.createWorkspace(createForm);
      
      setWorkspaces([newWorkspace, ...workspaces]);
      setShowCreateModal(false);
      setCreateForm({ name: '', description: '' });
      
      alert('Workspace created successfully!');
    } catch (err) {
      setError(err.message || 'Failed to create workspace');
      console.error('Error creating workspace:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleOpenWorkspace = async (workspaceId) => {
    try {
      const { url } = await api.getWorkspaceEmbeddedUrl(workspaceId);
      
      // Open embedded Metabase in new window/tab
      const metabaseUrl = `${process.env.REACT_APP_METABASE_URL}${url}`;
      window.open(metabaseUrl, '_blank');
    } catch (err) {
      alert('Failed to open workspace: ' + (err.message || 'Unknown error'));
      console.error('Error opening workspace:', err);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading workspaces...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">My Workspaces</h1>
            <p className="mt-2 text-gray-600">
              Manage your analytics workspaces and dashboards
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
          >
            <Plus className="h-5 w-5 mr-2" />
            New Workspace
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Workspaces Grid */}
      {workspaces.length === 0 ? (
        <div className="text-center py-12">
          <Folder className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No workspaces</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by creating a new workspace
          </p>
          <div className="mt-6">
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-5 w-5 mr-2" />
              New Workspace
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {workspaces.map((workspace) => (
            <div
              key={workspace.id}
              className="bg-white overflow-hidden shadow-sm rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <Folder className="h-8 w-8 text-blue-600" />
                    </div>
                    <div className="ml-3">
                      <h3 className="text-lg font-medium text-gray-900">
                        {workspace.name}
                      </h3>
                    </div>
                  </div>
                </div>

                {workspace.description && (
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                    {workspace.description}
                  </p>
                )}

                <div className="flex items-center text-sm text-gray-500 mb-4">
                  <Calendar className="h-4 w-4 mr-2" />
                  Created {formatDate(workspace.created_at)}
                </div>

                {workspace.metabase_collection_id && (
                  <div className="text-xs text-gray-400 mb-4">
                    Collection ID: {workspace.metabase_collection_id}
                  </div>
                )}

                <button
                  onClick={() => handleOpenWorkspace(workspace.id)}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Open in Metabase
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Workspace Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">
                Create New Workspace
              </h3>
            </div>

            <form onSubmit={handleCreateWorkspace}>
              <div className="px-6 py-4">
                <div className="mb-4">
                  <label
                    htmlFor="name"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Workspace Name *
                  </label>
                  <input
                    type="text"
                    id="name"
                    value={createForm.name}
                    onChange={(e) =>
                      setCreateForm({ ...createForm, name: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="My Analytics Workspace"
                    required
                  />
                </div>

                <div className="mb-4">
                  <label
                    htmlFor="description"
                    className="block text-sm font-medium text-gray-700 mb-2"
                  >
                    Description
                  </label>
                  <textarea
                    id="description"
                    value={createForm.description}
                    onChange={(e) =>
                      setCreateForm({
                        ...createForm,
                        description: e.target.value,
                      })
                    }
                    rows="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Optional description for your workspace"
                  />
                </div>
              </div>

              <div className="px-6 py-4 bg-gray-50 rounded-b-lg flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setCreateForm({ name: '', description: '' });
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  disabled={creating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={creating}
                >
                  {creating ? 'Creating...' : 'Create Workspace'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkspaceList;