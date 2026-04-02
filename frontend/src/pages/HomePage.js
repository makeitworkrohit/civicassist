import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowRight, Microphone, Brain, MapPin, ListChecks } from '@phosphor-icons/react';

const HomePage = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen">
      <section className="relative min-h-[80vh] flex items-center" style={{
        backgroundImage: 'url(https://images.unsplash.com/photo-1761792425134-7e09471c5b55?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MTN8MHwxfHNlYXJjaHwzfHxtb2Rlcm4lMjBnb3Zlcm5tZW50JTIwYnVpbGRpbmclMjBhcmNoaXRlY3R1cmV8ZW58MHx8fHwxNzc1MTY4MDI4fDA&ixlib=rb-4.1.0&q=85)',
        backgroundSize: 'cover',
        backgroundPosition: 'center'
      }}>
        <div className="absolute inset-0 bg-gradient-to-r from-white/95 via-white/80 to-transparent"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="max-w-2xl">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tighter leading-none mb-6" data-testid="hero-title">
              Your Voice.
              <br />
              The Right Portal.
              <br />
              <span className="text-[#002FA7]">Instantly.</span>
            </h1>
            <p className="text-base text-[#52525B] leading-relaxed mb-8 max-w-xl">
              Civic Assist uses AI to simplify your complaint, identify the issue, and direct you to the exact government portal—saving time and eliminating confusion.
            </p>
            <Link
              to={user ? "/complaint" : "/login"}
              data-testid="hero-cta-button"
              className="inline-flex items-center gap-3 bg-[#002FA7] text-white font-bold uppercase tracking-wide rounded-none border border-transparent hover:bg-[#002280] transition-colors px-8 py-4"
            >
              {user ? 'File a Complaint' : 'Get Started'}
              <ArrowRight size={20} weight="bold" />
            </Link>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight mb-4">How Civic Assist Works</h2>
            <p className="text-base text-[#52525B] max-w-2xl mx-auto">
              Four simple steps to get your complaint to the right place
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white border border-[#E4E4E7] p-6" data-testid="step-1">
              <div className="w-12 h-12 bg-[#002FA7] flex items-center justify-center mb-4">
                <Microphone size={24} weight="bold" className="text-white" />
              </div>
              <div className="font-mono text-sm tracking-tight text-[#09090B] mb-2">01</div>
              <h3 className="text-xl font-bold tracking-tight mb-2">Speak or Type</h3>
              <p className="text-base text-[#52525B]">Describe your problem in any language, using text or voice input.</p>
            </div>

            <div className="bg-white border border-[#E4E4E7] p-6" data-testid="step-2">
              <div className="w-12 h-12 bg-[#002FA7] flex items-center justify-center mb-4">
                <Brain size={24} weight="bold" className="text-white" />
              </div>
              <div className="font-mono text-sm tracking-tight text-[#09090B] mb-2">02</div>
              <h3 className="text-xl font-bold tracking-tight mb-2">AI Simplifies</h3>
              <p className="text-base text-[#52525B]">Our AI converts your input into a clear, actionable complaint.</p>
            </div>

            <div className="bg-white border border-[#E4E4E7] p-6" data-testid="step-3">
              <div className="w-12 h-12 bg-[#002FA7] flex items-center justify-center mb-4">
                <MapPin size={24} weight="bold" className="text-white" />
              </div>
              <div className="font-mono text-sm tracking-tight text-[#09090B] mb-2">03</div>
              <h3 className="text-xl font-bold tracking-tight mb-2">Portal Match</h3>
              <p className="text-base text-[#52525B]">Based on your location and issue, we find the right government portal.</p>
            </div>

            <div className="bg-white border border-[#E4E4E7] p-6" data-testid="step-4">
              <div className="w-12 h-12 bg-[#002FA7] flex items-center justify-center mb-4">
                <ListChecks size={24} weight="bold" className="text-white" />
              </div>
              <div className="font-mono text-sm tracking-tight text-[#09090B] mb-2">04</div>
              <h3 className="text-xl font-bold tracking-tight mb-2">Get Guidance</h3>
              <p className="text-base text-[#52525B]">Follow step-by-step instructions to file your complaint successfully.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-[#F4F4F5]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <img 
                src="https://images.unsplash.com/photo-1709701576120-7c15eaff1fcb?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTJ8MHwxfHNlYXJjaHwyfHxwZXJzb24lMjB1c2luZyUyMHBob25lJTIwY2l0eSUyMHN0cmVldHxlbnwwfHx8fDE3NzUxNjgwMTZ8MA&ixlib=rb-4.1.0&q=85"
                alt="Person using phone in city"
                className="w-full h-96 object-cover border border-[#E4E4E7]"
              />
            </div>
            <div>
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold tracking-tight mb-4">Built for Every Citizen</h2>
              <p className="text-base text-[#52525B] leading-relaxed mb-6">
                Whether you're dealing with water supply issues, electricity problems, road maintenance, or any civic concern—Civic Assist ensures your complaint reaches the right department without hassle.
              </p>
              <Link
                to="/how-it-works"
                data-testid="learn-more-link"
                className="inline-flex items-center gap-2 text-[#002FA7] hover:text-[#002280] font-bold uppercase tracking-wide transition-colors"
              >
                Learn More <ArrowRight size={16} weight="bold" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
