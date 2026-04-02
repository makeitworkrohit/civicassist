import React, { useState } from 'react';

const HelpPage = () => {
  const [openIndex, setOpenIndex] = useState(null);

  const faqs = [
    {
      question: 'What is Civic Assist?',
      answer: 'Civic Assist is an AI-powered platform that helps citizens file complaints to the right government portals. It simplifies your complaint using AI and directs you to the appropriate department based on your location.'
    },
    {
      question: 'How does the voice input feature work?',
      answer: 'Click the "Record Voice Complaint" button and allow microphone access. Speak your complaint in any language. Our AI will transcribe it using OpenAI Whisper technology and process it just like typed text.'
    },
    {
      question: 'Which languages are supported?',
      answer: 'The platform supports multiple Indian languages including Hindi, English, and other regional languages. The AI can understand and process complaints in your preferred language.'
    },
    {
      question: 'Do I need to create an account?',
      answer: 'Yes, you need to register with your email and provide your location (state and city) so we can suggest the correct government portal for your area.'
    },
    {
      question: 'What information do I need to provide?',
      answer: 'You need to provide your name, email, state, city, and optionally your pin code. This helps us route your complaint to the right portal.'
    },
    {
      question: 'How accurate is the AI simplification?',
      answer: 'Our AI uses GPT-4o to understand and simplify complaints. After simplification, we show you the result and ask for confirmation. If it\'s not accurate, you can re-enter your complaint.'
    },
    {
      question: 'Can I file complaints for any type of issue?',
      answer: 'Yes! We support various categories including Water Supply, Electricity, Road Maintenance, Waste Management, Public Transport, Healthcare, Education, Police, Revenue, Consumer Rights, and more.'
    },
    {
      question: 'Will my complaint be automatically submitted to the government?',
      answer: 'No. We direct you to the correct government portal and provide step-by-step guidance. You will need to submit the complaint on the official portal yourself.'
    },
    {
      question: 'Is my data safe?',
      answer: 'Yes. Your data is stored securely and only used to process your complaints and suggest appropriate portals. We do not share your personal information with third parties.'
    },
    {
      question: 'What if the suggested portal is not correct?',
      answer: 'If you believe the suggested portal is incorrect, you can contact us through the Contact page. We\'re continuously improving our portal matching algorithm.'
    }
  ];

  return (
    <div className="min-h-screen bg-white py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-black tracking-tighter leading-none mb-4" data-testid="help-page-title">
            Frequently Asked Questions
          </h1>
          <p className="text-base text-[#52525B] max-w-2xl mx-auto">
            Find answers to common questions about Civic Assist
          </p>
        </div>

        <div className="space-y-2">
          {faqs.map((faq, index) => (
            <div key={index} className="border border-[#E4E4E7] bg-white" data-testid={`faq-item-${index + 1}`}>
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full text-left p-6 flex justify-between items-center hover:bg-[#F4F4F5] transition-colors"
                data-testid={`faq-question-${index + 1}`}
              >
                <span className="text-base font-bold tracking-tight pr-4">{faq.question}</span>
                <span className="text-2xl font-bold text-[#002FA7] flex-shrink-0">
                  {openIndex === index ? '−' : '+'}
                </span>
              </button>
              {openIndex === index && (
                <div className="px-6 pb-6 border-t border-[#E4E4E7] pt-4" data-testid={`faq-answer-${index + 1}`}>
                  <p className="text-base text-[#52525B] leading-relaxed">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-16 bg-[#F4F4F5] border border-[#E4E4E7] p-8 text-center">
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight mb-4">Still have questions?</h2>
          <p className="text-base text-[#52525B] mb-6">
            If you couldn't find the answer you're looking for, feel free to contact us.
          </p>
          <a
            href="/contact"
            data-testid="help-contact-link"
            className="inline-flex bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none border border-transparent hover:bg-[#002280] transition-colors px-8 py-3"
          >
            Contact Us
          </a>
        </div>
      </div>
    </div>
  );
};

export default HelpPage;
