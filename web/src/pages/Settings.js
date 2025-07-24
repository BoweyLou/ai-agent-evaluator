import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import { EyeIcon, EyeSlashIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

const Settings = () => {
  const [keys, setKeys] = useState({
    openrouter_api_key: '',
    github_token: ''
  });
  const [status, setStatus] = useState({
    openrouter_configured: false,
    github_configured: false,
    available_models: []
  });
  const [showKeys, setShowKeys] = useState({
    openrouter: false,
    github: false
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const response = await apiService.get('/settings/api-keys');
      setStatus(response);
    } catch (error) {
      console.error('Failed to load API key status:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await apiService.post('/settings/api-keys', keys);
      toast.success(response.message || 'API keys updated successfully');
      await loadStatus();
      
      // Clear the input fields after successful update
      setKeys({ openrouter_api_key: '', github_token: '' });
    } catch (error) {
      toast.error('Failed to update API keys');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    try {
      await apiService.delete('/settings/api-keys');
      toast.success('API keys cleared');
      await loadStatus();
    } catch (error) {
      toast.error('Failed to clear API keys');
    }
  };

  const toggleShowKey = (type) => {
    setShowKeys(prev => ({ ...prev, [type]: !prev[type] }));
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Settings
        </h1>
        <p className="text-gray-600">
          Configure your API keys and platform settings
        </p>
      </div>

      {/* API Configuration */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold text-gray-900">
            API Key Configuration
          </h2>
        </div>
        <div className="card-content">
          <p className="text-gray-600 mb-6">
            Configure your API keys for enhanced evaluation features. Keys are stored securely for your session.
          </p>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* OpenRouter API Key */}
              <div>
                <div className="flex items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700 mr-2">
                    OpenRouter API Key
                  </label>
                  {status.openrouter_configured && (
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  )}
                </div>
                <div className="relative">
                  <input
                    type={showKeys.openrouter ? 'text' : 'password'}
                    className="input-field pr-10"
                    placeholder="sk-or-your-openrouter-key"
                    value={keys.openrouter_api_key}
                    onChange={(e) => setKeys(prev => ({ ...prev, openrouter_api_key: e.target.value }))}
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => toggleShowKey('openrouter')}
                  >
                    {showKeys.openrouter ? (
                      <EyeSlashIcon className="w-5 h-5 text-gray-400" />
                    ) : (
                      <EyeIcon className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Required for AI judge evaluation
                </p>
                
                {status.available_models.length > 0 && (
                  <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-md">
                    <p className="text-sm text-blue-700">
                      ✅ {status.available_models.length} AI models available
                    </p>
                  </div>
                )}
              </div>
              
              {/* GitHub Token */}
              <div>
                <div className="flex items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700 mr-2">
                    GitHub Token (Optional)
                  </label>
                  {status.github_configured && (
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  )}
                </div>
                <div className="relative">
                  <input
                    type={showKeys.github ? 'text' : 'password'}
                    className="input-field pr-10"
                    placeholder="ghp_your-github-token"
                    value={keys.github_token}
                    onChange={(e) => setKeys(prev => ({ ...prev, github_token: e.target.value }))}
                  />
                  <button
                    type="button"
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    onClick={() => toggleShowKey('github')}
                  >
                    {showKeys.github ? (
                      <EyeSlashIcon className="w-5 h-5 text-gray-400" />
                    ) : (
                      <EyeIcon className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  Optional - for advanced workspace management
                </p>
                
                <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <p className="text-sm text-yellow-700">
                    ⚠️ GitHub integration provides branch-based workspaces but is not required for basic evaluation.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex space-x-4">
              <button
                type="submit"
                className="btn-primary"
                disabled={loading || (!keys.openrouter_api_key && !keys.github_token)}
              >
                {loading ? 'Updating...' : 'Update Keys'}
              </button>
              
              <button
                type="button"
                className="btn-secondary"
                onClick={handleClear}
                disabled={loading || (!status.openrouter_configured && !status.github_configured)}
              >
                Clear All
              </button>
            </div>
          </form>
        </div>
      </div>
      
      {/* Current Status */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold text-gray-900">
            Current Configuration
          </h2>
        </div>
        <div className="card-content">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-center space-x-3">
              {status.openrouter_configured ? (
                <CheckCircleIcon className="w-6 h-6 text-green-500" />
              ) : (
                <XCircleIcon className="w-6 h-6 text-red-500" />
              )}
              <div>
                <h3 className="font-medium text-gray-900">OpenRouter</h3>
                <p className="text-sm text-gray-600">
                  {status.openrouter_configured ? 'Configured and ready' : 'Not configured'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {status.github_configured ? (
                <CheckCircleIcon className="w-6 h-6 text-green-500" />
              ) : (
                <XCircleIcon className="w-6 h-6 text-red-500" />
              )}
              <div>
                <h3 className="font-medium text-gray-900">GitHub</h3>
                <p className="text-sm text-gray-600">
                  {status.github_configured ? 'Configured and ready' : 'Not configured'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Information */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold text-gray-900">
            Getting Your API Keys
          </h2>
        </div>
        <div className="card-content">
          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">OpenRouter (for AI Judge)</h3>
              <ol className="list-decimal list-inside text-sm text-gray-600 space-y-1">
                <li>Go to <a href="https://openrouter.ai/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-700">https://openrouter.ai/</a></li>
                <li>Sign up and get your API key</li>
                <li>Add credits to your account for AI model usage</li>
                <li>Paste the key above (starts with sk-or-...)</li>
              </ol>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-900 mb-2">GitHub (for Workspace Management)</h3>
              <ol className="list-decimal list-inside text-sm text-gray-600 space-y-1">
                <li>Go to GitHub Settings → Developer settings → Personal access tokens</li>
                <li>Create a token with 'repo' permissions</li>
                <li>Paste the token above (starts with ghp_...)</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;