import React, { useState, useEffect } from 'react';
import './ResultsPage.css';

function ResultsPage({ quizData, quizId, onReset }) {
  const [shareLink, setShareLink] = useState('');

  useEffect(() => {
    if (quizId) {
      const url = new URL(window.location.href);
      url.searchParams.set('quiz_id', quizId);
      setShareLink(url.toString());
    }
  }, [quizId]);

  const handleCopy = () => {
    navigator.clipboard.writeText(shareLink).then(() => {
      const btn = document.getElementById('copy-btn');
      const originalText = btn.textContent;
      btn.textContent = 'Copied!';
      setTimeout(() => {
        btn.textContent = originalText;
      }, 2000);
    });
  };

  if (!quizData) {
    return <div>No results available</div>;
  }

  const percentage = Math.round(quizData.percentage);
  const wrongResults = (quizData.results || []).filter((item) => !item.is_correct);
  let message = '';
  if (percentage >= 90) message = '🎉 Excellent work!';
  else if (percentage >= 70) message = '👍 Great job!';
  else if (percentage >= 50) message = '📚 Good effort!';
  else message = '💪 Keep practicing!';

  return (
    <div className="results-card">
      <h2 className="results-title">Quiz Results</h2>

      <div className="score-display">
        <div className="score-circle">
          <span>{percentage}%</span>
        </div>
        <div className="score-info">
          <p className="score-text">Score: {quizData.score} / {quizData.total}</p>
          <p className="score-message">{message}</p>
        </div>
      </div>

      <div className="share-section">
        <label className="section-label">Share this quiz</label>
        <div className="share-row">
          <input type="text" value={shareLink} readOnly />
          <button id="copy-btn" className="btn-copy" onClick={handleCopy}>
            Copy
          </button>
        </div>
      </div>

      {wrongResults.length > 0 && (
        <div className="review-section">
          <label className="section-label">Review Incorrect Answers</label>
          <div className="review-list">
            {wrongResults.map((item) => (
              <div key={item.index} className="review-item">
                <p className="review-question">
                  Q{item.index + 1}. {item.question}
                </p>
                <p className="review-line wrong">
                  Your answer: {item.selected_answer ? `${item.selected_answer}. ${item.selected_option || ''}` : 'Not answered'}
                </p>
                <p className="review-line correct">
                  Correct answer: {item.correct_answer}. {item.correct_option}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <button className="btn-generate" onClick={onReset}>
        Create Another Quiz
      </button>
    </div>
  );
}

export default ResultsPage;
