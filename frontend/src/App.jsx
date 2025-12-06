import React, { useState, useRef } from 'react';
import axios from 'axios';
import {
  Mic,
  Send,
  Download,
  Settings,
  AlertCircle,
  CheckCircle,
  Clock,
  FileText,
  Share2,
  Loader
} from 'lucide-react';
import './index.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export default function App() {
  const [transcript, setTranscript] = useState('');
  const [meetingPlatform, setMeetingPlatform] = useState('zoom');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('input');
  const [recordingActive, setRecordingActive] = useState(false);
  const mediaStreamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  // Analyze transcript with AI
  const handleAnalyze = async () => {
    if (!transcript.trim()) {
      setError('Please enter a transcript or record audio');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_URL}/api/analyze`, {
        transcript,
        meeting_platform: meetingPlatform,
        meeting_id: `meeting_${Date.now()}`
      });

      console.log('Analysis response:', response.data);
      // Handle both response.data.analysis and response.data directly
      const analysisData = response.data.analysis || response.data;
      setAnalysis(analysisData);
      setActiveTab('results');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze transcript. Please check the API connection.');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Start recording audio
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      chunksRef.current = [];

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        chunksRef.current.push(event.data);
      };

      mediaRecorder.onstart = () => {
        setRecordingActive(true);
        setError('');
      };

      mediaRecorder.onstop = async () => {
        setRecordingActive(false);
        if (chunksRef.current.length === 0) {
          setError('No audio recorded. Please try again.');
          return;
        }
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        console.log('Audio blob created, size:', audioBlob.size);
        await handleTranscription(audioBlob);
      };

      mediaRecorder.start();
    } catch (err) {
      setError('Microphone access denied. Please enable microphone permissions.');
      console.error('Recording error:', err);
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && recordingActive) {
      mediaRecorderRef.current.stop();
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
    }
  };

  // Handle transcription after recording stops
  const handleTranscription = async (audioBlob) => {
    try {
      setLoading(true);
      setError('');
      
      console.log('Starting transcription, audio blob size:', audioBlob.size);
      
      const formData = new FormData();
      formData.append('file', audioBlob, 'audio.webm');
      
      console.log('Sending to:', `${API_URL}/api/transcribe`);
      
      const response = await axios.post(`${API_URL}/api/transcribe`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      console.log('Transcription response:', response.data);
      
      if (response.data && response.data.transcript) {
        setTranscript(response.data.transcript);
        setError('');
      } else {
        setError('No transcript returned from server');
      }
    } catch (err) {
      console.error('Transcription error full:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to transcribe audio. Please try again.';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Export analysis
  const handleExport = async (format) => {
    if (!analysis) return;

    try {
      const response = await axios.post(`${API_URL}/export`, {
        analysis,
        export_to: format
      });

      if (format === 'pdf' || format === 'csv') {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `meeting-notes-${Date.now()}.${format}`);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
      }
    } catch (err) {
      setError('Export failed. Please try again.');
      console.error('Export error:', err);
    }
  };

  // Send to Email
  const handleSendEmail = async () => {
    if (!analysis) return;

    const email = prompt('Enter email address:');
    if (!email) return;

    try {
      setLoading(true);
      await axios.post(`${API_URL}/api/notify`, {
        analysis,
        email
      });
      alert('Meeting minutes sent to email successfully!');
    } catch (err) {
      setError('Failed to send email: ' + (err.response?.data?.detail || err.message));
      console.error('Email error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Send to Slack
  const handleSendSlack = async () => {
    if (!analysis) return;

    const webhook = prompt('Enter Slack webhook URL:');
    if (!webhook) return;

    try {
      setLoading(true);
      await axios.post(`${API_URL}/api/notify`, {
        analysis,
        slack_webhook: webhook
      });
      alert('Meeting minutes sent to Slack successfully!');
    } catch (err) {
      setError('Failed to send to Slack: ' + (err.response?.data?.detail || err.message));
      console.error('Slack error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Export to Jira
  const handleExportJira = async () => {
    if (!analysis || !analysis.tasks || analysis.tasks.length === 0) {
      alert('No tasks to export to Jira');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/api/export/jira`, {
        analysis
      });
      alert(response.data.message || 'Tasks exported to Jira successfully!');
    } catch (err) {
      setError('Failed to export to Jira: ' + (err.response?.data?.detail || err.message));
      console.error('Jira export error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Export to Trello
  const handleExportTrello = async () => {
    if (!analysis || !analysis.tasks || analysis.tasks.length === 0) {
      alert('No tasks to export to Trello');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/api/export/trello`, {
        analysis
      });
      alert(response.data.message || 'Tasks exported to Trello successfully!');
    } catch (err) {
      setError('Failed to export to Trello: ' + (err.response?.data?.detail || err.message));
      console.error('Trello export error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <FileText className="logo-icon" />
            <div className="logo-text">
              <h1>Meeting Notes Agent</h1>
              <p>AI-powered meeting analysis and task extraction</p>
            </div>
          </div>
          <Settings className="settings-icon" />
        </div>
      </header>

      {/* Error Alert */}
      {error && (
        <div className="error-alert">
          <AlertCircle size={20} />
          <span>{error}</span>
          <button onClick={() => setError('')}>×</button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 'input' ? 'active' : ''}`}
          onClick={() => setActiveTab('input')}
        >
          Input
        </button>
        <button
          className={`tab-button ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveTab('results')}
          disabled={!analysis}
        >
          Results
        </button>
      </div>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'input' ? (
          <div className="input-section">
            <div className="form-group">
              <label>Meeting Platform</label>
              <select
                value={meetingPlatform}
                onChange={(e) => setMeetingPlatform(e.target.value)}
              >
                <option value="zoom">Zoom</option>
                <option value="teams">Microsoft Teams</option>
                <option value="google_meet">Google Meet</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label>Meeting Transcript</label>
              <textarea
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                placeholder="Paste your meeting transcript here or record audio..."
                className="transcript-input"
              />
            </div>

            <div className="button-group">
              <button
                className={`btn btn-recording ${recordingActive ? 'recording' : ''}`}
                onClick={recordingActive ? stopRecording : startRecording}
              >
                <Mic size={18} />
                {recordingActive ? 'Stop Recording' : 'Start Recording'}
              </button>
              <button
                className="btn btn-primary"
                onClick={handleAnalyze}
                disabled={loading || !transcript.trim()}
              >
                {loading ? (
                  <>
                    <Loader size={18} className="spinner" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Send size={18} />
                    Analyze Meeting
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="results-section">
            {analysis && (
              <>
                {/* Summary */}
                <div className="result-card summary-card">
                  <h2>Meeting Summary</h2>
                  <p>{analysis.summary}</p>
                </div>

                {/* Tasks */}
                {analysis.tasks && analysis.tasks.length > 0 && (
                  <div className="result-card">
                    <h3>
                      <CheckCircle size={20} />
                      Tasks ({analysis.tasks.length})
                    </h3>
                    <div className="task-list">
                      {analysis.tasks.map((task, idx) => (
                        <div key={idx} className="task-item">
                          <div className="task-header">
                            <h4>{task.title}</h4>
                            <span className={`priority ${task.priority.toLowerCase()}`}>
                              {task.priority}
                            </span>
                          </div>
                          <div className="task-details">
                            <span><strong>Assignee:</strong> {task.assignee}</span>
                            <span><strong>Due:</strong> {task.due_date}</span>
                          </div>
                          {task.description && (
                            <p className="task-description">{task.description}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Decisions */}
                {analysis.decisions && analysis.decisions.length > 0 && (
                  <div className="result-card">
                    <h3>
                      <CheckCircle size={20} />
                      Decisions ({analysis.decisions.length})
                    </h3>
                    <ul className="decision-list">
                      {analysis.decisions.map((decision, idx) => (
                        <li key={idx}>{decision}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Risks */}
                {analysis.risks && analysis.risks.length > 0 && (
                  <div className="result-card">
                    <h3>
                      <AlertCircle size={20} />
                      Risks ({analysis.risks.length})
                    </h3>
                    <ul className="risk-list">
                      {analysis.risks.map((risk, idx) => (
                        <li key={idx}>{risk}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Follow-ups */}
                {analysis.follow_ups && analysis.follow_ups.length > 0 && (
                  <div className="result-card">
                    <h3>
                      <Clock size={20} />
                      Follow-ups ({analysis.follow_ups.length})
                    </h3>
                    <ul className="followup-list">
                      {analysis.follow_ups.map((followup, idx) => (
                        <li key={idx}>{followup}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Export & Share */}
                <div className="result-card action-card">
                  <h3>Share Meeting Minutes & Export Tasks</h3>
                  <div className="action-buttons">
                    <button className="btn btn-secondary" onClick={handleSendEmail} disabled={loading}>
                      <Share2 size={18} />
                      Email Minutes
                    </button>
                    <button className="btn btn-secondary" onClick={handleSendSlack} disabled={loading}>
                      <Share2 size={18} />
                      Slack Minutes
                    </button>
                    {analysis.tasks && analysis.tasks.length > 0 && (
                      <>
                        <button className="btn btn-secondary" onClick={handleExportJira} disabled={loading}>
                          <Download size={18} />
                          Export to Jira
                        </button>
                        <button className="btn btn-secondary" onClick={handleExportTrello} disabled={loading}>
                          <Download size={18} />
                          Export to Trello
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>&copy; 2025 Meeting Notes Agent. Built with AI.</p>
      </footer>
    </div>
  );
}
