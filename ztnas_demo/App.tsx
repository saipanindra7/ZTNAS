import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import type { View } from './types';
import { initialView } from './constants';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>(initialView);

  return (
    <div className="flex h-screen bg-slate-900 font-sans">
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} />
      <main className="flex-1 overflow-y-auto">
        <Dashboard currentView={currentView} setCurrentView={setCurrentView} />
      </main>
    </div>
  );
};

export default App;
