import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { Microphone, Stop, ArrowRight, CheckCircle, XCircle, Phone } from '@phosphor-icons/react';
import { toast } from 'sonner';
import ComplaintDraft from '../components/ComplaintDraft';
import DocumentHelper from '../components/DocumentHelper';
import LocalHelpSection from '../components/LocalHelpSection';

const ComplaintPage = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [simplified, setSimplified] = useState('');
  const [category, setCategory] = useState('');
  const [draftSubject, setDraftSubject] = useState('');
  const [draftDescription, setDraftDescription] = useState('');
  const [portal, setPortal] = useState(null);
  const [complaintId, setComplaintId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [showLocalHelp, setShowLocalHelp] = useState(false);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${BACKEND_URL}/api`;

  if (!user) {
    navigate('/login');
    return null;
  }

  if (!user.state || !user.city) {
    navigate('/profile');
    return null;
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        await transcribeAudio(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (error) {
      toast.error('Microphone access denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      setIsRecording(false);
      setMediaRecorder(null);
    }
  };

  const transcribeAudio = async (audioBlob) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');

      const response = await axios.post(`${API}/complaint/transcribe`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      setInputText(response.data.text);
      toast.success('Audio transcribed successfully!');
    } catch (error) {
      toast.error('Transcription failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSimplify = async () => {
    if (!inputText.trim()) {
      toast.error('Please enter or record your complaint');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(
        `${API}/complaint/simplify`,
        { text: inputText },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setSimplified(response.data.simplified);
      setCategory(response.data.category);
      setDraftSubject(response.data.subject);
      setDraftDescription(response.data.description);
      setStep(2);
    } catch (error) {
      toast.error('AI processing failed');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (confirmed) => {
    if (!confirmed) {
      setStep(1);
      setSimplified('');
      setCategory('');
      setDraftSubject('');
      setDraftDescription('');
      return;
    }

    setLoading(true);
    try {
      const portalResponse = await axios.post(
        `${API}/portal/suggest`,
        { category, state: user.state, city: user.city, pincode: user.pincode },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setPortal(portalResponse.data);

      const submitResponse = await axios.post(
        `${API}/complaint/submit`,
        {
          original_input: inputText,
          simplified_input: simplified,
          category,
          confirmed: true,
          draft_subject: draftSubject,
          draft_description: draftDescription
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setComplaintId(submitResponse.data.id);
      setStep(3);
      toast.success('Complaint processed successfully!');
    } catch (error) {
      toast.error('Failed to process complaint');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F4F5] py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight mb-2" data-testid="complaint-page-title">
            File Your Complaint
          </h1>
          <p className="text-base text-[#52525B]">
            Location: {user.city}, {user.state}
          </p>
        </div>

        {step === 1 && (
          <div className="bg-white border border-[#E4E4E7] p-8" data-testid="complaint-step-1">
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight mb-6">Describe Your Problem</h2>
            
            <div className="mb-6">
              <label className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2 block">
                Type Your Complaint
              </label>
              <textarea
                data-testid="complaint-text-input"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                className="w-full bg-transparent border border-[#E4E4E7] rounded-none focus:border-[#09090B] focus:ring-1 focus:ring-[#09090B] transition-all p-4 font-mono text-sm min-h-[200px]"
                placeholder="Example: The street lights on MG Road have not been working for the past two weeks, causing safety issues at night..."
              />
            </div>

            <div className="flex items-center gap-4 mb-6">
              <div className="h-px bg-[#E4E4E7] flex-1"></div>
              <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B]">Or</span>
              <div className="h-px bg-[#E4E4E7] flex-1"></div>
            </div>

            <div className="text-center mb-8">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                data-testid="voice-record-button"
                disabled={loading}
                className={`inline-flex items-center gap-3 font-bold uppercase tracking-wide rounded-none border transition-colors px-8 py-4 ${
                  isRecording
                    ? 'bg-[#E11D48] text-white border-transparent hover:bg-[#BE123C]'
                    : 'bg-transparent text-[#09090B] border-[#09090B] hover:bg-[#09090B] hover:text-white'
                }`}
              >
                {isRecording ? (
                  <>
                    <Stop size={20} weight="bold" />
                    Stop Recording
                  </>
                ) : (
                  <>
                    <Microphone size={20} weight="bold" />
                    Record Voice Complaint
                  </>
                )}
              </button>
              {isRecording && (
                <p className="text-sm text-[#E11D48] mt-3 font-bold">Recording in progress...</p>
              )}
            </div>

            <button
              onClick={handleSimplify}
              data-testid="simplify-button"
              disabled={loading || !inputText.trim()}
              className="w-full bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none border border-transparent hover:bg-[#002280] transition-colors px-6 py-3 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? 'Processing...' : 'Process with AI'}
              <ArrowRight size={20} weight="bold" />
            </button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6" data-testid="complaint-step-2">
            {/* AI Confirmation */}
            <div className="bg-white border border-[#E4E4E7] p-8">
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight mb-6">Is this your concern?</h2>
              
              <div className="border-l-4 border-[#002FA7] bg-[#F4F4F5] p-6 mb-6">
                <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2">Simplified Complaint</div>
                <p className="text-base text-[#09090B] leading-relaxed mb-4" data-testid="simplified-complaint">{simplified}</p>
                <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-1">Category</div>
                <p className="font-mono text-sm text-[#002FA7]" data-testid="complaint-category">{category}</p>
              </div>

              <div className="flex gap-4">
                <button
                  onClick={() => handleConfirm(true)}
                  data-testid="confirm-yes-button"
                  disabled={loading}
                  className="flex-1 bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none border border-transparent hover:bg-[#002280] transition-colors px-6 py-3 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <CheckCircle size={20} weight="bold" />
                  Yes, Proceed
                </button>
                <button
                  onClick={() => handleConfirm(false)}
                  data-testid="confirm-no-button"
                  disabled={loading}
                  className="flex-1 bg-transparent text-[#09090B] border border-[#09090B] font-bold uppercase tracking-wide rounded-none hover:bg-[#09090B] hover:text-white transition-colors px-6 py-3 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <XCircle size={20} weight="bold" />
                  No, Re-enter
                </button>
              </div>
            </div>

            {/* Complaint Draft */}
            <ComplaintDraft
              subject={draftSubject}
              description={draftDescription}
              category={category}
              userName={user.name}
              location={`${user.city}, ${user.state} - ${user.pincode || ''}`}
            />
          </div>
        )}

        {step === 3 && portal && (
          <div className="space-y-6" data-testid="complaint-step-3">
            {/* Portal Suggestion */}
            <div className="bg-white border border-[#E4E4E7] p-8">
              <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-2">Recommended Portal</div>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight mb-4" data-testid="portal-name">{portal.name}</h2>
              <p className="text-base text-[#52525B] leading-relaxed mb-6" data-testid="portal-description">{portal.description}</p>
              <a
                href={portal.url}
                target="_blank"
                rel="noopener noreferrer"
                data-testid="portal-link-button"
                className="inline-flex items-center gap-3 bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none border border-transparent hover:bg-[#002280] transition-colors px-8 py-3"
              >
                Go to Portal
                <ArrowRight size={20} weight="bold" />
              </a>
            </div>

            {/* Step-by-Step Guidance */}
            {portal.guidance_steps && portal.guidance_steps.length > 0 && (
              <div className="bg-white border border-[#E4E4E7] p-8">
                <h3 className="text-xl font-bold tracking-tight mb-6">Step-by-Step Guidance</h3>
                <div className="space-y-4">
                  {portal.guidance_steps.map((step, index) => (
                    <div key={index} className="flex gap-4" data-testid={`guidance-step-${index + 1}`}>
                      <div className="w-8 h-8 bg-[#09090B] text-white flex items-center justify-center font-mono text-sm font-bold flex-shrink-0">
                        {String(index + 1).padStart(2, '0')}
                      </div>
                      <p className="text-base text-[#09090B] pt-1">{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Document Helper */}
            <DocumentHelper category={category} complaintId={complaintId} />

            {/* Local Help Toggle Button */}
            <div className="text-center">
              <button
                onClick={() => setShowLocalHelp(!showLocalHelp)}
                data-testid="toggle-local-help-button"
                className="inline-flex items-center gap-3 bg-transparent text-[#09090B] border-2 border-[#09090B] font-bold uppercase tracking-wide rounded-none hover:bg-[#09090B] hover:text-white transition-colors px-8 py-3"
              >
                {showLocalHelp ? (
                  <>
                    <XCircle size={20} weight="bold" />
                    Hide Local Help & Contacts
                  </>
                ) : (
                  <>
                    <Phone size={20} weight="bold" />
                    Need Local Help & Contacts?
                  </>
                )}
              </button>
            </div>

            {/* Local Help Section - Collapsible */}
            {showLocalHelp && (
              <div className="animate-fadeIn">
                <LocalHelpSection state={user.state} city={user.city} category={category} pincode={user.pincode} />
              </div>
            )}

            <button
              onClick={() => {
                setStep(1);
                setInputText('');
                setSimplified('');
                setCategory('');
                setDraftSubject('');
                setDraftDescription('');
                setPortal(null);
                setComplaintId(null);
                setShowLocalHelp(false);
              }}
              data-testid="file-another-complaint-button"
              className="w-full bg-transparent text-[#09090B] border border-[#09090B] font-bold uppercase tracking-wide rounded-none hover:bg-[#09090B] hover:text-white transition-colors px-6 py-3"
            >
              File Another Complaint
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComplaintPage;
