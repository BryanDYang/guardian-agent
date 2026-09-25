export type Tab = 'meetings' | 'tasks' | 'chat';

export type TaskState = 'Open' | 'In-Progress' | 'Blocked' | 'Done' | 'Dropped';

export interface Attendee {
  id: string;
  name: string;
  initials: string;
  email: string;
  color: string;
}

export interface ProjectWorkspace {
  id: string;
  title: string;
  colorHex: string;
  iconSystemName: string;
  createdAt: string;
  meetingIds: string[];
}

export interface Meeting {
  id: string;
  title: string;
  date: string;
  duration: string;
  projectId?: string;
  waveformPeaks?: number[];
  attendees: Attendee[];
  summary: string[];
  suggestions: Suggestion[];
  decisions: Decision[];
  candidateTasks: CandidateTask[];
  transcript: TranscriptTurn[];
}

export interface Suggestion {
  id: string;
  text: string;
}

export interface Decision {
  id: string;
  text: string;
  timestamp: string;
}

export interface CandidateTask {
  id: string;
  assignee: Attendee;
  description: string;
  quote: string;
  timestamp: string;
  duplicateOf?: string; // ID of existing task
  dueDate?: string;
}

export interface Task {
  id: string;
  title: string;
  state: TaskState;
  assignee: Attendee;
  dueDate?: string;
  sourceMeetingId: string;
  sourceMeetingTitle: string;
  sourceTimestamp: string;
  project: string;
}

export interface TranscriptTurn {
  id: string;
  speaker: Attendee;
  text: string;
  startTime: string;
  endTime: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

export interface Citation {
  id: string;
  meetingId: string;
  meetingTitle: string;
  timestamp: string;
}
