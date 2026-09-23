import React, { useState, useEffect } from 'react';
import { Tab } from './types';
import { MeetingsTab } from './views/MeetingsTab';
import { Mic2, CheckSquare, MessageSquare } from 'lucide-react';
import { cn } from './lib/utils';
import { meetingNavigation } from './lib/events';

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('meetings');

  useEffect(() => {
    const unsubscribe = meetingNavigation.subscribe(() => {
      setActiveTab('meetings');
    });
    return unsubscribe;
  }, []);

  return (
    <div className="h-screen w-full flex justify-center bg-gray-900 font-sans sm:p-8">
      {/* iOS Device Frame Constraint (for preview purposes on desktop) */}
      <div className="w-full h-full sm:max-w-[400px] sm:h-full sm:max-h-[850px] bg-white sm:rounded-[3rem] sm:shadow-2xl sm:border-[8px] sm:border-black overflow-hidden relative shadow-[0_0_50px_rgba(0,0,0,0.5)]">
        
        {/* Dynamic Island / Status Bar spacer */}
        <div className="absolute top-0 w-full h-12 z-50 pointer-events-none flex justify-center items-start pt-2">
           <div className="w-32 h-7 bg-black rounded-full hidden sm:block"></div>
        </div>

        {/* Main Content Area */}
        <div className="h-full w-full relative">
          {activeTab === 'meetings' && <MeetingsTab />}
          {activeTab === 'tasks' && <PendingFeature title="Task workspace" message="Review extracted commitments inside each meeting. Task approval and tracking are not connected yet." />}
          {activeTab === 'chat' && <PendingFeature title="Project chat" message="Project question answering is not connected yet. Open a meeting to explore its transcript and cited notes." />}
        </div>

        {/* Global Bottom Tab Bar */}
        <div className="absolute bottom-0 left-0 right-0 h-[83px] bg-white/80 backdrop-blur-xl border-t border-gray-200 flex justify-around items-start pt-2 px-2 z-50">
          <TabButton 
            icon={<Mic2 className="w-6 h-6" />} 
            label="Meetings" 
            isActive={activeTab === 'meetings'} 
            onClick={() => setActiveTab('meetings')} 
          />
          <TabButton 
            icon={<CheckSquare className="w-6 h-6" />} 
            label="Tasks" 
            isActive={activeTab === 'tasks'} 
            onClick={() => setActiveTab('tasks')} 
          />
          <TabButton 
            icon={<MessageSquare className="w-6 h-6" />} 
            label="Chat" 
            isActive={activeTab === 'chat'} 
            onClick={() => setActiveTab('chat')} 
          />
        </div>
      </div>
    </div>
  );
}

function TabButton({ icon, label, isActive, onClick }: { icon: React.ReactNode, label: string, isActive: boolean, onClick: () => void }) {
  return (
    <button 
      onClick={onClick}
      className={cn(
        "flex flex-col items-center justify-center w-16 h-12 transition-colors",
        isActive ? "text-blue-600" : "text-gray-500 hover:text-gray-900"
      )}
    >
      <div className={cn("mb-1", isActive && "scale-110 transition-transform duration-200")}>
        {icon}
      </div>
      <span className="text-[10px] font-medium tracking-wide">{label}</span>
    </button>
  );
}


function PendingFeature({ title, message }: { title: string; message: string }) { return <div className="px-6 pt-16"><h1 className="text-2xl font-bold mb-4">{title}</h1><p className="text-sm text-gray-500 leading-relaxed">{message}</p></div>; }
