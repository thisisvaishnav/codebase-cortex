import React from 'react';
import { ShieldCheck, Database, Server, Terminal, Sparkles, Activity } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, tfHealth, vecHealth }) {
  return (
    <header className="bg-white border-b border-[#e5e4df] px-6 py-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 flex-shrink-0">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-[#D97757] flex items-center justify-center text-white shadow-sm">
          <ShieldCheck className="w-5.5 h-5.5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-[#141413] tracking-tight">Codebase Cortex</h1>
            <span className="text-[10px] font-semibold bg-[#D97757]/10 text-[#D97757] px-2 py-0.5 rounded-md uppercase tracking-wider">
              v1.0 Live
            </span>
          </div>
          <p className="text-xs text-[#5c5c5a]">Institutional Memory & Architectural Guard for TrueForge</p>
        </div>
      </div>

      <div className="flex items-center gap-2 bg-[#f5f4ef] p-1 rounded-lg border border-[#e5e4df] text-xs font-medium">
        <button
          onClick={() => setActiveTab('explain')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
            activeTab === 'explain'
              ? 'bg-white text-[#141413] shadow-sm font-semibold'
              : 'text-[#8c8c8a] hover:text-[#141413]'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-[#D97757]" />
          Institutional Q&A
        </button>

        <button
          onClick={() => setActiveTab('lineage')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
            activeTab === 'lineage'
              ? 'bg-white text-[#141413] shadow-sm font-semibold'
              : 'text-[#8c8c8a] hover:text-[#141413]'
          }`}
        >
          <Database className="w-3.5 h-3.5 text-emerald-600" />
          ADR Lineage Graph
        </button>

        <button
          onClick={() => setActiveTab('violations')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
            activeTab === 'violations'
              ? 'bg-white text-[#141413] shadow-sm font-semibold'
              : 'text-[#8c8c8a] hover:text-[#141413]'
          }`}
        >
          <Activity className="w-3.5 h-3.5 text-amber-600" />
          Violation & Drift Feed
        </button>

        <button
          onClick={() => setActiveTab('debugger')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all ${
            activeTab === 'debugger'
              ? 'bg-white text-[#141413] shadow-sm font-semibold'
              : 'text-[#8c8c8a] hover:text-[#141413]'
          }`}
        >
          <Terminal className="w-3.5 h-3.5 text-blue-600" />
          TrueForge SSE
        </button>
      </div>

      <div className="flex items-center gap-3 text-xs">
        <div className="flex items-center gap-1.5 bg-[#f5f4ef] px-2.5 py-1 rounded-md border border-[#e5e4df]">
          <Server className="w-3 h-3 text-[#5c5c5a]" />
          <span className="text-[#5c5c5a]">TrueForge :8790</span>
          <span className={`w-2 h-2 rounded-full ${tfHealth?.ok ? 'bg-emerald-500' : 'bg-rose-500'}`} />
        </div>

        <div className="flex items-center gap-1.5 bg-[#f5f4ef] px-2.5 py-1 rounded-md border border-[#e5e4df]">
          <Database className="w-3 h-3 text-[#5c5c5a]" />
          <span className="text-[#5c5c5a]">Vector MCP :9001</span>
          <span className={`w-2 h-2 rounded-full ${vecHealth?.ok ? 'bg-emerald-500' : 'bg-amber-500'}`} />
        </div>
      </div>
    </header>
  );
}
