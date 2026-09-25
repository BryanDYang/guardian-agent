import React, { useState } from 'react';
import { mockChat, mockProjects } from '../data';
import { cn } from '../lib/utils';
import { meetingNavigation } from '../lib/events';
import { ChatMessage } from '../types';
import { 
  ChevronDown,
  Search,
  ArrowUp,
  Volume2,
  Menu,
  Notebook,
  Check
} from 'lucide-react';

const INITIAL_GREETING: ChatMessage = {
  id: 'greeting',
  role: 'assistant',
  content: 'What would you like to understand about this project?'
};

export function ChatView() {
  const [input, setInput] = useState('');
  const [playingCitation, setPlayingCitation] = useState<string | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isProjectDropdownOpen, setIsProjectDropdownOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(mockProjects[0]?.title || 'Thesis Project');
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_GREETING, ...mockChat]);
  const [activeHistoryProject, setActiveHistoryProject] = useState('All');

  const handleNewChat = () => {
    setMessages([INITIAL_GREETING]);
  };

  const mockHistoryItems = [
    { id: 'h1', title: 'Thesis research notes', project: 'AI Thesis', time: 'recent' },
    { id: 'h2', title: 'Literature review summary', project: 'AI Thesis', time: 'recent' },
    { id: 'h3', title: 'Robotics integration ideas', project: 'Robotics Lab', time: 'past_7_days' },
    { id: 'h4', title: 'Hardware specs meeting', project: 'Robotics Lab', time: 'past_7_days' },
    { id: 'h5', title: 'Capstone presentation prep', project: 'Capstone', time: 'recent' }
  ];

  const filteredHistory = mockHistoryItems.filter(h => activeHistoryProject === 'All' || h.project === activeHistoryProject);
  const recentHistory = filteredHistory.filter(h => h.time === 'recent');
  const pastHistory = filteredHistory.filter(h => h.time === 'past_7_days');

  return (
    <div className="flex flex-col h-full bg-white relative">
      {/* Slide-out Drawer */}
      {isDrawerOpen && (
        <div className="absolute inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/20 backdrop-blur-sm transition-opacity" onClick={() => setIsDrawerOpen(false)} />
          <div className="relative w-[70%] h-full bg-white shadow-xl animate-in slide-in-from-left duration-300 z-50 flex flex-col">
            <div className="p-4 pt-12 border-b border-gray-200">
              <h2 className="text-lg font-bold text-gray-900 truncate">Chat History</h2>
            </div>
            
            <div className="flex overflow-x-auto no-scrollbar py-3 px-4 border-b border-gray-100 space-x-2 shrink-0">
              {['All', ...mockProjects.map(p => p.title)].map(proj => (
                <button
                  key={proj}
                  onClick={() => setActiveHistoryProject(proj)}
                  className={cn(
                    "px-3 py-1.5 text-sm font-medium rounded-full whitespace-nowrap transition-all",
                    activeHistoryProject === proj ? "bg-gray-900 text-white shadow-sm" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  )}
                >
                  {proj}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6">
              {recentHistory.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Recent</h3>
                  <div className="space-y-1 text-sm text-gray-700 font-medium">
                    {recentHistory.map(item => (
                      <button key={item.id} className="w-full text-left p-2 rounded-lg hover:bg-gray-100 transition-colors">
                        {item.title}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {pastHistory.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Previous 7 Days</h3>
                  <div className="space-y-1 text-sm text-gray-700 font-medium">
                    {pastHistory.map(item => (
                      <button key={item.id} className="w-full text-left p-2 rounded-lg hover:bg-gray-100 transition-colors">
                        {item.title}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {recentHistory.length === 0 && pastHistory.length === 0 && (
                <div className="text-sm text-gray-500 text-center py-4">No chat history found.</div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white/90 backdrop-blur-md border-b border-gray-200 px-4 pt-12 pb-3 shrink-0 absolute top-0 left-0 right-0 z-10 flex justify-between items-center">
        <button onClick={() => setIsDrawerOpen(true)} className="p-2 -ml-2 text-gray-500 hover:text-gray-900 transition-colors">
          <Menu className="w-6 h-6" />
        </button>
        <div className="relative">
          <button 
            onClick={() => setIsProjectDropdownOpen(!isProjectDropdownOpen)}
            className="flex items-center space-x-1 bg-gray-100 hover:bg-gray-200 transition-colors px-3 py-1.5 rounded-full"
          >
            <span className="text-sm font-semibold text-gray-900 truncate max-w-[120px]">{selectedProject}</span>
            <ChevronDown className={cn("w-4 h-4 text-gray-500 transition-transform", isProjectDropdownOpen && "rotate-180")} />
          </button>
          
          {isProjectDropdownOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setIsProjectDropdownOpen(false)} />
              <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-48 bg-white rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.1)] border border-gray-100 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2">
                {mockProjects.map(proj => (
                  <button
                    key={proj.id}
                    onClick={() => { setSelectedProject(proj.title); setIsProjectDropdownOpen(false); }}
                    className="w-full flex items-center justify-between px-4 py-3 text-sm hover:bg-gray-50 text-gray-700 border-b border-gray-50 last:border-0 transition-colors"
                  >
                    <span className={cn(selectedProject === proj.title && "font-semibold text-blue-600")}>
                      {proj.title}
                    </span>
                    {selectedProject === proj.title && <Check className="w-4 h-4 text-blue-600" />}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
        <button onClick={handleNewChat} className="p-2 -mr-2 text-gray-500 hover:text-blue-600 transition-colors" title="New Chat">
          <Notebook className="w-5 h-5" />
        </button>
      </div>

      {/* Chat Feed */}
      <div className="flex-1 overflow-y-auto px-4 pt-28 pb-32 space-y-6">
        {messages.map(msg => {
          const isUser = msg.role === 'user';
          return (
            <div key={msg.id} className={cn("flex flex-col", isUser ? "items-end" : "items-start")}>
              <div className={cn(
                "max-w-[85%] rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed",
                isUser ? "bg-blue-600 text-white rounded-br-sm" : "bg-gray-100 text-gray-900 rounded-bl-sm"
              )}>
                {msg.content}
              </div>
              
              {/* Citations */}
              {!isUser && msg.citations && msg.citations.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {msg.citations.map(cit => (
                    <button 
                      key={cit.id} 
                      onClick={() => meetingNavigation.navigate(cit.meetingId, 'transcript')}
                      className="flex items-center space-x-1.5 bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 px-2.5 py-1.5 rounded-full text-xs font-semibold transition-colors active:scale-95 shadow-sm"
                    >
                      <span>{cit.meetingTitle} @ {cit.timestamp}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Input Bar */}
      <div className="absolute bottom-[83px] left-0 right-0 bg-white border-t border-gray-200 p-4 shrink-0 pb-safe z-20">
        
        {/* Floating Mini Audio Player for Citation */}
        {playingCitation && (
          <div className="absolute bottom-[100%] left-4 right-4 mb-4 bg-gray-900 text-white rounded-2xl p-3 shadow-xl animate-in slide-in-from-bottom-2 flex items-center justify-between z-30">
            <div className="flex items-center space-x-3">
               <button className="w-8 h-8 rounded-full bg-white text-gray-900 flex items-center justify-center shrink-0">
                 <Volume2 className="w-4 h-4 ml-0.5" />
               </button>
               <div>
                 <p className="text-xs font-semibold">Playing Citation Audio</p>
                 <p className="text-[10px] text-gray-400">Weekly Thesis Sync @ 12:04</p>
               </div>
            </div>
            <button 
              onClick={() => setPlayingCitation(null)}
              className="text-gray-400 hover:text-white p-2"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="relative flex items-end bg-gray-100 rounded-3xl border border-gray-200 focus-within:border-gray-300 focus-within:ring-2 focus-within:ring-blue-100 transition-all p-1">
          <div className="absolute left-3 bottom-3 text-gray-400">
            <Search className="w-5 h-5" />
          </div>
          <textarea 
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask about past decisions..."
            className="w-full bg-transparent border-none outline-none resize-none max-h-32 min-h-[40px] pl-10 pr-12 py-2.5 text-[15px] text-gray-900 placeholder:text-gray-500 overflow-y-auto"
            rows={1}
          />
          <button 
            disabled={!input.trim()}
            className={cn(
              "absolute right-1.5 bottom-1.5 p-2 rounded-full transition-all shrink-0",
              input.trim() ? "bg-blue-600 text-white" : "bg-gray-300 text-white"
            )}
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
