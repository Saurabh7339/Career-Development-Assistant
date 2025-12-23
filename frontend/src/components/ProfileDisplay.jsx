import { useEffect, useState } from 'react';
import { profileAPI, analysisAPI } from '../services/api';
import MarkdownRenderer from './MarkdownRenderer';

const ProfileDisplay = ({ profileId, onAnalyze }) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [analysisQuery, setAnalysisQuery] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);
  const [showSkillsModal, setShowSkillsModal] = useState(false);
  const [modalSkills, setModalSkills] = useState([]);
  const [modalTitle, setModalTitle] = useState('');

  useEffect(() => {
    if (profileId) {
      loadProfile();
    } else {
      setLoading(false);
      setError('No profile ID provided');
    }
  }, [profileId]);

  const loadProfile = async () => {
    if (!profileId) {
      setLoading(false);
      setError('No profile ID provided');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await profileAPI.get(profileId);
      setProfile(data);
    } catch (err) {
      console.error('Error loading profile:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  if (!profile) {
    return null;
  }

  const handleAnalyze = async () => {
    if (!profileId) {
      setAnalysisError('Profile ID is missing');
      return;
    }

    setAnalyzing(true);
    setAnalysisError(null);
    setAnalysisResult(null);

    try {
      const requestData = {
        user_profile_id: profileId,
        user_query: analysisQuery || `I want to transition to ${targetRole || 'a new role'}.`,
        target_role: {
          role_name: targetRole || 'Target Role',
          description: '',
          skill_framework: '',
        },
        use_rag: true,
      };

      const response = await analysisAPI.analyze(requestData);
      setAnalysisResult(response);
      
      // Extract skills_met and skills_missing from response
      // These should already be in the response structure
    } catch (err) {
      setAnalysisError(err.response?.data?.detail || err.message || 'Failed to analyze skills');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleShowSkills = (skills, title) => {
    if (!skills || skills.length === 0) {
      alert(`No ${title.toLowerCase()} found.`);
      return;
    }
    setModalSkills(skills);
    setModalTitle(title);
    setShowSkillsModal(true);
  };

  const handleCloseModal = () => {
    setShowSkillsModal(false);
    setModalSkills([]);
    setModalTitle('');
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Side - Profile Details */}
        <div className="lg:col-span-2">
          <div className="p-6 bg-white rounded-lg shadow-lg">
            <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-3xl font-bold text-gray-800">{profile.name}</h2>
          <p className="text-lg text-gray-600 mt-1">{profile.current_role}</p>
          {profile.experience_years > 0 && (
            <p className="text-sm text-gray-500 mt-1">
              {profile.experience_years} years of experience
            </p>
          )}
        </div>
        {onAnalyze && (
          <button
            onClick={() => onAnalyze(profile)}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-medium"
          >
            Analyze Skills
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Skills */}
        <div>
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Skills</h3>
          {profile.skills && profile.skills.length > 0 ? (
            <div className="space-y-2">
              {profile.skills.map((skill, index) => (
                <div
                  key={index}
                  className="bg-gray-50 p-3 rounded-lg border border-gray-200"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-gray-800">{skill.name}</p>
                      <p className="text-sm text-gray-600 mt-1">
                        Proficiency: <span className="capitalize">{skill.proficiency}</span>
                        {skill.years_experience > 0 && (
                          <span className="ml-2">({skill.years_experience} years)</span>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 italic">No skills listed</p>
          )}
        </div>

        {/* Certifications */}
        <div>
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Certifications</h3>
          {profile.certifications && profile.certifications.length > 0 ? (
            <div className="space-y-2">
              {profile.certifications.map((cert, index) => (
                <div
                  key={index}
                  className="bg-gray-50 p-3 rounded-lg border border-gray-200"
                >
                  <p className="text-gray-800">{cert}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 italic">No certifications listed</p>
          )}
        </div>
      </div>

      {/* Analysis Section Toggle */}
      <div className="mt-8 pt-8 border-t border-gray-200">
        <button
          type="button"
          onClick={() => setShowAnalysis(!showAnalysis)}
          className="w-full flex items-center justify-between px-6 py-4 bg-primary-50 hover:bg-primary-100 border-2 border-primary-200 rounded-lg transition shadow-sm"
        >
          <span className="font-semibold text-primary-800 text-lg">
            📊 Analyze your skills for your goals or objectives
          </span>
          <svg
            className={`w-6 h-6 text-primary-600 transition-transform ${showAnalysis ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {/* Analysis Form */}
        {showAnalysis && (
          <div className="mt-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Role *
              </label>
              <input
                type="text"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="e.g., Senior Architect, Data Scientist, etc."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Goals/Objectives (Optional)
              </label>
              <textarea
                value={analysisQuery}
                onChange={(e) => setAnalysisQuery(e.target.value)}
                placeholder="Describe your career goals, what you want to achieve, or any specific questions..."
                rows="3"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              />
            </div>

            <button
              type="button"
              onClick={handleAnalyze}
              disabled={analyzing || !targetRole.trim()}
              className={`w-full px-6 py-3 rounded-lg transition font-medium ${
                analyzing || !targetRole.trim()
                  ? 'bg-gray-400 text-white cursor-not-allowed opacity-60'
                  : 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer shadow-md hover:shadow-lg'
              }`}
              style={{
                minHeight: '48px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              {analyzing ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="text-white font-semibold">Analyzing...</span>
                </span>
              ) : (
                <span className="flex items-center justify-center text-white font-semibold">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                  Analyze Skills
                </span>
              )}
            </button>
            {!targetRole.trim() && (
              <p className="text-sm text-gray-500 text-center mt-2">
                Please enter a target role to enable analysis
              </p>
            )}

            {analysisError && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {analysisError}
              </div>
            )}

            {analysisResult && (
              <div className="mt-6 p-6 bg-gray-50 rounded-lg border border-gray-200">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-xl font-semibold text-gray-800">Analysis Results</h3>
                  {analysisResult.overall_gap_score !== undefined && (
                    <div className="text-right">
                      <p className="text-sm text-gray-600">Gap Score</p>
                      <p className="text-2xl font-bold text-primary-600">
                        {analysisResult.overall_gap_score.toFixed(2)}
                      </p>
                    </div>
                  )}
                </div>
                
                {analysisResult.analysis_summary && (
                  <div className="prose prose-lg max-w-none">
                    <MarkdownRenderer content={analysisResult.analysis_summary} />
                  </div>
                )}

                {/* Additional Stats */}
                {(analysisResult.skills_met?.length > 0 || 
                  analysisResult.skills_missing?.length > 0 || 
                  analysisResult.skills_weak?.length > 0) && (
                  <div className="mt-6 grid grid-cols-3 gap-4 pt-6 border-t border-gray-300">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-green-600">
                        {analysisResult.skills_met?.length || 0}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">Skills Met</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-yellow-600">
                        {analysisResult.skills_weak?.length || 0}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">Skills Weak</p>
                    </div>
                    <div className="text-center">
                      <p className="text-2xl font-bold text-red-600">
                        {analysisResult.skills_missing?.length || 0}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">Skills Missing</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
          </div>
        </div>

        {/* Right Side - Skills Summary */}
        {analysisResult && (
          <div className="lg:col-span-1">
            <div className="p-6 bg-white rounded-lg shadow-lg sticky top-4">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Skills Summary</h3>
              
              {/* Skills Met */}
              <div className="mb-4">
                <button
                  onClick={() => handleShowSkills(analysisResult.skills_met, 'Skills Met')}
                  className="w-full px-4 py-3 bg-green-50 hover:bg-green-100 border-2 border-green-200 rounded-lg transition text-left"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-green-800">Skills Met</p>
                      <p className="text-sm text-green-600">
                        {analysisResult.skills_met?.length || 0} skills
                      </p>
                    </div>
                    <div className="text-2xl font-bold text-green-600">
                      {analysisResult.skills_met?.length || 0}
                    </div>
                  </div>
                </button>
              </div>

              {/* Skills Missing */}
              <div className="mb-4">
                <button
                  onClick={() => handleShowSkills(analysisResult.skills_missing, 'Skills Missing')}
                  className="w-full px-4 py-3 bg-red-50 hover:bg-red-100 border-2 border-red-200 rounded-lg transition text-left"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-red-800">Skills Missing</p>
                      <p className="text-sm text-red-600">
                        {analysisResult.skills_missing?.length || 0} skills
                      </p>
                    </div>
                    <div className="text-2xl font-bold text-red-600">
                      {analysisResult.skills_missing?.length || 0}
                    </div>
                  </div>
                </button>
              </div>

              {/* Skills Weak */}
              {analysisResult.skills_weak && analysisResult.skills_weak.length > 0 && (
                <div className="mb-4">
                  <button
                    onClick={() => handleShowSkills(analysisResult.skills_weak, 'Skills Weak')}
                    className="w-full px-4 py-3 bg-yellow-50 hover:bg-yellow-100 border-2 border-yellow-200 rounded-lg transition text-left"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-yellow-800">Skills Weak</p>
                        <p className="text-sm text-yellow-600">
                          {analysisResult.skills_weak.length} skills
                        </p>
                      </div>
                      <div className="text-2xl font-bold text-yellow-600">
                        {analysisResult.skills_weak.length}
                      </div>
                    </div>
                  </button>
                </div>
              )}

              {/* Gap Score */}
              {analysisResult.overall_gap_score !== undefined && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-600 mb-1">Overall Gap Score</p>
                  <p className="text-3xl font-bold text-primary-600">
                    {analysisResult.overall_gap_score.toFixed(2)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">out of 100</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Skills Modal */}
      {showSkillsModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={handleCloseModal}
        >
          <div 
            className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-800">{modalTitle}</h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-500 hover:text-gray-700 transition"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {modalSkills.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No skills found</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {modalSkills.map((skill, index) => (
                    <div
                      key={index}
                      className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition bg-white"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <h3 className="text-lg font-semibold text-gray-800">{skill.skill_name}</h3>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          skill.status === 'met' ? 'bg-green-100 text-green-800' :
                          skill.status === 'missing' ? 'bg-red-100 text-red-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {skill.status}
                        </span>
                      </div>

                      <div className="space-y-2">
                        {/* Proficiency Levels */}
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Current:</span>
                          <span className="font-medium text-gray-800 capitalize">
                            {skill.current_proficiency || 'N/A'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Required:</span>
                          <span className="font-medium text-gray-800 capitalize">
                            {skill.required_proficiency || 'N/A'}
                          </span>
                        </div>

                        {/* Gap Severity */}
                        {skill.gap_severity && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <div className="flex items-center justify-between">
                              <span className="text-sm text-gray-600">Gap Severity:</span>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                skill.gap_severity === 'high' ? 'bg-red-100 text-red-800' :
                                skill.gap_severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                'bg-green-100 text-green-800'
                              }`}>
                                {skill.gap_severity}
                              </span>
                            </div>
                          </div>
                        )}

                        {/* Recommendation */}
                        {skill.recommendation && (
                          <div className="mt-3 pt-3 border-t border-gray-200">
                            <p className="text-sm font-medium text-gray-700 mb-1">Recommendation:</p>
                            <p className="text-sm text-gray-600">{skill.recommendation}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
              <button
                onClick={handleCloseModal}
                className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfileDisplay;

