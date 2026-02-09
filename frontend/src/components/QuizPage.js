import React, { useState, useEffect } from 'react';
import './QuizPage.css';

const API_BASE = process.env.REACT_APP_API_BASE || '';

function QuizPage({ questions, quizId, onQuizSubmitted, onReset }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [answeredCount, setAnsweredCount] = useState(0);

  useEffect(() => {
    const count = Object.keys(answers).length;
    setAnsweredCount(count);
  }, [answers]);

  const handleAnswerSelect = (letter) => {
    const newAnswers = { ...answers, [currentIndex]: letter };
    setAnswers(newAnswers);
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handleSubmit = async () => {
    if (Object.keys(answers).length === 0) {
      alert('Please answer at least one question.');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/submit-quiz`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quiz_id: quizId, answers }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Submit failed');

      onQuizSubmitted(data);
    } catch (err) {
      alert(String(err));
    }
  };

  if (questions.length === 0) {
    return <div>No questions available</div>;
  }

  const currentQuestion = questions[currentIndex];
  const progress = ((currentIndex + 1) / questions.length) * 100;
  const isLastQuestion = currentIndex === questions.length - 1;
  const selectedAnswer = answers[currentIndex];

  return (
    <div className="quiz-card">
      <div className="quiz-header">
        <div className="progress-info">
          <span className="question-counter">
            Question {currentIndex + 1} of {questions.length}
          </span>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
        <div className="answered-counter">
          <span>{answeredCount}</span> answered
        </div>
      </div>

      <div className="question-container">
        <div className="question-text">{currentQuestion.question}</div>

        <div className="options-container">
          {['A', 'B', 'C', 'D'].map((letter, idx) => {
            const option = currentQuestion.options[letter] || currentQuestion.options[idx];
            const isSelected = selectedAnswer === letter;

            return (
              <div
                key={letter}
                className={`option-item ${isSelected ? 'selected' : ''}`}
                onClick={() => handleAnswerSelect(letter)}
              >
                <input
                  type="radio"
                  name={`question-${currentIndex}`}
                  value={letter}
                  checked={isSelected}
                  onChange={() => handleAnswerSelect(letter)}
                />
                <label>
                  {letter}. {option}
                </label>
              </div>
            );
          })}
        </div>
      </div>

      <div className="quiz-actions">
        <button
          className="btn-nav"
          onClick={handlePrevious}
          disabled={currentIndex === 0}
        >
          ← Previous
        </button>
        {!isLastQuestion ? (
          <button className="btn-nav" onClick={handleNext}>
            Next →
          </button>
        ) : (
          <button className="btn-submit" onClick={handleSubmit}>
            Submit Quiz
          </button>
        )}
      </div>
    </div>
  );
}

export default QuizPage;
