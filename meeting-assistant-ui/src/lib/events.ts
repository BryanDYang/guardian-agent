type NavigateToMeetingEvent = {
  meetingId: string;
  segment?: 'summary' | 'tasks' | 'transcript' | 'storyline';
};

type Listener = (e: NavigateToMeetingEvent) => void;

let listeners: Listener[] = [];
let pendingNav: NavigateToMeetingEvent | null = null;

export const meetingNavigation = {
  subscribe(listener: Listener) {
    listeners.push(listener);
    return () => {
      listeners = listeners.filter(l => l !== listener);
    };
  },
  navigate(meetingId: string, segment?: 'summary' | 'tasks' | 'transcript' | 'storyline') {
    const event = { meetingId, segment };
    pendingNav = event;
    listeners.forEach(l => l(event));
  },
  getPending() {
    return pendingNav;
  },
  clearPending() {
    pendingNav = null;
  }
};
