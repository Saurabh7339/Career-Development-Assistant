import { useState, useEffect } from 'react';
import { profileAPI } from '../services/api';

const ProfileList = ({ onSelectProfile, onCreateNew }) => {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await profileAPI.list();
      setProfiles(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load profiles');
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

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Profiles</h2>
        {onCreateNew && (
          <button
            onClick={onCreateNew}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-medium"
          >
            Create New Profile
          </button>
        )}
      </div>

      {profiles.length === 0 ? (
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <p className="text-gray-600 mb-4">No profiles found</p>
          {onCreateNew && (
            <button
              onClick={onCreateNew}
              className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition"
            >
              Create Your First Profile
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {profiles.map((profile) => {
            const profileId = profile.id || profile.profile_id;
            return (
              <div
                key={profileId}
                className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition cursor-pointer"
                onClick={() => {
                  if (onSelectProfile && profileId) {
                    onSelectProfile({ ...profile, id: profileId });
                  } else {
                    console.error('Profile missing ID:', profile);
                    alert('Error: Profile ID not found');
                  }
                }}
              >
                <h3 className="text-xl font-bold text-gray-800 mb-2">{profile.name}</h3>
                <p className="text-gray-600 mb-4">{profile.current_role}</p>
                <div className="flex justify-between text-sm text-gray-500">
                  <span>{profile.skills?.length || 0} skills</span>
                  <span>{profile.certifications?.length || 0} certifications</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ProfileList;

