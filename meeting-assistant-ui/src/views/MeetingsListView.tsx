import React, { useState } from 'react';
import { Plus, X, Mic2, ChevronRight, LoaderCircle, FolderOpen } from 'lucide-react';
import { MeetingRecord, request, statusLabel, useResource } from '../lib/api';

export function MeetingsListView({ onSelectMeeting }: { onSelectMeeting: (id: string) => void }) {
  const { data: meetings, error, refresh } = useResource<MeetingRecord[]>('/api/meetings');
  const [projectFilter, setProjectFilter] = useState('');
  const [showUpload, setShowUpload] = useState(false);
  const [busy, setBusy] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const projects = [...new Set((meetings || []).map(meeting => meeting.project))];
  const filtered = (meetings || []).filter(meeting => !projectFilter || meeting.project === projectFilter);
  async function upload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setUploadError('');
    try {
      const data = new FormData(event.currentTarget);
      data.set('permission_confirmed', 'true');
      const meeting = await request<MeetingRecord>('/api/meetings', { method: 'POST', body: data });
      setShowUpload(false); refresh(); onSelectMeeting(meeting.id);
    } catch (error) { setUploadError(error instanceof Error ? error.message : 'Upload failed.'); }
    finally { setBusy(false); }
  }
  return (
    <div className="flex flex-col h-full bg-[#f2f2f7]">
      <header className="bg-white border-b border-gray-200 px-5 pt-14 pb-4">
        <div className="flex items-center justify-between">
          <div><p className="text-xs font-semibold tracking-widest text-blue-600 uppercase mb-1">Meeting workspace</p><h1 className="text-2xl font-bold text-gray-900">Meetings</h1></div>
          <button aria-label="Add meeting" onClick={() => { setUploadError(''); setShowUpload(true); }} className="bg-blue-600 text-white p-2.5 rounded-full hover:bg-blue-700"><Plus className="w-5 h-5" /></button>
        </div>
        <label className="block text-xs text-gray-500 mt-4 mb-1" htmlFor="project-filter">Project</label>
        <select id="project-filter" value={projectFilter} onChange={event => setProjectFilter(event.target.value)} className="w-full border border-gray-200 bg-gray-50 rounded-xl p-2 text-sm">
          <option value="">All projects</option>{projects.map(project => <option key={project}>{project}</option>)}
        </select>
      </header>
      <main className="flex-1 overflow-y-auto px-4 pt-4 pb-28 space-y-3">
        {error && <div role="alert" className="bg-red-50 border border-red-200 text-red-800 rounded-xl p-4 text-sm">{error}<button onClick={refresh} className="block mt-2 font-semibold underline">Retry connection</button></div>}
        {!meetings && !error && <p className="text-gray-500 text-sm py-8 text-center">Loading meetings…</p>}
        {meetings && filtered.length === 0 && <div className="text-center bg-white border border-gray-200 rounded-2xl px-6 py-12">
          <FolderOpen className="w-10 h-10 text-blue-400 mx-auto mb-4" /><h2 className="font-semibold text-gray-900">Your next meeting starts here</h2>
          <p className="text-sm text-gray-500 mt-2 mb-6">Upload a recording to get a transcript, summary, and cited action items.</p>
          <button onClick={() => setShowUpload(true)} className="bg-blue-600 text-white rounded-xl px-4 py-2.5 font-medium text-sm">Upload recording</button>
        </div>}
        {filtered.map(meeting => <button key={meeting.id} onClick={() => onSelectMeeting(meeting.id)} className="w-full text-left bg-white rounded-2xl p-4 border border-gray-200 shadow-sm hover:border-blue-300">
          <div className="flex items-start gap-3"><div className="bg-blue-50 rounded-xl p-2.5"><Mic2 className="w-5 h-5 text-blue-600" /></div>
            <div className="min-w-0 flex-1"><h2 className="font-semibold text-gray-900 truncate">{meeting.title}</h2><p className="text-xs text-gray-500 mt-1">{meeting.project} · {meeting.date}</p></div>
            <ChevronRight className="w-4 h-4 text-gray-400 mt-3 shrink-0" />
          </div>
          <p className={`text-xs font-medium mt-4 flex items-center gap-2 ${meeting.status === 'failed' ? 'text-red-600' : meeting.status === 'completed' ? 'text-emerald-700' : 'text-blue-600'}`}>
            {['queued', 'transcribing', 'extracting'].includes(meeting.status) && <LoaderCircle className="w-3.5 h-3.5 animate-spin" />}{statusLabel[meeting.status]}
          </p>
        </button>)}
      </main>
      {showUpload && <div className="absolute inset-0 z-[60] bg-black/40 backdrop-blur-sm p-4 flex items-center justify-center">
        <form onSubmit={upload} className="bg-white rounded-2xl p-5 w-full max-h-full overflow-y-auto shadow-xl">
          <div className="flex justify-between items-center mb-1"><h2 className="text-xl font-semibold">Add meeting</h2><button type="button" aria-label="Close upload" disabled={busy} onClick={() => setShowUpload(false)} className="p-2 rounded-full bg-gray-100"><X className="w-4 h-4" /></button></div>
          <p className="text-sm text-gray-500 mb-5">Turn a recording into meeting notes.</p>
          <label htmlFor="meeting-title" className="block text-xs font-medium text-gray-600 mb-1">Meeting title</label>
          <input id="meeting-title" name="title" required maxLength={200} placeholder="Weekly project sync" className="w-full border border-gray-200 rounded-lg px-3 py-2 mb-3" />
          <label htmlFor="meeting-project" className="block text-xs font-medium text-gray-600 mb-1">Project</label>
          <input id="meeting-project" name="project" required maxLength={100} defaultValue={projectFilter || 'Capstone'} className="w-full border border-gray-200 rounded-lg px-3 py-2 mb-3" />
          <label htmlFor="meeting-date" className="block text-xs font-medium text-gray-600 mb-1">Meeting date</label>
          <input id="meeting-date" name="meeting_date" type="date" required defaultValue={new Date().toLocaleDateString('en-CA')} className="w-full border border-gray-200 rounded-lg px-3 py-2 mb-3" />
          <label htmlFor="meeting-file" className="block text-xs font-medium text-gray-600 mb-1">Recording</label>
          <input id="meeting-file" name="file" type="file" accept=".wav,.mp3,.mp4,.m4a,.flac,.ogg,.webm,.mov" required className="w-full text-sm border border-gray-200 rounded-lg p-2" />
          <p className="text-xs text-gray-500 mt-1">Audio or video · up to 512 MB</p>
          <label className="flex gap-2 text-xs leading-relaxed text-gray-600 my-5"><input type="checkbox" required className="mt-1 shrink-0" /><span>I have written consent for this private recording, or permission to use this public audio. Its transcript will be sent to Codex for processing.</span></label>
          {uploadError && <p role="alert" className="text-sm text-red-700 bg-red-50 rounded-lg p-3 mb-3">{uploadError}</p>}
          <button disabled={busy} className="w-full bg-blue-600 disabled:bg-blue-300 text-white rounded-xl py-3 font-medium">{busy ? 'Uploading…' : 'Upload and process'}</button>
        </form>
      </div>}
    </div>
  );
}
