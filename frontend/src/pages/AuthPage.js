import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { EnvelopeSimple, LockKey, User as UserIcon } from '@phosphor-icons/react';
import { toast } from 'sonner';

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
        toast.success('Logged in successfully!');
        navigate('/complaint');
      } else {
        await register(formData.name, formData.email, formData.password);
        toast.success('Account created successfully!');
        navigate('/profile');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F4F5] flex items-center justify-center py-12 px-4">
      <div className="w-full max-w-md">
        <div className="bg-white border border-[#E4E4E7] p-8">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight mb-2" data-testid="auth-title">
            {isLogin ? 'Login' : 'Create Account'}
          </h1>
          <p className="text-base text-[#52525B] mb-8">
            {isLogin ? 'Access your complaint dashboard' : 'Start filing complaints easily'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <div>
                <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                  Full Name
                </label>
                <div className="relative">
                  <UserIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-[#52525B]" size={18} />
                  <input
                    type="text"
                    data-testid="register-name-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all h-12 pl-12 pr-4 font-mono text-sm"
                    required
                  />
                </div>
              </div>
            )}

            <div>
              <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                Email Address
              </label>
              <div className="relative">
                <EnvelopeSimple className="absolute left-4 top-1/2 -translate-y-1/2 text-[#52525B]" size={18} />
                <input
                  type="email"
                  data-testid="auth-email-input"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all h-12 pl-12 pr-4 font-mono text-sm"
                  required
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                Password
              </label>
              <div className="relative">
                <LockKey className="absolute left-4 top-1/2 -translate-y-1/2 text-[#52525B]" size={18} />
                <input
                  type="password"
                  data-testid="auth-password-input"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all h-12 pl-12 pr-4 font-mono text-sm"
                  required
                  minLength={6}
                />
              </div>
            </div>

            <button
              type="submit"
              data-testid="auth-submit-button"
              disabled={loading}
              className="w-full bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none border border-transparent hover:bg-[#002280] transition-colors px-6 py-3 disabled:opacity-50"
            >
              {loading ? 'Processing...' : (isLogin ? 'Login' : 'Create Account')}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              data-testid="auth-toggle-button"
              className="text-sm text-[#002FA7] hover:text-[#002280] font-bold uppercase tracking-wide"
            >
              {isLogin ? 'Need an account? Register' : 'Already have an account? Login'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
