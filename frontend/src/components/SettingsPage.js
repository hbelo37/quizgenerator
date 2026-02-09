import React, { useState } from 'react';
import './SettingsPage.css';

const API_BASE = process.env.REACT_APP_API_BASE || '';

function SettingsPage({ onQuizGenerated }) {
  const [sourceType, setSourceType] = useState('url');
  const [url, setUrl] = useState('');
  const [pdfFile, setPdfFile] = useState(null);
  const [numQuestions, setNumQuestions] = useState(10);
  const [difficulty, setDifficulty] = useState('medium');
  const [status, setStatus] = useState({ text: '', type: '' });
  const [isGenerating, setIsGenerating] = useState(false);

  const extractContent = async () => {
    if (sourceType === 'url' && !url.trim()) {
      setStatus({ text: 'Please enter a URL', type: 'error' });
      return null;
    }
    if (sourceType === 'pdf' && !pdfFile) {
      setStatus({ text: 'Please choose a PDF file', type: 'error' });
      return null;
    }

    setStatus({ text: `Extracting text from ${sourceType === 'url' ? 'URL' : 'PDF'}...`, type: 'info' });

    try {
      let res;
      if (sourceType === 'url') {
        res = await fetch(`${API_BASE}/upload/url`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url }),
        });
      } else {
        const formData = new FormData();
        formData.append('file', pdfFile);
        res = await fetch(`${API_BASE}/upload/pdf`, {
          method: 'POST',
          body: formData,
        });
      }

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Extraction failed');

      return data.content;
    } catch (err) {
      setStatus({ text: String(err), type: 'error' });
      return null;
    }
  };

  const handleGenerate = async () => {
    // Auto-extract content first
    const content = await extractContent();
    if (!content) return;

    setIsGenerating(true);
    setStatus({ text: 'Generating quiz with local LLM... this may take a minute.', type: 'info' });

    try {
      const res = await fetch(`${API_BASE}/generate-quiz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          source_type: 'text',
          source_label: null,
          difficulty,
          num_questions: numQuestions,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Quiz generation failed');

      onQuizGenerated(data.quiz_id, data.questions);
    } catch (err) {
      setStatus({ text: `${String(err)}. Ensure Ollama is running.`, type: 'error' });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    setPdfFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === 'application/pdf') {
      setPdfFile(file);
    }
  };

  return (
    <div className="settings-card">
      <div className="header-text">
        <p className="subtitle">or upload a PDF and let AI do the rest</p>
      </div>

      {/* Content Source */}
      <div className="section-group">
        <label className="section-label">Content Source</label>
        <div className="button-group">
          <button
            className={`source-btn ${sourceType === 'url' ? 'active' : ''}`}
            onClick={() => setSourceType('url')}
          >
            <span className="icon">🔗</span>
            Article URL
          </button>
          <button
            className={`source-btn ${sourceType === 'pdf' ? 'active' : ''}`}
            onClick={() => setSourceType('pdf')}
          >
            <span className="icon">📄</span>
            Upload PDF
          </button>
        </div>

        {/* URL Input */}
        {sourceType === 'url' && (
          <div className="input-group">
            <div className="input-wrapper">
              <span className="input-icon">🔗</span>
              <input
                type="url"
                placeholder="https://example.com/article"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="url-input"
              />
            </div>
          </div>
        )}

        {/* PDF Upload */}
        {sourceType === 'pdf' && (
          <div className="input-group">
            <div
              className="dropzone"
              onClick={() => document.getElementById('pdf-file-input').click()}
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
            >
              <span className="drop-icon">📄</span>
              <p>Click to choose a PDF, or drop it here</p>
              <input
                id="pdf-file-input"
                type="file"
                accept="application/pdf"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
            </div>
            {pdfFile && <p className="filename">✓ {pdfFile.name}</p>}
          </div>
        )}

        {status.text && (
          <p className={`status-text ${status.type}`}>{status.text}</p>
        )}
      </div>

      {/* Number of Questions */}
      <div className="section-group">
        <label className="section-label">Number of Questions</label>
        <div className="button-group">
          {[5, 10, 15, 20].map((num) => (
            <button
              key={num}
              className={`qty-btn ${numQuestions === num ? 'active' : ''}`}
              onClick={() => setNumQuestions(num)}
            >
              {num}
            </button>
          ))}
        </div>
      </div>

      {/* Difficulty Level */}
      <div className="section-group">
        <label className="section-label">Difficulty Level</label>
        <div className="difficulty-group">
          <button
            className={`difficulty-btn ${difficulty === 'easy' ? 'active' : ''}`}
            onClick={() => setDifficulty('easy')}
          >
            <div className="difficulty-title">Easy</div>
            <div className="difficulty-desc">Straightforward recall questions</div>
          </button>
          <button
            className={`difficulty-btn ${difficulty === 'medium' ? 'active' : ''}`}
            onClick={() => setDifficulty('medium')}
          >
            <div className="difficulty-title">Medium</div>
            <div className="difficulty-desc">Requires understanding concepts</div>
          </button>
          <button
            className={`difficulty-btn ${difficulty === 'hard' ? 'active' : ''}`}
            onClick={() => setDifficulty('hard')}
          >
            <div className="difficulty-title">Hard</div>
            <div className="difficulty-desc">Analytical & tricky questions</div>
          </button>
        </div>
      </div>

      {/* Generate Button */}
      <button
        className="btn-generate"
        onClick={handleGenerate}
        disabled={isGenerating}
      >
        <span className="sparkle">✨</span>
        Generate Quiz
      </button>

      <p className="footer-note">
        Questions are generated using AI based on the article content
      </p>
    </div>
  );
}

export default SettingsPage;
