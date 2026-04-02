import React, { useState } from 'react';
import { Copy, CheckCircle, PencilSimple } from '@phosphor-icons/react';
import { toast } from 'sonner';

const ComplaintDraft = ({ subject, description, category, userName, location }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedSubject, setEditedSubject] = useState(subject);
  const [editedDescription, setEditedDescription] = useState(description);
  const [copied, setCopied] = useState({ subject: false, description: false, all: false });

  const copyToClipboard = (text, field) => {
    navigator.clipboard.writeText(text);
    setCopied({ ...copied, [field]: true });
    toast.success(`${field === 'all' ? 'All content' : field.charAt(0).toUpperCase() + field.slice(1)} copied to clipboard`);
    setTimeout(() => setCopied({ ...copied, [field]: false }), 2000);
  };

  const copyAll = () => {
    const fullText = `Subject: ${editedSubject}\n\nDescription:\n${editedDescription}\n\nCategory: ${category}\nLocation: ${location}\nName: ${userName}`;
    copyToClipboard(fullText, 'all');
  };

  return (
    <div className="bg-white border border-[#E4E4E7] p-6 md:p-8" data-testid="complaint-draft-section">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-xl sm:text-2xl font-bold tracking-tight mb-2">Your Complaint Draft</h3>
          <p className="text-sm text-[#52525B]">
            We've prepared a formal complaint ready for submission. You can copy or edit before filing.
          </p>
        </div>
        <button
          onClick={() => setIsEditing(!isEditing)}
          data-testid="toggle-edit-button"
          className="flex items-center gap-2 text-[#002FA7] hover:text-[#002280] font-bold text-sm transition-colors"
        >
          <PencilSimple size={18} weight="bold" />
          {isEditing ? 'Done' : 'Edit'}
        </button>
      </div>

      <div className="space-y-4">
        {/* Subject */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B]">Subject</label>
            <button
              onClick={() => copyToClipboard(editedSubject, 'subject')}
              data-testid="copy-subject-button"
              className="flex items-center gap-1 text-xs font-bold uppercase tracking-[0.2em] text-[#002FA7] hover:text-[#002280] transition-colors"
            >
              {copied.subject ? <CheckCircle size={14} weight="bold" /> : <Copy size={14} weight="bold" />}
              {copied.subject ? 'Copied' : 'Copy'}
            </button>
          </div>
          {isEditing ? (
            <input
              type="text"
              value={editedSubject}
              onChange={(e) => setEditedSubject(e.target.value)}
              data-testid="edit-subject-input"
              className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all h-12 px-4 font-mono text-sm"
            />
          ) : (
            <div className="bg-[#F4F4F5] border border-[#E4E4E7] p-4" data-testid="draft-subject">
              <p className="text-base text-[#09090B] font-mono">{editedSubject}</p>
            </div>
          )}
        </div>

        {/* Description */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B]">Description</label>
            <button
              onClick={() => copyToClipboard(editedDescription, 'description')}
              data-testid="copy-description-button"
              className="flex items-center gap-1 text-xs font-bold uppercase tracking-[0.2em] text-[#002FA7] hover:text-[#002280] transition-colors"
            >
              {copied.description ? <CheckCircle size={14} weight="bold" /> : <Copy size={14} weight="bold" />}
              {copied.description ? 'Copied' : 'Copy'}
            </button>
          </div>
          {isEditing ? (
            <textarea
              value={editedDescription}
              onChange={(e) => setEditedDescription(e.target.value)}
              data-testid="edit-description-input"
              className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all p-4 font-mono text-sm min-h-[200px]"
            />
          ) : (
            <div className="bg-[#F4F4F5] border border-[#E4E4E7] p-4" data-testid="draft-description">
              <p className="text-base text-[#09090B] leading-relaxed whitespace-pre-wrap">{editedDescription}</p>
            </div>
          )}
        </div>

        {/* Auto-filled Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 bg-[#F4F4F5] border border-[#E4E4E7] p-4">
          <div>
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-1">Category</div>
            <p className="text-sm font-mono text-[#09090B]">{category}</p>
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-1">Location</div>
            <p className="text-sm font-mono text-[#09090B]">{location}</p>
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-1">Name</div>
            <p className="text-sm font-mono text-[#09090B]">{userName}</p>
          </div>
        </div>

        {/* Copy All Button */}
        <button
          onClick={copyAll}
          data-testid="copy-all-button"
          className="w-full bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none border border-transparent hover:bg-[#002280] transition-colors px-6 py-3 flex items-center justify-center gap-2"
        >
          {copied.all ? <CheckCircle size={20} weight="bold" /> : <Copy size={20} weight="bold" />}
          {copied.all ? 'Copied All' : 'Copy All Details'}
        </button>
      </div>
    </div>
  );
};

export default ComplaintDraft;
