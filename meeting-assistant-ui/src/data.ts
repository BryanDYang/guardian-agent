import { Meeting, Task, Attendee, ChatMessage, ProjectWorkspace } from './types';

const ALICE: Attendee = { id: 'u1', name: 'Alice Chen', initials: 'AC', email: 'alice@example.com', color: 'bg-blue-500' };
const BOB: Attendee = { id: 'u2', name: 'Bob Smith', initials: 'BS', email: 'bob@example.com', color: 'bg-green-500' };
const CHARLIE: Attendee = { id: 'u3', name: 'Charlie Davis', initials: 'CD', email: 'charlie@example.com', color: 'bg-amber-500' };

export const mockProjects: ProjectWorkspace[] = [
  {
    id: 'p1',
    title: 'AI Thesis',
    colorHex: '#5E5CE6',
    iconSystemName: 'brain',
    createdAt: 'Aug 01, 2026',
    meetingIds: ['m1', 'm2']
  },
  {
    id: 'p2',
    title: 'Robotics Lab',
    colorHex: '#34C759',
    iconSystemName: 'cpu',
    createdAt: 'Aug 10, 2026',
    meetingIds: ['m3']
  },
  {
    id: 'p3',
    title: 'Capstone',
    colorHex: '#FF9500',
    iconSystemName: 'star',
    createdAt: 'Sept 01, 2026',
    meetingIds: []
  }
];

const generateWaveform = (length: number) => Array.from({ length }, () => Math.random() * 0.8 + 0.1);

export const mockMeetings: Meeting[] = [
  {
    id: 'm1',
    title: 'Weekly Thesis Sync',
    date: 'Sept 12, 2026',
    duration: '42m 15s',
    projectId: 'p1',
    waveformPeaks: generateWaveform(40),
    attendees: [ALICE, BOB, CHARLIE],
    summary: [
      'Agreed to pivot the ML architecture from standard RNNs to a transformer-based approach.',
      'Data labeling timeline is pushed back by one week due to resource constraints.',
      'Next steps involve setting up the AWS infrastructure for the new pipeline.'
    ],
    suggestions: [
      { id: 's1', text: 'Consider reviewing the new paper on efficient attention mechanisms before finalizing the model depth.' }
    ],
    decisions: [
      { id: 'd1', text: 'Adopt Transformer architecture for the core extraction module.', timestamp: '12:04' },
      { id: 'd2', text: 'Delay phase 2 user testing until Q4.', timestamp: '34:12' }
    ],
    candidateTasks: [
      {
        id: 'ct1',
        assignee: ALICE,
        description: 'Provision AWS EC2 instances for model training',
        quote: "I can go ahead and spin up the GPU instances by tomorrow morning.",
        timestamp: '14:32',
        dueDate: 'Sept 17'
      },
      {
        id: 'ct2',
        assignee: BOB,
        description: 'Update data labeling guidelines',
        quote: "I'll update the rubric for the labeling team since we shifted the timeline.",
        timestamp: '22:15',
        duplicateOf: 't123',
        dueDate: 'Sept 23'
      }
    ],
    transcript: [
      { id: 'tr1', speaker: ALICE, text: 'So looking at the latest results, the RNN just isn\'t converging fast enough on the larger dataset.', startTime: '11:45', endTime: '11:58' },
      { id: 'tr2', speaker: CHARLIE, text: 'I agree. Have we considered just moving to a transformer model? It might solve the context window issue.', startTime: '11:59', endTime: '12:10' },
      { id: 'tr3', speaker: ALICE, text: 'Yeah, let\'s adopt the Transformer architecture for the core extraction module. I can go ahead and spin up the GPU instances by tomorrow morning.', startTime: '14:20', endTime: '14:35' },
      { id: 'tr4', speaker: BOB, text: 'Sounds good. Also, since we are pushing the timeline, I\'ll update the rubric for the labeling team.', startTime: '22:10', endTime: '22:20' }
    ]
  },
  {
    id: 'm2',
    title: 'Baseline Review',
    date: 'Sept 05, 2026',
    duration: '38m 10s',
    projectId: 'p1',
    waveformPeaks: generateWaveform(35),
    attendees: [ALICE, BOB],
    summary: ['Reviewed baseline metrics.'],
    suggestions: [],
    decisions: [{ id: 'd3', text: 'Lock in baseline metrics.', timestamp: '10:00' }],
    candidateTasks: [],
    transcript: []
  },
  {
    id: 'm3',
    title: 'Hardware Procurement',
    date: 'Sept 15, 2026',
    duration: '22m 05s',
    projectId: 'p2',
    waveformPeaks: generateWaveform(25),
    attendees: [CHARLIE, BOB],
    summary: ['Finalized hardware specs.'],
    suggestions: [],
    decisions: [{ id: 'd4', text: 'Order 4 LiDAR sensors.', timestamp: '05:22' }],
    candidateTasks: [],
    transcript: []
  }
];

export const mockTasks: Task[] = [
  {
    id: 't123',
    title: 'Revise labeling instructions',
    state: 'Open',
    assignee: BOB,
    dueDate: '2026-09-16',
    sourceMeetingId: 'm0',
    sourceMeetingTitle: 'Prev Weekly Sync',
    sourceTimestamp: '08:15',
    project: 'Thesis Project'
  },
  {
    id: 't124',
    title: 'Draft literature review chapter 2',
    state: 'In-Progress',
    assignee: ALICE,
    dueDate: '2026-09-18',
    sourceMeetingId: 'm0',
    sourceMeetingTitle: 'Prev Weekly Sync',
    sourceTimestamp: '42:10',
    project: 'Thesis Project'
  },
  {
    id: 't125',
    title: 'Order new sensory modules',
    state: 'Open',
    assignee: CHARLIE,
    dueDate: '2026-09-16',
    sourceMeetingId: 'm3',
    sourceMeetingTitle: 'Hardware Procurement',
    sourceTimestamp: '10:00',
    project: 'Robotics Lab'
  }
];

export const mockChat: ChatMessage[] = [
  {
    id: 'msg1',
    role: 'user',
    content: 'What did we decide about the ML architecture in the last sync?'
  },
  {
    id: 'msg2',
    role: 'assistant',
    content: 'During the Weekly Thesis Sync on Aug 21, the team agreed to pivot the ML architecture from standard RNNs to a transformer-based approach to address context window issues.',
    citations: [
      { id: 'cit1', meetingId: 'm1', meetingTitle: 'Weekly Thesis Sync', timestamp: '12:04' }
    ]
  }
];
