import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MegaphoneSimple, SignOut, User } from '@phosphor-icons/react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl bg-white/70 border-b border-black/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center gap-2" data-testid="logo-link">
            <MegaphoneSimple size={28} weight="bold" className="text-[#002FA7]" />
            <span className="text-xl font-black tracking-tight">CIVIC ASSIST</span>
          </Link>

          <div className="flex items-center gap-6">
            <Link
              to="/"
              data-testid="nav-home"
              className={`text-xs font-bold uppercase tracking-[0.2em] transition-colors ${
                isActive('/') ? 'text-[#002FA7]' : 'text-[#52525B] hover:text-[#09090B]'
              }`}
            >
              Home
            </Link>
            {user && (
              <Link
                to="/complaint"
                data-testid="nav-complaint"
                className={`text-xs font-bold uppercase tracking-[0.2em] transition-colors ${
                  isActive('/complaint') ? 'text-[#002FA7]' : 'text-[#52525B] hover:text-[#09090B]'
                }`}
              >
                File Complaint
              </Link>
            )}
            <Link
              to="/how-it-works"
              data-testid="nav-how-it-works"
              className={`text-xs font-bold uppercase tracking-[0.2em] transition-colors ${
                isActive('/how-it-works') ? 'text-[#002FA7]' : 'text-[#52525B] hover:text-[#09090B]'
              }`}
            >
              How It Works
            </Link>
            <Link
              to="/help"
              data-testid="nav-help"
              className={`text-xs font-bold uppercase tracking-[0.2em] transition-colors ${
                isActive('/help') ? 'text-[#002FA7]' : 'text-[#52525B] hover:text-[#09090B]'
              }`}
            >
              Help
            </Link>
            <Link
              to="/contact"
              data-testid="nav-contact"
              className={`text-xs font-bold uppercase tracking-[0.2em] transition-colors ${
                isActive('/contact') ? 'text-[#002FA7]' : 'text-[#52525B] hover:text-[#09090B]'
              }`}
            >
              Contact
            </Link>

            {user ? (
              <div className="flex items-center gap-3 ml-4 pl-4 border-l border-[#E4E4E7]">
                <Link to="/profile" data-testid="user-profile-link">
                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.2em] text-[#09090B] hover:text-[#002FA7] transition-colors">
                    <User size={16} weight="bold" />
                    {user.name}
                  </div>
                </Link>
                <button
                  onClick={logout}
                  data-testid="logout-button"
                  className="text-[#E11D48] hover:text-[#BE123C] transition-colors"
                  title="Logout"
                >
                  <SignOut size={20} weight="bold" />
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                data-testid="nav-login"
                className="ml-4 pl-4 border-l border-[#E4E4E7] bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none border border-transparent hover:bg-[#002280] transition-colors px-4 py-2 text-xs"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
