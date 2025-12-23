import { useState, useEffect } from 'react';
import ProfileList from './components/ProfileList';
import ProfileForm from './components/ProfileForm';
import ProfileDisplay from './components/ProfileDisplay';
import AnalysisChat from './components/AnalysisChat';
import { healthCheck } from './services/api';

function App() {
  const [view, setView] = useState('list'); // 'list', 'create', 'profile', 'chat'
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [apiStatus, setApiStatus] = useState('checking');

  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      await healthCheck();
      setApiStatus('connected');
    } catch (error) {
      setApiStatus('disconnected');
    }
  };

  const handleCreateProfile = () => {
    setView('create');
  };

  const handleProfileCreated = (result) => {
    setView('list');
    // Optionally reload profiles or navigate to the new profile
  };

  const handleSelectProfile = (profile) => {
    // Ensure we have the profile ID
    const profileId = profile.id || profile.profile_id;
    if (!profileId) {
      console.error('Profile missing ID:', profile);
      alert('Error: Profile ID not found. Please try again.');
      return;
    }
    setSelectedProfile({ ...profile, id: profileId });
    setView('profile');
  };

  const handleAnalyze = (profile) => {
    setSelectedProfile(profile);
    setView('chat');
  };

  const handleBackToList = () => {
    setView('list');
    setSelectedProfile(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">Skill Gap Analyzer</h1>
              <p className="text-sm text-gray-600">AI-Powered Career Development Assistant</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div
                  className={`w-3 h-3 rounded-full ${
                    apiStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'
                  }`}
                ></div>
                <span className="text-sm text-gray-600">
                  {apiStatus === 'connected' ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              {view !== 'list' && (
                <button
                  onClick={handleBackToList}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition"
                >
                  Back to Profiles
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8">
        {view === 'list' && (
          <ProfileList
            onSelectProfile={handleSelectProfile}
            onCreateNew={handleCreateProfile}
          />
        )}

        {view === 'create' && (
          <ProfileForm
            onSuccess={handleProfileCreated}
            onCancel={handleBackToList}
          />
        )}

        {view === 'profile' && selectedProfile && (
          <ProfileDisplay
            profileId={selectedProfile.id || selectedProfile.profile_id || selectedProfile.id}
            onAnalyze={handleAnalyze}
          />
        )}

        {view === 'chat' && selectedProfile && (
          <div className="h-[calc(100vh-200px)]">
            <AnalysisChat
              profile={selectedProfile}
              onClose={handleBackToList}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-4 text-center text-sm text-gray-600">
          <p>Skill Gap Identification System - Powered by AI</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
