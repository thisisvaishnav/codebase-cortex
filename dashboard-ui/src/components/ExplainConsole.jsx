import React, { useState } from 'react';
import { Search, Sparkles, ArrowRight, User, Calendar, GitCommit, ShieldAlert, CheckCircle2, RefreshCw } from 'lucide-react';
import { explainQuery } from '../services/api';

const SAMPLE_QUESTIONS = [
  "Why did we choose Redis over Postgres for session persistence?",
  "What is our policy on distributed session caching?",
  "Show active vs superseded ADR lineage for session management",
  "What event-driven message queue architecture do we use?",
];

export default function ExplainConsole() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  async function handleSearch(queryToRun) {
    const q = (queryToRun || question).trim();
    if (!q) return;
    setLoading(true);
    setResult(null);

    const data = await explainQuery(q);
    setResult(data);
    setLoading(false);
  }

  function handleSampleClick(q) {
    setQuestion(q);
    handleSearch(q);
  }

  return (
    <div className="max-w-4xl mx-auto w-full space-y-6">
      <div className="text-center space-y-2 py-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#D97757]/10 text-[#D97757] text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          cortex-explain Institutional Query Engine
        </div>
        <h2 className="text-2xl font-bold text-[#141413] tracking-tight">
          Ask Architectural Decision History
        </h2>
        <p className="text-sm text-[#5c5c5a] max-w-xl mx-auto">
          Semantic retrieval and multi-hop reasoning over ADR lineage. Attributes active and superseded decisions to authors, dates, and trade-offs.
        </p>
      </div>

      <div className="bg-white border-2 border-[#D97757] rounded-xl p-2 shadow-sm flex items-center gap-2">
        <Search className="w-5 h-5 text-[#8c8c8a] ml-2" />
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Ask a question (e.g. 'Why did we choose Redis over Postgres?')"
          className="flex-1 bg-transparent border-none outline-none text-sm text-[#141413] placeholder-[#8c8c8a] py-2"
        />
        <button
          onClick={() => handleSearch()}
          disabled={loading}
          className="bg-[#D97757] hover:bg-[#c4684a] text-white text-xs font-semibold px-5 py-2.5 rounded-lg transition-colors flex items-center gap-2"
        >
          {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Ask Cortex'}
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="font-semibold text-[#8c8c8a] uppercase tracking-wider text-[10px]">Sample Prompts:</span>
        {SAMPLE_QUESTIONS.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSampleClick(q)}
            className="bg-[#f5f4ef] hover:bg-[#e5e4df] text-[#5c5c5a] hover:text-[#141413] border border-[#e5e4df] px-3 py-1 rounded-full transition-all"
          >
            {q.length > 40 ? q.slice(0, 38) + '...' : q}
          </button>
        ))}
      </div>

      {loading && (
        <div className="bg-white border border-[#e5e4df] rounded-xl p-8 text-center space-y-3">
          <RefreshCw className="w-6 h-6 animate-spin text-[#D97757] mx-auto" />
          <p className="text-sm font-medium text-[#141413]">Querying vector memory & walking multi-hop lineage chains...</p>
          <p className="text-xs text-[#8c8c8a]">Scanning ACTIVE and SUPERSEDED records across docs/adr/</p>
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {result.lineage && result.lineage.length > 0 && (
            <div className="bg-white border border-[#e5e4df] rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#8c8c8a]">
                  ADR Lineage Chain (Oldest → Newest)
                </h3>
                <span className="text-xs text-[#5c5c5a] font-mono">
                  {result.lineage.length} hop(s) traced
                </span>
              </div>

              <div className="flex items-center gap-3 overflow-x-auto pb-2">
                {result.lineage.map((adr, idx) => (
                  <React.Fragment key={adr.id}>
                    <div className="bg-[#f5f4ef] border border-[#e5e4df] rounded-lg p-4 min-w-[240px] max-w-[280px] space-y-2 flex-shrink-0">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-xs text-[#D97757]">{adr.id}</span>
                        <span
                          className={`text-[10px] font-bold px-2 py-0.5 rounded text-white ${
                            adr.status === 'ACTIVE' ? 'bg-emerald-600' : 'bg-amber-600'
                          }`}
                        >
                          {adr.status}
                        </span>
                      </div>
                      <h4 className="text-xs font-semibold text-[#141413] line-clamp-2 leading-snug">
                        {adr.title}
                      </h4>
                      <div className="text-[11px] text-[#5c5c5a] flex items-center gap-2">
                        <User className="w-3 h-3" /> @{adr.author}
                        <Calendar className="w-3 h-3 ml-1" /> {adr.date}
                      </div>
                      {adr.merged_pr && (
                        <div className="text-[11px] text-[#8c8c8a] flex items-center gap-1 font-mono">
                          <GitCommit className="w-3 h-3 text-[#D97757]" /> PR #{adr.merged_pr}
                        </div>
                      )}
                    </div>
                    {idx < result.lineage.length - 1 && (
                      <ArrowRight className="w-5 h-5 text-[#8c8c8a] flex-shrink-0" />
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          <div className="bg-white border border-[#e5e4df] rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#8c8c8a] flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Contextual Answer & Decision Attribution
            </h3>
            <div
              className="prose prose-sm max-w-none text-[#5c5c5a] leading-relaxed space-y-3"
              dangerouslySetInnerHTML={{
                __html: (result.answer || '')
                  .replace(/^### (.*$)/gim, '<h3 class="text-base font-bold text-[#141413] mt-4 mb-2">$1</h3>')
                  .replace(/^## (.*$)/gim, '<h2 class="text-lg font-bold text-[#141413] mt-4 mb-2">$1</h2>')
                  .replace(/\*\*(.*?)\*\*/g, '<strong class="text-[#141413]">$1</strong>')
                  .replace(/`(.*?)`/g, '<code class="bg-[#f5f4ef] text-[#141413] px-1.5 py-0.5 rounded text-xs font-mono">$1</code>')
                  .replace(/^- (.*$)/gim, '<li class="ml-4 list-disc">$1</li>')
                  .replace(/\n\n/g, '<br/><br/>'),
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
