import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { MegaphoneSimple, SignOut, User, List, X } from '@phosphor-icons/react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  const isActive = (path) => location.pathname === path;

  // Close menu on route change
  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  // Prevent body scroll when menu is open
  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [menuOpen]);

  const navLinks = [
    { to: '/', label: 'Home', testId: 'nav-home' },
    ...(user ? [{ to: '/complaint', label: 'File Complaint', testId: 'nav-complaint' }] : []),
    { to: '/how-it-works', label: 'How It Works', testId: 'nav-how-it-works' },
    { to: '/help', label: 'Help', testId: 'nav-help' },
    { to: '/contact', label: 'Contact', testId: 'nav-contact' },
  ];

  return (
    <>
      <nav className="sticky top-0 z-50 backdrop-blur-xl bg-white/70 border-b border-black/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">

            {/* Logo */}
            <Link to="/" className="flex items-center gap-2" data-testid="logo-link">
              <MegaphoneSimple size={28} weight="bold" className="text-[#002FA7]" />
              <span className="text-xl font-black tracking-tight">CIVIC ASSIST</span>
            </Link>

            {/* Desktop Nav Links */}
            <div className="hidden md:flex items-center gap-6">
              {navLinks.map(({ to, label, testId }) => (
                <Link
                  key={to}
                  to={to}
                  data-testid={testId}
                  className={`text-xs font-bold uppercase tracking-[0.2em] transition-colors ${
                    isActive(to) ? 'text-[#002FA7]' : 'text-[#52525B] hover:text-[#09090B]'
                  }`}
                >
                  {label}
                </Link>
              ))}

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
                  className="ml-4 pl-4 border-l border-[#E4E4E7] bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none hover:bg-[#002280] transition-colors px-4 py-2 text-xs"
                >
                  Login
                </Link>
              )}
            </div>

            {/* Mobile: right side — user icon + hamburger */}
            <div className="flex md:hidden items-center gap-3">
              {user && (
                <Link to="/profile" data-testid="user-profile-link-mobile">
                  <div className="flex items-center justify-center w-9 h-9 rounded-full bg-[#002FA7]/10 text-[#002FA7]">
                    <User size={18} weight="bold" />
                  </div>
                </Link>
              )}
              <button
                onClick={() => setMenuOpen((prev) => !prev)}
                aria-label={menuOpen ? 'Close menu' : 'Open menu'}
                aria-expanded={menuOpen}
                className="flex items-center justify-center w-9 h-9 text-[#09090B] hover:text-[#002FA7] transition-colors"
              >
                {menuOpen ? <X size={24} weight="bold" /> : <List size={24} weight="bold" />}
              </button>
            </div>

          </div>
        </div>
      </nav>

      {/* Mobile Drawer Overlay */}
      {menuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 md:hidden"
          onClick={() => setMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile Drawer Panel */}
      <div
        className={`fixed top-0 right-0 z-50 h-full w-72 bg-white shadow-2xl flex flex-col transition-transform duration-300 ease-in-out md:hidden ${
          menuOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        aria-hidden={!menuOpen}
      >
        {/* Drawer Header */}
        <div className="flex items-center justify-between px-5 h-16 border-b border-[#E4E4E7]">
          <div className="flex items-center gap-2">
            <MegaphoneSimple size={22} weight="bold" className="text-[#002FA7]" />
            <span className="text-base font-black tracking-tight">CIVIC ASSIST</span>
          </div>
          <button
            onClick={() => setMenuOpen(false)}
            aria-label="Close menu"
            className="text-[#52525B] hover:text-[#09090B] transition-colors"
          >
            <X size={22} weight="bold" />
          </button>
        </div>

        {/* Nav Links */}
        <nav className="flex flex-col px-5 py-6 gap-1 flex-1 overflow-y-auto">
          {navLinks.map(({ to, label, testId }) => (
            <Link
              key={to}
              to={to}
              data-testid={`${testId}-mobile`}
              className={`py-3 px-3 text-sm font-bold uppercase tracking-[0.15em] rounded transition-colors ${
                isActive(to)
                  ? 'text-[#002FA7] bg-[#002FA7]/8'
                  : 'text-[#52525B] hover:text-[#09090B] hover:bg-[#F4F4F5]'
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Drawer Footer — Auth */}
        <div className="px-5 py-5 border-t border-[#E4E4E7]">
          {user ? (
            <div className="flex items-center justify-between">
              <Link
                to="/profile"
                data-testid="user-profile-link-drawer"
                className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.1em] text-[#09090B] hover:text-[#002FA7] transition-colors"
              >
                <User size={18} weight="bold" />
                {user.name}
              </Link>
              <button
                onClick={() => { logout(); setMenuOpen(false); }}
                data-testid="logout-button-mobile"
                className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#E11D48] hover:text-[#BE123C] transition-colors"
              >
                <SignOut size={16} weight="bold" />
                Logout
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              data-testid="nav-login-mobile"
              className="block w-full text-center bg-[#002FA7] text-white font-bold uppercase tracking-wide hover:bg-[#002280] transition-colors px-4 py-3 text-xs"
            >
              Login
            </Link>
          )}
        </div>
      </div>
    </>
  );
};

export default Navbar;
