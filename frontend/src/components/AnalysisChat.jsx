import { useState, useRef, useEffect } from 'react';
import { analysisAPI } from '../services/api';
import MarkdownRenderer from './MarkdownRenderer';

const AnalysisChat = ({ profile, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [targetRole, setTargetRole] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !targetRole.trim() || loading) return;

    const userMessage = {
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    const currentInput = input;
    const currentTargetRole = targetRole;
    setInput('');

    try {
      const requestData = {
        user_profile_id: profile.id || profile.profile_id,
        user_query: currentInput,
        target_role: {
          role_name: currentTargetRole,
          description: '',
          skill_framework: '',
        },
        use_rag: true,
      };

      const response = await analysisAPI.analyze(requestData);

      const assistantMessage = {
        type: 'assistant',
        content: response.analysis_summary || 'Analysis completed',
        report: response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'error',
        content: error.response?.data?.detail || error.message || 'Failed to analyze skills',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Skill Gap Analysis</h2>
          <p className="text-sm text-gray-600">Analyzing: {profile.name}</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Target Role Input */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <input
          type="text"
          value={targetRole}
          onChange={(e) => setTargetRole(e.target.value)}
          placeholder="Enter target role (e.g., Senior Architect, Data Scientist)"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
        />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg mb-2">Start your skill gap analysis</p>
            <p className="text-sm">Enter your target role above and describe your career goals</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl rounded-lg px-4 py-3 ${
                message.type === 'user'
                  ? 'bg-primary-600 text-white'
                  : message.type === 'error'
                  ? 'bg-red-50 text-red-700 border border-red-200'
                  : 'bg-white border border-gray-200 shadow-sm'
              }`}
            >
              {message.type === 'assistant' ? (
                <div className="prose-container">
                  <MarkdownRenderer content={message.content} />
                </div>
              ) : (
                <p className="whitespace-pre-wrap">{message.content}</p>
              )}
              {message.report && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Gap Score</p>
                      <p className="font-semibold text-lg">{message.report.overall_gap_score?.toFixed(2) || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Skills Met</p>
                      <p className="font-semibold">{message.report.skills_met?.length || 0}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Skills Missing</p>
                      <p className="font-semibold">{message.report.skills_missing?.length || 0}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-lg px-4 py-3 shadow-sm">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                <span className="text-gray-600">Analyzing your skills...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your career goals and what you want to achieve..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            rows="2"
            disabled={loading || !targetRole.trim()}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim() || !targetRole.trim()}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
};

export default AnalysisChat;

