import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  ExpandMore,
  Download,
  Visibility,
  TrendingUp,
  Assessment
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import api from '../services/api';

function Results() {
  const { evaluationId } = useParams();
  const [evaluation, setEvaluation] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedResult, setSelectedResult] = useState(null);
  const [detailDialog, setDetailDialog] = useState(false);

  useEffect(() => {
    loadResults();
  }, [evaluationId]);

  const loadResults = async () => {
    try {
      const [evalResponse, resultsResponse] = await Promise.all([
        api.get(`/api/v1/evaluations/${evaluationId}`),
        api.get(`/api/v1/evaluations/${evaluationId}/results`)
      ]);
      
      setEvaluation(evalResponse.data);
      setResults(resultsResponse.data);
    } catch (err) {
      setError('Failed to load results');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const getRankPosition = (result) => {
    const sortedResults = [...results].sort((a, b) => b.total_score - a.total_score);
    return sortedResults.findIndex(r => r.id === result.id) + 1;
  };

  const downloadReport = async () => {
    try {
      const response = await api.get(`/api/v1/evaluations/${evaluationId}/report`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `evaluation-${evaluationId}-report.md`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Failed to download report');
    }
  };

  const showDetails = (result) => {
    setSelectedResult(result);
    setDetailDialog(true);
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
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1">
            Evaluation Results
          </Typography>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={downloadReport}
          >
            Download Report
          </Button>
        </Box>
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        
        {/* Summary Card */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {evaluation?.task?.name}
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              {evaluation?.task?.description}
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={6} md={3}>
                <Typography variant="h4" color="primary">
                  {results.length}
                </Typography>
                <Typography variant="body2">Agents Tested</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h4" color="success.main">
                  {Math.max(...results.map(r => r.total_score), 0).toFixed(1)}
                </Typography>
                <Typography variant="body2">Best Score</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="h4" color="info.main">
                  {(results.reduce((sum, r) => sum + r.total_score, 0) / results.length || 0).toFixed(1)}
                </Typography>
                <Typography variant="body2">Average Score</Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Chip
                  label={evaluation?.status || 'Unknown'}
                  color={evaluation?.status === 'completed' ? 'success' : 'default'}
                  icon={<Assessment />}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
        
        {/* Results Table */}
        <TableContainer component={Paper} sx={{ mb: 3 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Rank</TableCell>
                <TableCell>Agent</TableCell>
                <TableCell align="right">Total Score</TableCell>
                <TableCell align="right">Pattern Consolidation</TableCell>
                <TableCell align="right">IE Hack Removal</TableCell>
                <TableCell align="right">Font Modernization</TableCell>
                <TableCell align="right">Style Cleanup</TableCell>
                <TableCell align="right">Smart Retention</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {results
                .sort((a, b) => b.total_score - a.total_score)
                .map((result) => (
                  <TableRow key={result.id} hover>
                    <TableCell>
                      <Chip
                        label={`#${getRankPosition(result)}`}
                        color={getRankPosition(result) === 1 ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="subtitle1">
                        {result.agent_name.toUpperCase()}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${result.total_score.toFixed(1)}%`}
                        color={getScoreColor(result.total_score)}
                      />
                    </TableCell>
                    <TableCell align="right">{result.scores?.pattern_consolidation?.toFixed(1) || 'N/A'}</TableCell>
                    <TableCell align="right">{result.scores?.ie_hack_removal?.toFixed(1) || 'N/A'}</TableCell>
                    <TableCell align="right">{result.scores?.font_tag_modernization?.toFixed(1) || 'N/A'}</TableCell>
                    <TableCell align="right">{result.scores?.style_block_cleanup?.toFixed(1) || 'N/A'}</TableCell>
                    <TableCell align="right">{result.scores?.smart_retention?.toFixed(1) || 'N/A'}</TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        startIcon={<Visibility />}
                        onClick={() => showDetails(result)}
                      >
                        Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              }
            </TableBody>
          </Table>
        </TableContainer>
        
        {/* Detailed Analysis */}
        <Typography variant="h5" gutterBottom>
          Analysis & Recommendations
        </Typography>
        
        {results.map((result) => (
          <Accordion key={result.id}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                <Typography variant="h6" sx={{ flexGrow: 1 }}>
                  {result.agent_name.toUpperCase()}
                </Typography>
                <Chip
                  label={`${result.total_score.toFixed(1)}%`}
                  color={getScoreColor(result.total_score)}
                  sx={{ mr: 2 }}
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Strengths
                  </Typography>
                  <ul>
                    {result.feedback?.strengths?.map((strength, index) => (
                      <li key={index}>
                        <Typography variant="body2">{strength}</Typography>
                      </li>
                    )) || <li><Typography variant="body2">No specific strengths identified</Typography></li>}
                  </ul>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Areas for Improvement
                  </Typography>
                  <ul>
                    {result.feedback?.improvements?.map((improvement, index) => (
                      <li key={index}>
                        <Typography variant="body2">{improvement}</Typography>
                      </li>
                    )) || <li><Typography variant="body2">No specific improvements suggested</Typography></li>}
                  </ul>
                </Grid>
              </Grid>
              
              {result.ai_feedback && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    AI Judge Feedback
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2">
                      {result.ai_feedback}
                    </Typography>
                  </Paper>
                </Box>
              )}
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
      
      {/* Detail Dialog */}
      <Dialog
        open={detailDialog}
        onClose={() => setDetailDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedResult?.agent_name.toUpperCase()} - Detailed Results
        </DialogTitle>
        <DialogContent>
          {selectedResult && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Score Breakdown
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                {Object.entries(selectedResult.scores || {}).map(([category, score]) => (
                  <Grid item xs={6} key={category}>
                    <Card>
                      <CardContent>
                        <Typography variant="h4" color="primary">
                          {score.toFixed(1)}
                        </Typography>
                        <Typography variant="body2">
                          {category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
              
              <Typography variant="h6" gutterBottom>
                Raw Analysis Data
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'grey.50', maxHeight: 300, overflow: 'auto' }}>
                <pre>
                  {JSON.stringify(selectedResult.analysis_data, null, 2)}
                </pre>
              </Paper>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default Results;