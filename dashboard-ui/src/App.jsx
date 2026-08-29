import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ExplainConsole from './components/ExplainConsole';
import LineageGraph from './components/LineageGraph';
import ViolationFeed from './components/ViolationFeed';
import SseDebugger from './components/SseDebugger';
import { checkTrueForgeHealth, checkVectorHealth } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('explain'); // explain | lineage | violations | debugger
  const [tfHealth, setTfHealth] = useState({ ok: false });
  const [vecHealth, setVecHealth] = useState({ ok: false });

  useEffect(() => {
    pollHealth();
    const interval = setInterval(pollHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  async function pollHealth() {
    const tf = await checkTrueForgeHealth();
    const vec = await checkVectorHealth();
    setTfHealth(tf);
    setVecHealth(vec);
  }

  return (
    <div className="min-h-screen bg-[#faf9f5] text-[#141413] flex flex-col font-sans">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        tfHealth={tfHealth}
        vecHealth={vecHealth}
      />

      <main className="flex-1 p-6 overflow-y-auto">
        {activeTab === 'explain' && <ExplainConsole />}
        {activeTab === 'lineage' && <LineageGraph />}
        {activeTab === 'violations' && <ViolationFeed />}
        {activeTab === 'debugger' && <SseDebugger />}
      </main>
    </div>
  );
}
