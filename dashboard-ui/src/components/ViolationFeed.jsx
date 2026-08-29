import React, { useState } from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, User, GitPullRequest, Code, RefreshCw, XCircle, ArrowUpRight } from 'lucide-react';

const MOCK_VIOLATIONS = [
  {
    id: 'viol-142',
    pr: 142,
    title: 'Refactor session store to use local map for speed',
    author: 'junior-dev',
    stage1_matches: ['ADR-002: Redis for Distributed Session Persistence'],
    stage2_confidence: 95.0,
    severity: 'HARD_VIOLATION',
    adr_id: 'ADR-002',
    adr_author: 'senior-dev',
    invariant: 'Session state MUST never be stored in process memory. They MUST be stored in the shared Redis cache layer.',
    status: 'ESCALATED',
    codeowners: ['@senior-dev', '@lead-maintainer'],
    qodo_resolution: 'declined-architectural',
    timestamp: '10 mins ago',
  },
  {
    id: 'viol-138',
    pr: 138,
    title: 'Add billing webhook retry listener',
    author: 'backend-dev',
    stage1_matches: ['ADR-003: Event-Driven Architecture with NATS JetStream'],
    stage2_confidence: 65.0,
    severity: 'ADVISORY',
    adr_id: 'ADR-003',
    adr_author: 'lead-arch',
    invariant: 'Outbound event handlers MUST use idempotent message ids.',
    status: 'ADVISORY_POSTED',
    codeowners: ['@lead-arch'],
    qodo_resolution: 'fixed',
    timestamp: '2 hours ago',
  },
];

export default function ViolationFeed() {
  const [violations, setViolations] = useState(MOCK_VIOLATIONS);

  return (
    <div className="max-w-5xl mx-auto w-full space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-[#141413] tracking-tight">
            Real-Time Maintainer Violation & Drift Feed
          </h2>
          <p className="text-xs text-[#5c5c5a]">
            Monitors two-stage contradiction audit results (cortex-detect), CODEOWNERS maintainer escalations, and Qodo self-healing resolution statuses.
          </p>
        </div>

        <button
          onClick={() => setViolations([...MOCK_VIOLATIONS])}
          className="text-xs bg-white border border-[#e5e4df] text-[#5c5c5a] hover:text-[#141413] px-3 py-1.5 rounded-lg flex items-center gap-1.5 font-medium shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5 text-[#D97757]" />
          Refresh Feed
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white border border-[#e5e4df] p-4 rounded-xl shadow-sm space-y-1">
          <div className="text-2xl font-bold text-rose-600">1</div>
          <div className="text-xs font-semibold text-[#141413]">Hard Violations (≥80%)</div>
          <div className="text-[11px] text-[#8c8c8a]">Requires maintainer sign-off</div>
        </div>

        <div className="bg-white border border-[#e5e4df] p-4 rounded-xl shadow-sm space-y-1">
          <div className="text-2xl font-bold text-amber-600">1</div>
          <div className="text-xs font-semibold text-[#141413]">Advisories (60-79%)</div>
          <div className="text-[11px] text-[#8c8c8a]">Guidance posted on PR thread</div>
        </div>

        <div className="bg-white border border-[#e5e4df] p-4 rounded-xl shadow-sm space-y-1">
          <div className="text-2xl font-bold text-emerald-600">100%</div>
          <div className="text-xs font-semibold text-[#141413]">Qodo Resolution Rate</div>
          <div className="text-[11px] text-[#8c8c8a]">Architectural invariants protected</div>
        </div>
      </div>

      <div className="space-y-4">
        {violations.map((item) => {
          const isHard = item.severity === 'HARD_VIOLATION';
          return (
            <div
              key={item.id}
              className={`bg-white border rounded-xl p-5 shadow-sm space-y-4 ${
                isHard ? 'border-rose-200' : 'border-amber-200'
              }`}
            >
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-[#e5e4df] pb-3">
                <div className="flex items-center gap-2">
                  {isHard ? (
                    <XCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0" />
                  )}
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-[#141413]">PR #{item.pr}: {item.title}</span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded text-white ${
                          isHard ? 'bg-rose-600' : 'bg-amber-600'
                        }`}
                      >
                        {isHard ? 'HARD VIOLATION (≥80%)' : 'ADVISORY (60-79%)'}
                      </span>
                    </div>
                    <div className="text-xs text-[#8c8c8a]">
                      Authored by @{item.author} · {item.timestamp}
                    </div>
                  </div>
                </div>

                <div className="text-right text-xs font-mono">
                  <span className="text-[#8c8c8a]">Stage 2 Score: </span>
                  <span className={`font-bold ${isHard ? 'text-rose-600' : 'text-amber-600'}`}>
                    {item.stage2_confidence}%
                  </span>
                </div>
              </div>

              <div className="bg-[#f5f4ef] p-3 rounded-lg border border-[#e5e4df] text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#D97757]">Conflicting Decision: {item.adr_id}</span>
                  <span className="text-[#8c8c8a]">Decided by @{item.adr_author}</span>
                </div>
                <div className="text-rose-950 font-medium bg-rose-50 border border-rose-200 p-2.5 rounded">
                  <strong>Invariant:</strong> "{item.invariant}"
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between text-xs gap-3 pt-1">
                <div className="flex items-center gap-2">
                  <span className="text-[#8c8c8a] font-semibold">Escalated CODEOWNERS:</span>
                  {item.codeowners.map((co, idx) => (
                    <span key={idx} className="bg-[#f5f4ef] text-[#141413] px-2 py-0.5 rounded border border-[#e5e4df] font-mono">
                      {co}
                    </span>
                  ))}
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[#8c8c8a] font-semibold">Qodo Resolver:</span>
                  <span
                    className={`px-2 py-0.5 rounded text-white text-[11px] font-bold ${
                      item.qodo_resolution === 'declined-architectural'
                        ? 'bg-rose-700'
                        : 'bg-emerald-700'
                    }`}
                  >
                    {item.qodo_resolution === 'declined-architectural'
                      ? '🛑 Fix Declined (Protects Invariant)'
                      : '✅ Fix Applied'}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
