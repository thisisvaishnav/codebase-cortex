import React, { useState, useEffect } from 'react';
import { Database, Filter, ArrowRight, User, Calendar, GitCommit, FileText, AlertCircle, CheckCircle, ShieldCheck } from 'lucide-react';
import { fetchListDecisions, traceLineage } from '../services/api';

export default function LineageGraph() {
  const [adrs, setAdrs] = useState([]);
  const [filter, setFilter] = useState('ALL'); // ALL | ACTIVE | SUPERSEDED
  const [selectedAdr, setSelectedAdr] = useState(null);
  const [lineageChain, setLineageChain] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAdrs();
  }, []);

  async function loadAdrs() {
    setLoading(true);
    const data = await fetchListDecisions(true);
    setAdrs(data);
    if (data.length > 0) {
      handleSelectAdr(data[0]);
    }
    setLoading(false);
  }

  async function handleSelectAdr(adr) {
    setSelectedAdr(adr);
    const res = await traceLineage(adr.id);
    setLineageChain(res.chain || [adr]);
  }

  const filteredAdrs = adrs.filter((a) => {
    if (filter === 'ACTIVE') return a.status === 'ACTIVE';
    if (filter === 'SUPERSEDED') return a.status === 'SUPERSEDED';
    return true;
  });

  return (
    <div className="max-w-6xl mx-auto w-full space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-[#141413] tracking-tight">
            ADR Visual Timeline & Lineage Graph
          </h2>
          <p className="text-xs text-[#5c5c5a]">
            Interactive visualization of architectural decision records, active invariants, and superseded history.
          </p>
        </div>

        <div className="flex items-center gap-2 bg-white border border-[#e5e4df] p-1 rounded-lg text-xs font-medium">
          <Filter className="w-3.5 h-3.5 text-[#8c8c8a] ml-2" />
          <button
            onClick={() => setFilter('ALL')}
            className={`px-3 py-1 rounded-md transition-all ${
              filter === 'ALL' ? 'bg-[#f5f4ef] text-[#141413] font-bold' : 'text-[#8c8c8a]'
            }`}
          >
            All ({adrs.length})
          </button>
          <button
            onClick={() => setFilter('ACTIVE')}
            className={`px-3 py-1 rounded-md transition-all ${
              filter === 'ACTIVE' ? 'bg-emerald-50 text-emerald-700 font-bold' : 'text-[#8c8c8a]'
            }`}
          >
            Active ({adrs.filter((a) => a.status === 'ACTIVE').length})
          </button>
          <button
            onClick={() => setFilter('SUPERSEDED')}
            className={`px-3 py-1 rounded-md transition-all ${
              filter === 'SUPERSEDED' ? 'bg-amber-50 text-amber-700 font-bold' : 'text-[#8c8c8a]'
            }`}
          >
            Superseded ({adrs.filter((a) => a.status === 'SUPERSEDED').length})
          </button>
        </div>
      </div>

      {loading ? (
        <div className="bg-white border border-[#e5e4df] rounded-xl p-12 text-center text-sm text-[#8c8c8a]">
          Loading indexed decision records...
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 space-y-3 max-h-[600px] overflow-y-auto pr-1">
            {filteredAdrs.map((adr) => {
              const isSelected = selectedAdr?.id === adr.id;
              return (
                <div
                  key={adr.id}
                  onClick={() => handleSelectAdr(adr)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-white border-2 border-[#D97757] shadow-sm'
                      : 'bg-white border-[#e5e4df] hover:border-[#8c8c8a]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold text-xs text-[#D97757] font-mono">{adr.id}</span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded text-white ${
                        adr.status === 'ACTIVE' ? 'bg-emerald-600' : 'bg-amber-600'
                      }`}
                    >
                      {adr.status}
                    </span>
                  </div>

                  <h3 className="text-xs font-semibold text-[#141413] leading-snug mb-2">
                    {adr.title}
                  </h3>

                  <div className="flex items-center justify-between text-[11px] text-[#8c8c8a]">
                    <span>@{adr.author}</span>
                    <span>{adr.date}</span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="lg:col-span-7 space-y-6">
            {selectedAdr && (
              <>
                <div className="bg-white border border-[#e5e4df] rounded-xl p-5 shadow-sm space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-[#8c8c8a]">
                    Lineage Chain for {selectedAdr.id}
                  </h3>

                  <div className="flex items-center gap-3 overflow-x-auto pb-2">
                    {lineageChain.map((item, idx) => (
                      <React.Fragment key={item.id}>
                        <div
                          className={`p-3 rounded-lg border text-xs min-w-[200px] space-y-1 ${
                            item.id === selectedAdr.id
                              ? 'bg-[#D97757]/10 border-[#D97757]'
                              : 'bg-[#f5f4ef] border-[#e5e4df]'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-[#D97757]">{item.id}</span>
                            <span
                              className={`text-[9px] font-bold px-1.5 py-0.5 rounded text-white ${
                                item.status === 'ACTIVE' ? 'bg-emerald-600' : 'bg-amber-600'
                              }`}
                            >
                              {item.status}
                            </span>
                          </div>
                          <div className="font-medium text-[#141413] truncate">{item.title}</div>
                        </div>
                        {idx < lineageChain.length - 1 && (
                          <ArrowRight className="w-4 h-4 text-[#8c8c8a] flex-shrink-0" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>

                <div className="bg-white border border-[#e5e4df] rounded-xl p-6 shadow-sm space-y-5">
                  <div className="flex items-start justify-between border-b border-[#e5e4df] pb-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-bold text-[#D97757] font-mono">{selectedAdr.id}</span>
                        <span
                          className={`text-xs font-bold px-2.5 py-0.5 rounded text-white ${
                            selectedAdr.status === 'ACTIVE' ? 'bg-emerald-600' : 'bg-amber-600'
                          }`}
                        >
                          {selectedAdr.status}
                        </span>
                      </div>
                      <h3 className="text-base font-bold text-[#141413]">{selectedAdr.title}</h3>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-xs bg-[#f5f4ef] p-3 rounded-lg border border-[#e5e4df]">
                    <div>
                      <span className="text-[#8c8c8a] block text-[10px] uppercase font-bold">Author</span>
                      <span className="font-semibold text-[#141413]">@{selectedAdr.author}</span>
                    </div>
                    <div>
                      <span className="text-[#8c8c8a] block text-[10px] uppercase font-bold">Date</span>
                      <span className="font-semibold text-[#141413]">{selectedAdr.date}</span>
                    </div>
                    {selectedAdr.merged_pr && (
                      <div>
                        <span className="text-[#8c8c8a] block text-[10px] uppercase font-bold">Merged PR</span>
                        <span className="font-semibold text-[#D97757]">#{selectedAdr.merged_pr}</span>
                      </div>
                    )}
                    {selectedAdr.superseded_by_adr && (
                      <div>
                        <span className="text-[#8c8c8a] block text-[10px] uppercase font-bold">Superseded By</span>
                        <span className="font-semibold text-amber-700">{selectedAdr.superseded_by_adr}</span>
                      </div>
                    )}
                  </div>

                  {selectedAdr.invariants && selectedAdr.invariants.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-600" />
                        Invariants (MUST / MUST NEVER Rules)
                      </h4>
                      <ul className="space-y-1.5">
                        {selectedAdr.invariants.map((inv, idx) => (
                          <li key={idx} className="text-xs bg-emerald-50 text-emerald-950 p-2.5 rounded-lg border border-emerald-200">
                            {inv}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-[#8c8c8a]">Rationale & Technical Reasoning</h4>
                    <p className="text-xs text-[#5c5c5a] leading-relaxed bg-[#f5f4ef] p-3 rounded-lg border border-[#e5e4df]">
                      {selectedAdr.reasoning || 'No rationale recorded.'}
                    </p>
                  </div>

                  {selectedAdr.alternatives && selectedAdr.alternatives.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-[#8c8c8a]">Alternatives Rejected</h4>
                      <ul className="list-disc ml-4 text-xs text-[#5c5c5a] space-y-1">
                        {selectedAdr.alternatives.map((alt, idx) => (
                          <li key={idx}>{alt}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
