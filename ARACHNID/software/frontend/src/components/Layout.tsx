import React from 'react';
import { Header } from './Header';
import { GlobalEStop } from './GlobalEStop';

export type TabType = 'mission' | 'map' | 'diagnostics' | 'controls' | 'logs';

interface LayoutProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  children: React.ReactNode;
}

const TAB_CONFIG: { id: TabType; label: string; icon: string; title: string }[] = [
  { id: 'mission', label: 'MISSION', icon: 'rocket_launch', title: 'Mission Control' },
  { id: 'map', label: 'MAP', icon: 'map', title: 'Occupancy Grid' },
  { id: 'diagnostics', label: 'DIAGNOSTICS', icon: 'precision_manufacturing', title: 'Spatial Array Diagnostics' },
  { id: 'controls', label: 'CONTROLS', icon: 'tune', title: 'Teleoperation Console' },
  { id: 'logs', label: 'LOGS', icon: 'terminal', title: 'System Logs' },
];

export const Layout: React.FC<LayoutProps> = ({ activeTab, onTabChange, children }) => {
  const currentConfig = TAB_CONFIG.find((t) => t.id === activeTab) || TAB_CONFIG[0];

  return (
    <div className="min-h-screen flex flex-col bg-[#f9f9ff] text-[#1a1b21]">
      <GlobalEStop />
      <Header activeTabTitle={currentConfig.title} />

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-[1440px] mx-auto pt-24 pb-24 px-4 md:px-6">
        {children}
      </main>

      {/* Persistent Stitch Bottom Navigation Bar */}
      <nav className="fixed bottom-0 left-0 w-full z-40 bg-[#ffffff]/90 backdrop-blur-xl border-t border-[#e2e2e9] shadow-[0_-1px_8px_rgba(0,0,0,0.03)]">
        <div className="max-w-[1440px] mx-auto flex items-center justify-around h-16 px-2">
          {TAB_CONFIG.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                  isActive
                    ? 'text-[#0b1f4d] font-bold'
                    : 'text-[#45464f] hover:text-[#000928]'
                }`}
              >
                <span className="material-symbols-outlined text-[20px] mb-0.5">{tab.icon}</span>
                <span className="font-label-caps text-[10px] tracking-wider">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
};
