import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';
import { 
  PlusIcon, 
  PlayIcon, 
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon 
} from '@heroicons/react/24/outline';

const Dashboard = () => {
  const [evaluations, setEvaluations] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [evaluationsData, summaryData] = await Promise.all([
        apiService.getEvaluations({ limit: 10 }),
        apiService.getResultsSummary()
      ]);
      
      setEvaluations(evaluationsData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'badge-warning',
      active: 'badge-info',
      completed: 'badge-success',
      failed: 'badge-danger'
    };
    
    return (
      <span className={`badge ${styles[status] || 'badge-warning'}`}>
        {status}
      </span>
    );
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      case 'active':
        return <ClockIcon className="w-5 h-5 text-blue-500" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          AI Agent Evaluation Platform
        </h1>
        <p className="text-gray-600">
          Compare and evaluate AI coding agents on various tasks
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="card-content">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-blue-100 rounded-lg">
                <PlayIcon className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">
                New Evaluation
              </h3>
            </div>
            <p className="text-gray-600 mb-4">
              Start testing agents on a task
            </p>
            <Link to="/evaluation/new" className="btn-primary">
              Start Evaluation
            </Link>
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-green-100 rounded-lg">
                <PlusIcon className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">
                Create Task
              </h3>
            </div>
            <p className="text-gray-600 mb-4">
              Design a new evaluation task
            </p>
            <Link to="/tasks/new" className="btn-secondary">
              Create Task
            </Link>
          </div>
        </div>

        <div className="card">
          <div className="card-content">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-purple-100 rounded-lg">
                <ChartBarIcon className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">
                View Results
              </h3>
            </div>
            <p className="text-gray-600 mb-4">
              Browse all evaluation results
            </p>
            <Link to="/results" className="btn-secondary">
              View Results
            </Link>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="card-content">
              <div className="text-2xl font-bold text-gray-900">
                {summary.total_evaluations}
              </div>
              <div className="text-sm text-gray-600">Total Evaluations</div>
            </div>
          </div>

          <div className="card">
            <div className="card-content">
              <div className="text-2xl font-bold text-green-600">
                {summary.completed_evaluations}
              </div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
          </div>

          <div className="card">
            <div className="card-content">
              <div className="text-2xl font-bold text-blue-600">
                {summary.active_evaluations}
              </div>
              <div className="text-sm text-gray-600">Active</div>
            </div>
          </div>

          <div className="card">
            <div className="card-content">
              <div className="text-2xl font-bold text-orange-600">
                {summary.recent_evaluations}
              </div>
              <div className="text-sm text-gray-600">This Week</div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Evaluations */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-xl font-semibold text-gray-900">
            Recent Evaluations
          </h2>
        </div>
        <div className="card-content">
          {evaluations.length === 0 ? (
            <div className="text-center py-12">
              <ClockIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No evaluations yet
              </h3>
              <p className="text-gray-600 mb-4">
                Get started by creating a new evaluation
              </p>
              <Link to="/evaluation/new" className="btn-primary">
                Start Your First Evaluation
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {evaluations.map((evaluation) => (
                <div
                  key={evaluation.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    {getStatusIcon(evaluation.status)}
                    <div>
                      <h3 className="font-medium text-gray-900">
                        {evaluation.task_id}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {evaluation.agents.length} agents • Created{' '}
                        {new Date(evaluation.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    {getStatusBadge(evaluation.status)}
                    <Link
                      to={`/results/${evaluation.id}`}
                      className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      View Details
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Agent Performance Summary */}
      {summary?.agent_performance && Object.keys(summary.agent_performance).length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="text-xl font-semibold text-gray-900">
              Agent Performance
            </h2>
          </div>
          <div className="card-content">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(summary.agent_performance).map(([agent, stats]) => (
                <div key={agent} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 capitalize mb-2">
                    {agent}
                  </h3>
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Average Score:</span>
                      <span className="font-medium">{stats.average_score}/100</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Evaluations:</span>
                      <span className="font-medium">{stats.total_evaluations}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;