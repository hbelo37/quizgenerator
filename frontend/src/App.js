import React, { useState, useEffect } from 'react';
import './App.css';
import SettingsPage from './components/SettingsPage';
import QuizPage from './components/QuizPage';
import ResultsPage from './components/ResultsPage';
import { API_BASE } from './utils/apiBase';

function App() {
  const [step, setStep] = useState('settings'); // 'settings', 'quiz', 'results'
  const [currentQuizId, setCurrentQuizId] = useState('');
  const [currentQuestions, setCurrentQuestions] = useState([]);
  const [quizData, setQuizData] = useState(null);

  useEffect(() => {
    // Check for shared quiz in URL
    const urlParams = new URLSearchParams(window.location.search);
    const quizId = urlParams.get('quiz_id');
    if (quizId) {
      loadSharedQuiz(quizId);
    }
  }, []);

  const loadSharedQuiz = async (quizId) => {
    try {
      const res = await fetch(`${API_BASE}/quiz/${quizId}`);
      const data = await res.json();
      if (res.ok) {
        setCurrentQuizId(data.quiz_id);
        setCurrentQuestions(data.questions);
        setStep('quiz');
      }
    } catch (err) {
      console.error('Failed to load shared quiz:', err);
    }
  };

  const handleQuizGenerated = (quizId, questions) => {
    setCurrentQuizId(quizId);
    setCurrentQuestions(questions);
    setStep('quiz');
  };

  const handleQuizSubmitted = (results) => {
    setQuizData(results);
    setStep('results');
  };

  const handleReset = () => {
    setStep('settings');
    setCurrentQuizId('');
    setCurrentQuestions([]);
    setQuizData(null);
    window.history.replaceState({}, '', window.location.pathname);
  };

  return (
    <div className="app-container">
      {step === 'settings' && (
        <SettingsPage
          onQuizGenerated={handleQuizGenerated}
        />
      )}
      {step === 'quiz' && (
        <QuizPage
          questions={currentQuestions}
          quizId={currentQuizId}
          onQuizSubmitted={handleQuizSubmitted}
          onReset={handleReset}
        />
      )}
      {step === 'results' && (
        <ResultsPage
          quizData={quizData}
          quizId={currentQuizId}
          onReset={handleReset}
        />
      )}
    </div>
  );
}

export default App;
