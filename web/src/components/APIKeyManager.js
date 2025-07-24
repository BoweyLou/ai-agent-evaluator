import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  Grid,
  IconButton,
  InputAdornment
} from '@mui/material';
import { Visibility, VisibilityOff, Check, Warning } from '@mui/icons-material';
import api from '../services/api';

function APIKeyManager() {
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
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const response = await api.get('/api/v1/settings/api-keys');
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to load API key status:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await api.post('/api/v1/settings/api-keys', keys);
      setMessage(response.data.message);
      await loadStatus();
      
      // Clear the input fields after successful update
      setKeys({ openrouter_api_key: '', github_token: '' });
    } catch (error) {
      setMessage('Failed to update API keys');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    try {
      await api.delete('/api/v1/settings/api-keys');
      setMessage('API keys cleared');
      await loadStatus();
    } catch (error) {
      setMessage('Failed to clear API keys');
    }
  };

  const toggleShowKey = (type) => {
    setShowKeys(prev => ({ ...prev, [type]: !prev[type] }));
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          API Key Configuration
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Configure your API keys for enhanced evaluation features. Keys are stored securely for your session.
        </Typography>
        
        {message && (
          <Alert 
            severity={message.includes('Failed') ? 'error' : 'success'} 
            sx={{ mb: 2 }}
          >
            {message}
          </Alert>
        )}
        
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle1">
                    OpenRouter API Key
                  </Typography>
                  {status.openrouter_configured && (
                    <Check color="success" sx={{ ml: 1 }} />
                  )}
                </Box>
                <TextField
                  fullWidth
                  label="OpenRouter API Key"
                  type={showKeys.openrouter ? 'text' : 'password'}
                  value={keys.openrouter_api_key}
                  onChange={(e) => setKeys(prev => ({ ...prev, openrouter_api_key: e.target.value }))}
                  placeholder="sk-or-your-openrouter-key"
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => toggleShowKey('openrouter')}
                          edge="end"
                        >
                          {showKeys.openrouter ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  Required for AI judge evaluation
                </Typography>
              </Box>
              
              {status.available_models.length > 0 && (
                <Alert severity="info" sx={{ mb: 2 }}>
                  {status.available_models.length} AI models available
                </Alert>
              )}
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Typography variant="subtitle1">
                    GitHub Token (Optional)
                  </Typography>
                  {status.github_configured && (
                    <Check color="success" sx={{ ml: 1 }} />
                  )}
                </Box>
                <TextField
                  fullWidth
                  label="GitHub Token"
                  type={showKeys.github ? 'text' : 'password'}
                  value={keys.github_token}
                  onChange={(e) => setKeys(prev => ({ ...prev, github_token: e.target.value }))}
                  placeholder="ghp_your-github-token"
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => toggleShowKey('github')}
                          edge="end"
                        >
                          {showKeys.github ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  Optional - for advanced workspace management
                </Typography>
              </Box>
              
              <Alert severity="info" icon={<Warning />}>
                GitHub integration provides branch-based workspaces but is not required for basic evaluation.
              </Alert>
            </Grid>
          </Grid>
          
          <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
            <Button
              type="submit"
              variant="contained"
              disabled={loading || (!keys.openrouter_api_key && !keys.github_token)}
            >
              {loading ? 'Updating...' : 'Update Keys'}
            </Button>
            
            <Button
              variant="outlined"
              onClick={handleClear}
              disabled={loading || (!status.openrouter_configured && !status.github_configured)}
            >
              Clear All
            </Button>
          </Box>
        </form>
        
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Current Status
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="body2">
                  OpenRouter: {status.openrouter_configured ? '✅ Configured' : '❌ Not configured'}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="body2">
                  GitHub: {status.github_configured ? '✅ Configured' : '❌ Not configured'}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
}

export default APIKeyManager;