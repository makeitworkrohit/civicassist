import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { MapPin, Envelope, User as UserIcon } from '@phosphor-icons/react';

const ProfilePage = () => {
  const { user, updateProfile, token } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    state: '',
    city: '',
    pincode: ''
  });
  const [states, setStates] = useState([]);
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || '',
        state: user.state || '',
        city: user.city || '',
        pincode: user.pincode || ''
      });
    }
    fetchStates();
  }, [user]);

  useEffect(() => {
    if (formData.state) {
      fetchCities(formData.state);
    }
  }, [formData.state]);

  const fetchStates = async () => {
    try {
      const response = await axios.get(`${API}/locations/states`);
      setStates(response.data.states);
    } catch (error) {
      console.error('Failed to fetch states');
    }
  };

  const fetchCities = async (state) => {
    try {
      const response = await axios.get(`${API}/locations/cities/${state}`);
      setCities(response.data.cities);
    } catch (error) {
      console.error('Failed to fetch cities');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await updateProfile(formData);
      toast.success('Profile updated successfully!');
      navigate('/complaint');
    } catch (error) {
      toast.error('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    navigate('/login');
    return null;
  }

  return (
    <div className="min-h-screen bg-[#F4F4F5] py-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white border border-[#E4E4E7] p-8">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight mb-2" data-testid="profile-title">Update Profile</h1>
          <p className="text-base text-[#52525B] mb-8">
            We need your location to suggest the right complaint portal
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                Full Name
              </label>
              <div className="relative">
                <UserIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-[#52525B]" size={18} />
                <input
                  type="text"
                  data-testid="profile-name-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all h-12 pl-12 pr-4 font-mono text-sm"
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                Email (Read Only)
              </label>
              <div className="relative">
                <Envelope className="absolute left-4 top-1/2 -translate-y-1/2 text-[#52525B]" size={18} />
                <input
                  type="email"
                  value={user.email}
                  disabled
                  className="w-full bg-[#F4F4F5] border border-[#E4E4E7] rounded-none h-12 pl-12 pr-4 font-mono text-sm text-[#52525B]"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                State
              </label>
              <div className="relative">
                <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-[#52525B]" size={18} />
                <select
                  data-testid="profile-state-select"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value, city: '' })}
                  className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all h-12 pl-12 pr-4 font-mono text-sm"
                  required
                >
                  <option value="">Select State</option>
                  {states.map((state) => (
                    <option key={state} value={state}>{state}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                City
              </label>
              <div className="relative">
                <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-[#52525B]" size={18} />
                <select
                  data-testid="profile-city-select"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all h-12 pl-12 pr-4 font-mono text-sm"
                  required
                  disabled={!formData.state}
                >
                  <option value="">Select City</option>
                  {cities.map((city) => (
                    <option key={city} value={city}>{city}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                Pin Code (Optional)
              </label>
              <div className="relative">
                <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-[#52525B]" size={18} />
                <input
                  type="text"
                  data-testid="profile-pincode-input"
                  value={formData.pincode}
                  onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
                  className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all h-12 pl-12 pr-4 font-mono text-sm"
                  pattern="[0-9]{6}"
                  placeholder="123456"
                />
              </div>
            </div>

            <button
              type="submit"
              data-testid="profile-submit-button"
              disabled={loading}
              className="w-full bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none border border-transparent hover:bg-[#002280] transition-colors px-6 py-3 disabled:opacity-50"
            >
              {loading ? 'Updating...' : 'Update Profile'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
