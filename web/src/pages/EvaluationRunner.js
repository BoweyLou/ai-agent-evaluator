import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Stepper,
  Step,
  StepLabel,
  Alert,
  Grid,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  CheckCircle,
  Warning,
  Code,
  Download,
  ExpandMore
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';

function EvaluationRunner() {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeStep, setActiveStep] = useState(0);
  const [agentResults, setAgentResults] = useState({});
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [uploadDialog, setUploadDialog] = useState(false);
  const [uploadContent, setUploadContent] = useState('');

  useEffect(() => {
    loadTask();
  }, [taskId]);

  const loadTask = async () => {
    try {
      const response = await api.get(`/api/v1/tasks/${taskId}`);
      setTask(response.data);
      
      // Check if evaluation already exists
      const evalResponse = await api.get(`/api/v1/evaluations/task/${taskId}`);
      if (evalResponse.data.length > 0) {
        setEvaluation(evalResponse.data[0]);
        setActiveStep(evalResponse.data[0].status === 'completed' ? 3 : 2);
      }
    } catch (err) {
      if (err.response?.status !== 404) {
        setError('Failed to load task');
      }
    } finally {
      setLoading(false);
    }
  };

  const startEvaluation = async () => {
    try {
      const response = await api.post(`/api/v1/evaluations/`, {
        task_id: taskId,
        agents: task.agents.map(a => a.name)
      });
      setEvaluation(response.data);
      setActiveStep(1);
    } catch (err) {
      setError('Failed to start evaluation');
    }
  };

  const uploadAgentResult = async () => {
    try {
      await api.post(`/api/v1/evaluations/${evaluation.id}/results`, {
        agent_name: selectedAgent,
        files: [{
          name: 'result.html',
          content: uploadContent
        }]
      });
      
      setAgentResults(prev => ({
        ...prev,
        [selectedAgent]: { status: 'completed', content: uploadContent }
      }));
      
      setUploadDialog(false);
      setUploadContent('');
      setSelectedAgent(null);
    } catch (err) {
      setError('Failed to upload agent result');
    }
  };

  const runEvaluation = async () => {
    try {
      setActiveStep(2);
      await api.post(`/api/v1/evaluations/${evaluation.id}/run`);
      
      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const response = await api.get(`/api/v1/evaluations/${evaluation.id}`);
          setEvaluation(response.data);
          
          if (response.data.status === 'completed') {
            clearInterval(pollInterval);
            setActiveStep(3);
          } else if (response.data.status === 'failed') {
            clearInterval(pollInterval);
            setError('Evaluation failed');
          }
        } catch (err) {
          clearInterval(pollInterval);
          setError('Failed to check evaluation status');
        }
      }, 2000);
    } catch (err) {
      setError('Failed to run evaluation');
    }
  };

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Task Overview
            </Typography>
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h5">{task?.name}</Typography>
                <Typography color="text.secondary" sx={{ mb: 2 }}>
                  {task?.description}
                </Typography>
                <Chip label={task?.type} color="primary" />
              </CardContent>
            </Card>
            
            <Typography variant="h6" gutterBottom>
              Baseline Files
            </Typography>
            <List>
              {task?.baseline_files?.map((file, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={file.name}
                    secondary={`${(file.content.length / 1024).toFixed(2)} KB`}
                  />
                  <ListItemSecondaryAction>
                    <IconButton edge="end">
                      <Download />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
            
            <Button
              variant="contained"
              onClick={startEvaluation}
              startIcon={<PlayArrow />}
              fullWidth
              sx={{ mt: 2 }}
            >
              Start Evaluation
            </Button>
          </Box>
        );
        
      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Agent Instructions
            </Typography>
            <Alert severity="info" sx={{ mb: 3 }}>
              Run each agent manually with the provided prompts. Upload their outputs when complete.
            </Alert>
            
            <Grid container spacing={2}>
              {task?.agents?.map((agent) => (
                <Grid item xs={12} md={4} key={agent.name}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {agent.name.toUpperCase()}
                      </Typography>
                      
                      <Accordion>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                          <Typography>View Prompt</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                            {agent.prompt || 'Default prompt will be used'}
                          </Typography>
                        </AccordionDetails>
                      </Accordion>
                      
                      <Box sx={{ mt: 2 }}>
                        {agentResults[agent.name]?.status === 'completed' ? (
                          <Chip
                            icon={<CheckCircle />}
                            label="Completed"
                            color="success"
                          />
                        ) : (
                          <Button
                            variant="outlined"
                            onClick={() => {
                              setSelectedAgent(agent.name);
                              setUploadDialog(true);
                            }}
                            startIcon={<Code />}
                            fullWidth
                          >
                            Upload Result
                          </Button>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
            
            <Button
              variant="contained"
              onClick={runEvaluation}
              disabled={Object.keys(agentResults).length !== task?.agents?.length}
              fullWidth
              sx={{ mt: 3 }}
            >
              Run Evaluation
            </Button>
          </Box>
        );
        
      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Running Evaluation
            </Typography>
            <LinearProgress sx={{ mb: 2 }} />
            <Typography color="text.secondary">
              Analyzing agent outputs and generating scores...
            </Typography>
          </Box>
        );
        
      case 3:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Evaluation Complete
            </Typography>
            <Alert severity="success" sx={{ mb: 2 }}>
              Evaluation completed successfully!
            </Alert>
            <Button
              variant="contained"
              onClick={() => navigate(`/results/${evaluation.id}`)}
              fullWidth
            >
              View Results
            </Button>
          </Box>
        );
        
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <Container>
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <LinearProgress sx={{ width: '50%' }} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Run Evaluation
        </Typography>
        
        <Stepper activeStep={activeStep} sx={{ mt: 3, mb: 3 }}>
          <Step>
            <StepLabel>Setup</StepLabel>
          </Step>
          <Step>
            <StepLabel>Run Agents</StepLabel>
          </Step>
          <Step>
            <StepLabel>Evaluate</StepLabel>
          </Step>
          <Step>
            <StepLabel>Results</StepLabel>
          </Step>
        </Stepper>
        
        <Paper sx={{ p: 3 }}>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {getStepContent(activeStep)}
        </Paper>
      </Box>
      
      <Dialog open={uploadDialog} onClose={() => setUploadDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Upload {selectedAgent} Result</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={10}
            label="Agent Output"
            value={uploadContent}
            onChange={(e) => setUploadContent(e.target.value)}
            placeholder="Paste the agent's HTML/CSS output here..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialog(false)}>Cancel</Button>
          <Button
            onClick={uploadAgentResult}
            variant="contained"
            disabled={!uploadContent.trim()}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default EvaluationRunner;