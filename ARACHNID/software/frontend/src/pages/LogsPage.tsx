import React, { useState } from 'react';
import { useRover } from '../hooks/useRover';

export const LogsPage: React.FC = () => {
  const { logs, explorationData } = useRover();
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const exploredPct = Math.round(explorationData?.explored_percent ?? 68);
  const frontierCount = explorationData?.frontier_count ?? 12;
  const currentTarget = explorationData?.current_goal
    ? `X: ${explorationData.current_goal.x.toFixed(2)}, Y: ${explorationData.current_goal.y.toFixed(2)}`
    : 'FRONTIER 08';

  const filteredLogs = logs.filter((log) => {
    if (filterSeverity !== 'ALL' && log.level.toUpperCase() !== filterSeverity) {
      return false;
    }
    if (searchQuery.trim()) {
      return log.message.toLowerCase().includes(searchQuery.toLowerCase());
    }
    return true;
  });

  const getSeverityDot = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
      case 'CRITICAL':
        return 'bg-[#ba1a1a] shadow-[0_0_4px_rgba(186,26,26,0.8)] animate-pulse';
      case 'WARNING':
      case 'WARN':
        return 'bg-[#d97706] shadow-[0_0_4px_rgba(217,119,6,0.8)]';
      case 'INFO':
        return 'bg-[#89a8ff] shadow-[0_0_4px_rgba(137,168,255,0.8)]';
      default:
        return 'bg-[#000928]';
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-3">
        {/* Coverage */}
        <div className="flex flex-col bg-[#ededf5] p-3.5 rounded-lg shadow-sm relative overflow-hidden border border-[#e2e2e9]">
          <div className="flex items-center justify-between mb-1">
            <span className="font-label-caps text-xs text-[#45464f]">COVERAGE</span>
            <span className="material-symbols-outlined text-[#000928] text-[18px]">radar</span>
          </div>
          <div className="font-headline-md text-2xl text-[#1a1b21] font-bold">{exploredPct}%</div>
          {/* Progress Bar */}
          <div className="w-full bg-[#e2e2e9] h-1.5 mt-2 rounded-full overflow-hidden">
            <div className="bg-[#000928] h-full" style={{ width: `${exploredPct}%` }} />
          </div>
        </div>

        {/* Frontiers */}
        <div className="flex flex-col bg-[#ededf5] p-3.5 rounded-lg shadow-sm relative overflow-hidden border border-[#e2e2e9]">
          <div className="flex items-center justify-between mb-1">
            <span className="font-label-caps text-xs text-[#45464f]">FRONTIERS</span>
            <span className="material-symbols-outlined text-[#000928] text-[18px]">explore</span>
          </div>
          <div className="font-headline-md text-2xl text-[#1a1b21] font-bold">{frontierCount}</div>
          {/* Mini Chart Bars */}
          <div className="w-full h-1.5 mt-2 flex gap-1">
            <div className="flex-1 bg-[#000928]/20 h-full rounded" />
            <div className="flex-1 bg-[#000928]/40 h-full rounded" />
            <div className="flex-1 bg-[#000928]/60 h-full rounded" />
            <div className="flex-1 bg-[#000928] h-full rounded" />
          </div>
        </div>

        {/* Target */}
        <div className="col-span-2 flex flex-col bg-[#0b1f4d] p-3.5 rounded-lg shadow-sm text-[#7788bc] border border-[#000928]">
          <div className="flex items-center justify-between mb-1">
            <span className="font-label-caps text-xs text-white/80">CURRENT TARGET</span>
            <span className="material-symbols-outlined text-white text-[18px]">my_location</span>
          </div>
          <div className="font-data-mono-lg text-lg text-white font-bold tracking-tight">
            {currentTarget}
          </div>
        </div>
      </div>

      {/* Technical Log Feed */}
      <div className="flex flex-col bg-[#ffffff] rounded-lg shadow-sm border border-[#e2e2e9] overflow-hidden">
        {/* Header with Search & Filter */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 bg-[#e8e7ef] border-b border-[#e2e2e9] gap-2">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#45464f] text-[18px]">list_alt</span>
            <span className="font-label-caps text-xs text-[#45464f]">SYSTEM LOGS</span>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="px-2.5 py-1 text-xs border border-[#c5c6d0] rounded bg-[#ffffff] text-[#1a1b21] focus:outline-none focus:border-[#000928] font-mono"
            />
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="px-2 py-1 text-xs border border-[#c5c6d0] rounded bg-[#ffffff] text-[#1a1b21] font-mono"
            >
              <option value="ALL">ALL</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </div>
        </div>

        {/* Log Entries Container */}
        <div className="flex flex-col p-3 gap-1.5 bg-[#f9f9ff] min-h-[360px] max-h-[500px] overflow-y-auto">
          {filteredLogs.length === 0 ? (
            <div className="text-center text-xs text-[#757680] py-12 font-mono">
              NO LOG ENTRIES RECORDED
            </div>
          ) : (
            filteredLogs.map((log, idx) => {
              const timeStr = new Date(log.timestamp_ms).toLocaleTimeString();
              return (
                <div
                  key={idx}
                  className="flex items-start gap-2.5 p-1.5 rounded hover:bg-[#f3f3fa] transition-colors"
                >
                  <span className="font-data-mono-sm text-xs text-[#757680] shrink-0">{timeStr}</span>
                  <div
                    className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${getSeverityDot(log.level)}`}
                  />
                  <span className="font-data-mono-sm text-xs text-[#1a1b21] break-all">
                    {log.message}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
