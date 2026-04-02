import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Phone, EnvelopeSimple, MapPin, Clock, Buildings } from '@phosphor-icons/react';

const LocalHelpSection = ({ state, city, category }) => {
  const { token } = useAuth();
  const [helpData, setHelpData] = useState(null);
  const [loading, setLoading] = useState(true);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  useEffect(() => {
    fetchLocalHelp();
  }, [state, city, category]);

  const fetchLocalHelp = async () => {
    try {
      const response = await axios.post(
        `${API}/locations/local-help`,
        { state, city, category },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setHelpData(response.data);
    } catch (error) {
      console.error('Failed to fetch local help');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white border border-[#E4E4E7] p-6 md:p-8">
        <div className="text-center text-[#52525B]">Loading local assistance...</div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-[#E4E4E7] p-6 md:p-8" data-testid="local-help-section">
      <div className="mb-6">
        <h3 className="text-xl sm:text-2xl font-bold tracking-tight mb-2">Local Help & Contacts</h3>
        <p className="text-sm text-[#52525B]">
          Direct contacts and offices in {city}, {state} for faster resolution
        </p>
      </div>

      {/* Contact Numbers */}
      {helpData?.contacts && helpData.contacts.length > 0 && (
        <div className="mb-8">
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-4">Helpline Numbers</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {helpData.contacts.map((contact, index) => (
              <div
                key={index}
                className="bg-[#F4F4F5] border border-[#E4E4E7] p-5"
                data-testid={`contact-card-${index}`}
              >
                <h4 className="text-base font-bold tracking-tight text-[#09090B] mb-3">{contact.office}</h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Phone size={16} weight="bold" className="text-[#002FA7]" />
                    <a href={`tel:${contact.phone}`} className="text-sm font-mono text-[#09090B] hover:text-[#002FA7] transition-colors">
                      {contact.phone}
                    </a>
                  </div>
                  {contact.email && contact.email !== 'NA' && (
                    <div className="flex items-center gap-2">
                      <EnvelopeSimple size={16} weight="bold" className="text-[#002FA7]" />
                      <a href={`mailto:${contact.email}`} className="text-sm font-mono text-[#09090B] hover:text-[#002FA7] transition-colors break-all">
                        {contact.email}
                      </a>
                    </div>
                  )}
                  {contact.timings && (
                    <div className="flex items-center gap-2">
                      <Clock size={16} weight="bold" className="text-[#52525B]" />
                      <span className="text-xs text-[#52525B]">{contact.timings}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Office Locations */}
      {helpData?.offices && helpData.offices.length > 0 && (
        <div>
          <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-4">Offline Offices</div>
          <div className="space-y-4">
            {helpData.offices.map((office, index) => (
              <div
                key={index}
                className="border-l-4 border-[#002FA7] bg-[#F4F4F5] p-5"
                data-testid={`office-card-${index}`}
              >
                <div className="flex items-start gap-3">
                  <Buildings size={24} weight="bold" className="text-[#002FA7] flex-shrink-0 mt-1" />
                  <div className="flex-1">
                    <h4 className="text-base font-bold tracking-tight text-[#09090B] mb-1">{office.name}</h4>
                    <div className="flex items-start gap-2 mb-2">
                      <MapPin size={16} weight="bold" className="text-[#52525B] flex-shrink-0 mt-1" />
                      <p className="text-sm text-[#52525B]">{office.address}</p>
                    </div>
                    <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#002FA7]">
                      {office.department}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Helpful Tip */}
      <div className="mt-6 bg-blue-50 border border-blue-200 p-4">
        <p className="text-sm text-blue-900 leading-relaxed">
          <strong>Tip:</strong> For faster resolution, you may visit the offline office or call the helpline before submitting online.
          Keep your documents and complaint draft ready.
        </p>
      </div>
    </div>
  );
};

export default LocalHelpSection;
