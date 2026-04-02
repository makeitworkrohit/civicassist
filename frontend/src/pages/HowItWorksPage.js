import React from 'react';
import { Microphone, Brain, MapPin, ListChecks, ArrowRight } from '@phosphor-icons/react';

const HowItWorksPage = () => {
  return (
    <div className="min-h-screen bg-white py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h1 className="text-4xl sm:text-5xl font-black tracking-tighter leading-none mb-4" data-testid="how-it-works-title">
            How Civic Assist Works
          </h1>
          <p className="text-base text-[#52525B] max-w-2xl mx-auto">
            Four simple steps to ensure your complaint reaches the right government portal
          </p>
        </div>

        <div className="space-y-16">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            <div>
              <div className="w-16 h-16 bg-[#002FA7] flex items-center justify-center mb-6">
                <Microphone size={32} weight="bold" className="text-white" />
              </div>
              <div className="font-mono text-sm tracking-tight text-[#09090B] mb-2">STEP 01</div>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-4">Input Your Complaint</h2>
              <p className="text-base text-[#52525B] leading-relaxed mb-4">
                Start by describing your problem. You can type it out or use voice input—whatever is more comfortable.
              </p>
              <p className="text-base text-[#52525B] leading-relaxed">
                Our system supports multiple languages, so you can communicate in Hindi, English, or other regional languages. The AI will understand and process your input seamlessly.
              </p>
            </div>
            <div className="bg-[#F4F4F5] border border-[#E4E4E7] p-8">
              <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-3">Example Input</div>
              <p className="text-base text-[#09090B] leading-relaxed italic">
                "The street lights on MG Road haven't been working for two weeks. It's getting dark early, and people are worried about safety while walking at night."
              </p>
            </div>
          </div>

          <div className="h-px bg-[#E4E4E7]"></div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            <div className="order-2 lg:order-1">
              <div className="bg-[#F4F4F5] border border-[#E4E4E7] p-8">
                <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-3">AI Output</div>
                <div className="border-l-4 border-[#002FA7] pl-4">
                  <p className="text-base text-[#09090B] leading-relaxed mb-3">
                    "Non-functional street lights on MG Road for 2 weeks causing safety concerns."
                  </p>
                  <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-1">Category</div>
                  <p className="font-mono text-sm text-[#002FA7]">Road Maintenance</p>
                </div>
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <div className="w-16 h-16 bg-[#002FA7] flex items-center justify-center mb-6">
                <Brain size={32} weight="bold" className="text-white" />
              </div>
              <div className="font-mono text-sm tracking-tight text-[#09090B] mb-2">STEP 02</div>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-4">AI Simplification</h2>
              <p className="text-base text-[#52525B] leading-relaxed mb-4">
                Our AI processes your input, removing unnecessary details while preserving the core issue.
              </p>
              <p className="text-base text-[#52525B] leading-relaxed">
                It also automatically categorizes your complaint (Water Supply, Electricity, Road Maintenance, etc.) to match it with the correct department.
              </p>
            </div>
          </div>

          <div className="h-px bg-[#E4E4E7]"></div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            <div>
              <div className="w-16 h-16 bg-[#002FA7] flex items-center justify-center mb-6">
                <MapPin size={32} weight="bold" className="text-white" />
              </div>
              <div className="font-mono text-sm tracking-tight text-[#09090B] mb-2">STEP 03</div>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-4">Portal Matching</h2>
              <p className="text-base text-[#52525B] leading-relaxed mb-4">
                Based on your location (state and city) and complaint category, our system identifies the appropriate government portal.
              </p>
              <p className="text-base text-[#52525B] leading-relaxed">
                This ensures your complaint reaches the right department without you having to navigate complex government websites.
              </p>
            </div>
            <div className="bg-[#F4F4F5] border border-[#E4E4E7] p-8">
              <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-3">Portal Suggestion</div>
              <h3 className="text-lg font-bold mb-2">CPGRAMS</h3>
              <p className="text-sm text-[#52525B] mb-4">Centralized Public Grievance Redress System</p>
              <button className="bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none border border-transparent px-6 py-2 text-xs flex items-center gap-2">
                Go to Portal <ArrowRight size={14} weight="bold" />
              </button>
            </div>
          </div>

          <div className="h-px bg-[#E4E4E7]"></div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            <div className="order-2 lg:order-1">
              <div className="bg-[#F4F4F5] border border-[#E4E4E7] p-8">
                <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#52525B] mb-4">Guidance Steps</div>
                <div className="space-y-3">
                  {['Visit the portal', 'Register/Login', 'Select department', 'Fill complaint form', 'Upload documents', 'Submit & track'].map((step, i) => (
                    <div key={i} className="flex gap-3 items-start">
                      <div className="w-6 h-6 bg-[#09090B] text-white flex items-center justify-center font-mono text-xs font-bold flex-shrink-0">
                        {String(i + 1).padStart(2, '0')}
                      </div>
                      <p className="text-sm text-[#09090B] pt-0.5">{step}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <div className="w-16 h-16 bg-[#002FA7] flex items-center justify-center mb-6">
                <ListChecks size={32} weight="bold" className="text-white" />
              </div>
              <div className="font-mono text-sm tracking-tight text-[#09090B] mb-2">STEP 04</div>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-4">Step-by-Step Guidance</h2>
              <p className="text-base text-[#52525B] leading-relaxed mb-4">
                We don't just direct you to a portal—we provide clear, step-by-step instructions on how to file your complaint.
              </p>
              <p className="text-base text-[#52525B] leading-relaxed">
                This includes what documents you might need, how to fill forms correctly, and tips for successful submission.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HowItWorksPage;
