import React, { useState } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Grid,
  IconButton,
  Alert,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress
} from '@mui/material';
import { Upload, Delete, Add } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

function TaskCreator() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [taskData, setTaskData] = useState({
    name: '',
    description: '',
    type: 'css_consolidation',
    baselineFiles: [],
    config: {
      scoring: {
        pattern_consolidation: 40,
        ie_hack_removal: 20,
        font_tag_modernization: 15,
        style_block_cleanup: 15,
        smart_retention: 10
      },
      rules: {
        require_css_classes: true,
        max_inline_styles: 5,
        preserve_data_driven_styles: true
      }
    },
    agents: [
      { name: 'claude', prompt: '' },
      { name: 'qdev', prompt: '' },
      { name: 'gemini', prompt: '' }
    ]
  });

  const steps = ['Basic Info', 'Upload Files', 'Configure Scoring', 'Agent Prompts'];

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    const filePromises = files.map(file => {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          resolve({
            name: file.name,
            content: e.target.result,
            size: file.size
          });
        };
        reader.readAsText(file);
      });
    });

    Promise.all(filePromises).then(results => {
      setTaskData(prev => ({
        ...prev,
        baselineFiles: [...prev.baselineFiles, ...results]
      }));
    });
  };

  const removeFile = (index) => {
    setTaskData(prev => ({
      ...prev,
      baselineFiles: prev.baselineFiles.filter((_, i) => i !== index)
    }));
  };

  const updateAgent = (index, field, value) => {
    setTaskData(prev => {
      const newAgents = [...prev.agents];
      newAgents[index] = { ...newAgents[index], [field]: value };
      return { ...prev, agents: newAgents };
    });
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/api/v1/tasks/', taskData);
      setSuccess('Task created successfully!');
      setTimeout(() => {
        navigate(`/tasks/${response.data.id}`);
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to create task');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box>
            <TextField
              fullWidth
              label="Task Name"
              value={taskData.name}
              onChange={(e) => setTaskData({ ...taskData, name: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Description"
              value={taskData.description}
              onChange={(e) => setTaskData({ ...taskData, description: e.target.value })}
              margin="normal"
              multiline
              rows={4}
              required
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Task Type</InputLabel>
              <Select
                value={taskData.type}
                onChange={(e) => setTaskData({ ...taskData, type: e.target.value })}
              >
                <MenuItem value="css_consolidation">CSS Consolidation</MenuItem>
                <MenuItem value="javascript_refactor">JavaScript Refactor</MenuItem>
                <MenuItem value="code_review">Code Review</MenuItem>
              </Select>
            </FormControl>
          </Box>
        );
        
      case 1:
        return (
          <Box>
            <Button
              variant="contained"
              component="label"
              startIcon={<Upload />}
              fullWidth
              sx={{ mb: 2 }}
            >
              Upload Baseline Files
              <input
                type="file"
                hidden
                multiple
                accept=".html,.css,.js"
                onChange={handleFileUpload}
              />
            </Button>
            
            <Grid container spacing={2}>
              {taskData.baselineFiles.map((file, index) => (
                <Grid item xs={12} md={6} key={index}>
                  <Card>
                    <CardContent sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="subtitle1">{file.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {(file.size / 1024).toFixed(2)} KB
                        </Typography>
                      </Box>
                      <IconButton onClick={() => removeFile(index)} color="error">
                        <Delete />
                      </IconButton>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        );
        
      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>Scoring Weights (Total: 100)</Typography>
            {Object.entries(taskData.config.scoring).map(([key, value]) => (
              <TextField
                key={key}
                fullWidth
                label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                type="number"
                value={value}
                onChange={(e) => setTaskData(prev => ({
                  ...prev,
                  config: {
                    ...prev.config,
                    scoring: {
                      ...prev.config.scoring,
                      [key]: parseInt(e.target.value) || 0
                    }
                  }
                }))}
                margin="normal"
              />
            ))}
            
            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>Evaluation Rules</Typography>
            <FormControl fullWidth margin="normal">
              <InputLabel>Require CSS Classes</InputLabel>
              <Select
                value={taskData.config.rules.require_css_classes}
                onChange={(e) => setTaskData(prev => ({
                  ...prev,
                  config: {
                    ...prev.config,
                    rules: {
                      ...prev.config.rules,
                      require_css_classes: e.target.value
                    }
                  }
                }))}
              >
                <MenuItem value={true}>Yes</MenuItem>
                <MenuItem value={false}>No</MenuItem>
              </Select>
            </FormControl>
          </Box>
        );
        
      case 3:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>Agent Prompts</Typography>
            {taskData.agents.map((agent, index) => (
              <Card key={agent.name} sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    {agent.name.toUpperCase()} Agent
                  </Typography>
                  <TextField
                    fullWidth
                    label="Custom Prompt"
                    value={agent.prompt}
                    onChange={(e) => updateAgent(index, 'prompt', e.target.value)}
                    multiline
                    rows={3}
                    placeholder="Leave empty to use default prompt"
                  />
                </CardContent>
              </Card>
            ))}
          </Box>
        );
        
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Create New Task
        </Typography>
        
        <Stepper activeStep={activeStep} sx={{ mt: 3, mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        
        <Paper sx={{ p: 3 }}>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
          
          {renderStepContent(activeStep)}
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Button
              disabled={activeStep === 0}
              onClick={handleBack}
            >
              Back
            </Button>
            
            <Box>
              {activeStep === steps.length - 1 ? (
                <Button
                  variant="contained"
                  onClick={handleSubmit}
                  disabled={loading || !taskData.name || taskData.baselineFiles.length === 0}
                >
                  {loading ? 'Creating...' : 'Create Task'}
                </Button>
              ) : (
                <Button
                  variant="contained"
                  onClick={handleNext}
                  disabled={activeStep === 0 && (!taskData.name || !taskData.description)}
                >
                  Next
                </Button>
              )}
            </Box>
          </Box>
          
          {loading && <LinearProgress sx={{ mt: 2 }} />}
        </Paper>
      </Box>
    </Container>
  );
}

export default TaskCreator;