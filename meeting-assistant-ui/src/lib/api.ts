import { useEffect, useState } from 'react';

export type JobStatus = 'queued' | 'transcribing' | 'extracting' | 'completed' | 'failed';
export interface MeetingRecord {
  id: string; title: string; project: string; date: string; created_at: string;
  status: JobStatus; diarization: boolean; error: string | null;
}
export interface Turn { id: string; speaker: string; start_time_ms: number; end_time_ms: number; content: string }
export interface Evidence { transcript_id: string; quote: string }
export interface Decision { statement: string; evidence: Evidence[] }
export interface Commitment { title: string; owner: string | null; due_date_text: string | null; evidence: Evidence[] }
export interface MeetingDetail extends MeetingRecord {
  audio_url: string;
  transcript: { turns: Turn[] } | null;
  extraction: { summary: string; decisions: Decision[]; commitments: Commitment[]; suggestions: Decision[] } | null;
}
export const statusLabel: Record<JobStatus, string> = {
  queued: 'Queued', transcribing: 'Transcribing audio', extracting: 'Extracting meeting notes',
  completed: 'Ready', failed: 'Needs attention',
};
export async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Request failed. Please try again.');
  }
  return response.json();
}
export function useResource<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const load = async () => {
      try {
        const result = await request<T>(url, { signal: controller.signal });
        if (!controller.signal.aborted) { setData(result); setError(''); }
      } catch (error) {
        if (!controller.signal.aborted) setError('Cannot reach the backend. Check that it is running, then retry.');
      }
      if (!controller.signal.aborted) timer = setTimeout(load, 2000);
    };
    void load();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [url, revision]);
  return { data, error, refresh: () => setRevision(value => value + 1) };
}
export function timestamp(milliseconds: number) {
  const total = Math.floor(milliseconds / 1000);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`;
}
