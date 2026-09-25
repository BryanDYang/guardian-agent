import React, { useState, useEffect } from 'react';
import { MeetingsListView } from './MeetingsListView';
import { MeetingDetailView } from './MeetingDetailView';
import { meetingNavigation } from '../lib/events';

export function MeetingsTab() {
  const [selectedMeetingId, setSelectedMeetingId] = useState<string | null>(() => {
    const pending = meetingNavigation.getPending();
    return pending ? pending.meetingId : null;
  });

  useEffect(() => {
    const unsubscribe = meetingNavigation.subscribe((e) => {
      setSelectedMeetingId(e.meetingId);
    });
    return unsubscribe;
  }, []);

  return (
    <div className="h-full w-full relative">
      <div className={selectedMeetingId ? 'hidden' : 'h-full w-full'}>
        <MeetingsListView onSelectMeeting={setSelectedMeetingId} />
      </div>
      {selectedMeetingId && (
        <div className="absolute inset-0 z-10 bg-[#f2f2f7]">
          <MeetingDetailView 
            meetingId={selectedMeetingId} 
            onBack={() => setSelectedMeetingId(null)} 
          />
        </div>
      )}
    </div>
  );
}
