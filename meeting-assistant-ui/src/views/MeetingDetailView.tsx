import React, { useRef, useState } from 'react';
import { ChevronLeft, LoaderCircle, CheckCircle2, AlertCircle } from 'lucide-react';
import { Evidence, MeetingDetail, request, statusLabel, timestamp, useResource } from '../lib/api';

export function MeetingDetailView({ meetingId, onBack }: { meetingId: string; onBack: () => void }) {
  const { data: meeting, error, refresh } = useResource<MeetingDetail>(`/api/meetings/${meetingId}`);
  const [tab, setTab] = useState<'summary' | 'tasks' | 'transcript'>('summary');
  const [actionError, setActionError] = useState('');
  const [retrying, setRetrying] = useState(false);
  const [playbackError, setPlaybackError] = useState('');
  const [currentTime, setCurrentTime] = useState(0);
  const audio = useRef<HTMLAudioElement>(null);
  const turns = meeting?.transcript?.turns || [];
  function seek(id: string) {
    const turn = turns.find(turn => turn.id === id);
    if (audio.current && turn) {
      audio.current.currentTime = turn.start_time_ms / 1000;
      void audio.current.play().catch(() => setPlaybackError('Press play to listen to this recording.'));
    }
  }
  function evidence(entries: Evidence[]) {
    return <div className="space-y-2 mt-3">{entries.map((item, i) => {
      const turn = turns.find(turn => turn.id === item.transcript_id);
      return <button key={i} onClick={() => seek(item.transcript_id)} className="block text-left w-full bg-blue-50 rounded-lg p-3 text-xs text-blue-900">
        <span className="font-mono font-semibold">{turn ? timestamp(turn.start_time_ms) : 'Source'}</span><span className="ml-2">“{item.quote}”</span>
      </button>;
    })}</div>;
  }
  async function retry() {
    setRetrying(true); setActionError('');
    try { await request(`/api/meetings/${meetingId}/retry`, { method: 'POST' }); refresh(); }
    catch (error) { setActionError(error instanceof Error ? error.message : 'Retry failed.'); }
    finally { setRetrying(false); }
  }
  const processing = meeting && ['queued', 'transcribing', 'extracting'].includes(meeting.status);
  return <div className="h-full flex flex-col bg-[#f2f2f7]">
    <header className="bg-white border-b border-gray-200 px-4 pt-14 pb-3">
      <button onClick={onBack} className="text-blue-600 flex items-center gap-1 text-sm mb-3"><ChevronLeft className="w-4 h-4" />Meetings</button>
      <h1 className="text-xl font-bold text-gray-900 break-words">{meeting?.title || 'Meeting'}</h1>
      {meeting && <p className="text-xs text-gray-500 mt-1 mb-4">{meeting.project} · {meeting.date}</p>}
      <div className="flex bg-gray-100 rounded-lg p-1 mt-3">{(['summary', 'tasks', 'transcript'] as const).map(item =>
        <button key={item} onClick={() => setTab(item)} className={`flex-1 text-sm rounded-md py-2 capitalize ${tab === item ? 'bg-white shadow-sm font-semibold' : 'text-gray-500'}`}>{item === 'tasks' ? 'Commitments' : item}</button>
      )}</div>
    </header>
    <main className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
      {error && <p role="alert" className="text-red-700 bg-red-50 rounded-xl p-3 text-sm">{error}</p>}
      {!meeting && !error && <p className="text-sm text-gray-500">Loading meeting…</p>}
      {meeting && <div className="bg-white border border-gray-200 rounded-xl p-3">
        <div role="status" className="flex gap-2 items-center text-sm font-medium">
          {processing ? <LoaderCircle className="w-4 h-4 animate-spin text-blue-600" /> : meeting.status === 'completed' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <AlertCircle className="w-4 h-4 text-red-600" />}
          {statusLabel[meeting.status]}
        </div>
        {processing && <p className="text-xs text-gray-500 mt-2">You can leave this screen. Processing continues in the background.</p>}
        {meeting.status === 'failed' && <><p role="alert" className="text-sm text-red-700 mt-2">{meeting.error}</p><button disabled={retrying} onClick={retry} className="mt-3 text-sm text-blue-600 font-semibold">{retrying ? 'Retrying…' : 'Retry processing'}</button></>}
        {!meeting.diarization && <p className="text-xs text-gray-500 mt-2">Speakers are unidentified. Speaker separation was not enabled for this recording.</p>}
        {actionError && <p role="alert" className="text-red-700 text-sm mt-2">{actionError}</p>}
      </div>}
      {tab === 'summary' && meeting?.extraction && <>
        <section className="bg-white border border-gray-200 rounded-xl p-4"><h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-3">Summary</h2><p className="text-sm text-gray-800 leading-relaxed">{meeting.extraction.summary || 'No summary returned.'}</p></section>
        <section><h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-3">Decisions</h2>
          {meeting.extraction.decisions.length === 0 && <p className="text-sm text-gray-500">No agreed decisions were extracted.</p>}
          {meeting.extraction.decisions.map((item, index) => <div key={index} className="bg-white rounded-xl border p-4 mb-3 text-sm">{item.statement}{evidence(item.evidence)}</div>)}
        </section>
        <section><h2 className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-3">Suggestions</h2>
          {meeting.extraction.suggestions.length === 0 && <p className="text-sm text-gray-500">No suggestions were extracted.</p>}
          {meeting.extraction.suggestions.map((item, index) => <div key={index} className="bg-white rounded-xl border p-4 mb-3 text-sm">{item.statement}{evidence(item.evidence)}</div>)}
        </section>
      </>}
      {tab === 'tasks' && meeting?.extraction && <>
        <p className="text-xs text-gray-500">Extracted commitments need review. They have not been added to a task tracker.</p>
        {meeting.extraction.commitments.length === 0 && <div className="bg-white border border-gray-200 rounded-xl p-6 text-sm text-gray-500">No explicit commitments were extracted.</div>}
        {meeting.extraction.commitments.map((task, index) => <div key={index} className="bg-white rounded-xl border p-4">
          <p className="text-xs text-gray-500 mb-2">{task.owner || 'Unassigned'}{task.due_date_text ? ` · Deadline mentioned: ${task.due_date_text}` : ''}</p>
          <h2 className="font-semibold text-sm">{task.title}</h2>{evidence(task.evidence)}
        </div>)}
      </>}
      {tab === 'transcript' && turns.map(turn => <button key={turn.id} onClick={() => seek(turn.id)} className={`w-full text-left border border-gray-200 rounded-xl p-4 ${currentTime * 1000 >= turn.start_time_ms && currentTime * 1000 < turn.end_time_ms ? 'bg-blue-50 border-blue-300' : 'bg-white border-gray-200'}`}>
        <div className="flex justify-between text-xs text-gray-500 mb-2"><span>{turn.speaker === 'UNKNOWN' ? 'Unidentified speaker' : turn.speaker}</span><span className="font-mono">{timestamp(turn.start_time_ms)}</span></div>
        <p className="text-sm text-gray-800 leading-relaxed">{turn.content}</p>
      </button>)}
      {meeting && ((tab === 'transcript' && !meeting.transcript) || (tab !== 'transcript' && !meeting.extraction)) && <p className="text-sm text-gray-500 py-6 text-center">Results will appear here as processing completes.</p>}
    </main>
    {meeting && <footer className="bg-white border-t border-gray-200 px-4 pt-3 pb-[96px]">
      <audio ref={audio} controls preload="metadata" src={meeting.audio_url} onTimeUpdate={() => setCurrentTime(audio.current?.currentTime || 0)} onError={() => setPlaybackError('This browser cannot play the recording. Try a WAV or MP3 file.')} className="w-full h-10" />
      {playbackError && <p role="alert" className="text-xs text-red-600 mt-1">{playbackError}</p>}
    </footer>}
  </div>;
}
