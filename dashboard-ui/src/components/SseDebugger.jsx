import React, { useState } from 'react';
import { Terminal, Play, Radio, CheckCircle, RefreshCw, Send } from 'lucide-react';
import { createSession, postTurn } from '../services/api';

export default function SseDebugger() {
  const [sessionId, setSessionId] = useState('');
  const [turnId, setTurnId] = useState('');
  const [promptText, setPromptText] = useState('cortex explain --question "Why did we choose Redis over Postgres?"');
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState('Idle');

  async function handleStartSession() {
    setStatus('Creating TrueForge Session (POST /api/v1/sessions)...');
    try {
      const session = await createSession('codebase-cortex');
      const sid = session.id || session.session?.id;
      setSessionId(sid);
      setStatus(`Session created: ${sid}`);
    } catch (err) {
      setStatus(`Error creating session: ${err.message}`);
    }
  }

  async function handleSendTurn() {
    if (!sessionId) {
      alert('Please create a session first.');
      return;
    }
    setStatus('Posting turn to TrueForge (POST /api/v1/sessions/{id}/turns)...');
    try {
      const turn = await postTurn(sessionId, promptText);
      const tid = turn.turn_id || turn.id;
      setTurnId(tid);
      setStatus(`Turn queued: ${tid}. Subscribing SSE stream...`);

      // SSE connection
      const sseUrl = `http://localhost:8790/api/v1/sessions/${sessionId}/turns/${tid}/subscribe`;
      const es = new EventSource(sseUrl);

      es.onmessage = (e) => {
        setEvents((prev) => [...prev, { time: new Date().toLocaleTimeString(), text: e.data }]);
      };
      es.onerror = () => {
        setStatus('SSE stream ended or disconnected.');
        es.close();
      };
    } catch (err) {
      setStatus(`Error posting turn: ${err.message}`);
    }
  }

  return (
    <div className="max-w-4xl mx-auto w-full space-y-6">
      <div>
        <h2 className="text-xl font-bold text-[#141413] tracking-tight">
          TrueForge REST & SSE Stream Debugger
        </h2>
        <p className="text-xs text-[#5c5c5a]">
          Direct REST and Server-Sent Events (SSE) communication console connecting to TrueForge daemon on port 8790.
        </p>
      </div>

      <div className="bg-white border border-[#e5e4df] rounded-xl p-6 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleStartSession}
            className="bg-[#141413] hover:bg-black text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-2"
          >
            <Play className="w-3.5 h-3.5 text-emerald-400" />
            1. POST /sessions
          </button>

          <span className="text-xs font-mono text-[#5c5c5a]">
            Session ID: <strong className="text-[#141413]">{sessionId || '(none)'}</strong>
          </span>
        </div>

        <div className="space-y-2">
          <label className="text-xs font-bold text-[#8c8c8a] uppercase tracking-wider">
            2. Turn User Input
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              className="flex-1 bg-[#f5f4ef] border border-[#e5e4df] rounded-lg px-3 py-2 text-xs font-mono text-[#141413] outline-none"
            />
            <button
              onClick={handleSendTurn}
              className="bg-[#D97757] hover:bg-[#c4684a] text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-2"
            >
              <Send className="w-3.5 h-3.5" />
              POST /turns
            </button>
          </div>
        </div>

        <div className="bg-[#f5f4ef] p-3 rounded-lg border border-[#e5e4df] text-xs font-mono text-[#5c5c5a] flex items-center gap-2">
          <Radio className="w-4 h-4 text-emerald-600 animate-pulse" />
          <span>Status: {status}</span>
        </div>
      </div>

      <div className="bg-[#141413] text-emerald-400 p-5 rounded-xl border border-zinc-800 space-y-3 font-mono text-xs shadow-md">
        <div className="flex justify-between items-center text-zinc-400 border-b border-zinc-800 pb-2">
          <span className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-emerald-400" />
            Live SSE Turn Output Stream
          </span>
          <span>GET /sessions/{sessionId || '{id}'}/turns/{turnId || '{turnId}'}/subscribe</span>
        </div>

        <div className="h-64 overflow-y-auto space-y-1 pr-2">
          {events.length === 0 ? (
            <span className="text-zinc-600 italic">Waiting for SSE events...</span>
          ) : (
            events.map((ev, idx) => (
              <div key={idx} className="flex gap-2">
                <span className="text-zinc-500">[{ev.time}]</span>
                <span className="text-emerald-300">{ev.text}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
