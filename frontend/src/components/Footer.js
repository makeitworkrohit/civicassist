import React from 'react';
import { Link } from 'react-router-dom';
import { MegaphoneSimple } from '@phosphor-icons/react';

const Footer = () => {
  return (
    <footer className="bg-[#09090B] text-white py-12 mt-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <MegaphoneSimple size={24} weight="bold" />
              <span className="text-lg font-black tracking-tight">CIVIC ASSIST</span>
            </div>
            <p className="text-sm text-[#A1A1AA] leading-relaxed">
              Empowering citizens to voice their concerns and connect with the right government portals efficiently.
            </p>
          </div>

          <div>
            <h3 className="text-xs font-bold uppercase tracking-[0.2em] mb-4">Quick Links</h3>
            <div className="flex flex-col gap-2">
              <Link to="/" className="text-sm text-[#A1A1AA] hover:text-white transition-colors">
                Home
              </Link>
              <Link to="/how-it-works" className="text-sm text-[#A1A1AA] hover:text-white transition-colors">
                How It Works
              </Link>
              <Link to="/help" className="text-sm text-[#A1A1AA] hover:text-white transition-colors">
                Help
              </Link>
              <Link to="/contact" className="text-sm text-[#A1A1AA] hover:text-white transition-colors">
                Contact Us
              </Link>
            </div>
          </div>

          <div>
            <h3 className="text-xs font-bold uppercase tracking-[0.2em] mb-4">About</h3>
            <p className="text-sm text-[#A1A1AA] leading-relaxed">
              Civic Assist is a platform designed to simplify the complaint filing process and direct citizens to appropriate government portals.
            </p>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-white/10 text-center">
          <p className="text-xs text-[#A1A1AA]">
            © 2026 Civic Assist. Built to serve citizens better.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
