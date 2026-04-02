import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { EnvelopeSimple, User, ChatText } from '@phosphor-icons/react';

const ContactPage = () => {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/contact`, formData);
      toast.success('Message sent successfully! We\'ll get back to you soon.');
      setFormData({ name: '', email: '', message: '' });
    } catch (error) {
      toast.error('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F4F5] py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-black tracking-tighter leading-none mb-4" data-testid="contact-page-title">
            Get in Touch
          </h1>
          <p className="text-base text-[#52525B] max-w-2xl mx-auto">
            Have questions or feedback? We'd love to hear from you.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white border border-[#E4E4E7] p-8">
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight mb-6">Send us a Message</h2>
            
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                  Your Name
                </label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 text-[#52525B]" size={18} />
                  <input
                    type="text"
                    data-testid="contact-name-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all h-12 pl-12 pr-4 font-mono text-sm"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                  Email Address
                </label>
                <div className="relative">
                  <EnvelopeSimple className="absolute left-4 top-1/2 -translate-y-1/2 text-[#52525B]" size={18} />
                  <input
                    type="email"
                    data-testid="contact-email-input"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all h-12 pl-12 pr-4 font-mono text-sm"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                  Message
                </label>
                <div className="relative">
                  <ChatText className="absolute left-4 top-4 text-[#52525B]" size={18} />
                  <textarea
                    data-testid="contact-message-input"
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all p-4 pl-12 font-mono text-sm min-h-[150px]"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                data-testid="contact-submit-button"
                disabled={loading}
                className="w-full bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none border border-transparent hover:bg-[#002280] transition-colors px-6 py-3 disabled:opacity-50"
              >
                {loading ? 'Sending...' : 'Send Message'}
              </button>
            </form>
          </div>

          <div className="space-y-6">
            <div className="bg-white border border-[#E4E4E7] p-8">
              <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-3">About Civic Assist</h3>
              <p className="text-base text-[#09090B] leading-relaxed mb-4">
                Civic Assist is designed to bridge the gap between citizens and government services by simplifying the complaint filing process.
              </p>
              <p className="text-base text-[#52525B] leading-relaxed">
                Our mission is to make civic engagement easier and more accessible for everyone, regardless of technical expertise or language barriers.
              </p>
            </div>

            <div className="bg-white border border-[#E4E4E7] p-8">
              <h3 className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-3">Quick Links</h3>
              <div className="space-y-3">
                <a href="/how-it-works" className="block text-base text-[#002FA7] hover:text-[#002280] font-bold transition-colors">
                  How It Works →
                </a>
                <a href="/help" className="block text-base text-[#002FA7] hover:text-[#002280] font-bold transition-colors">
                  Help & FAQs →
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactPage;
