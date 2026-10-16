import React, { useState, useEffect, useRef } from 'react';
import {
  Activity,
  Play,
  Pause,
  RefreshCw,
  Eye,
  X,
  Filter,
  Search,
  Shield,
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  FileText,
  Cpu,
  Sliders,
  Radio,
  Server,
  Clock,
  Layers,
  ChevronDown,
  Info,
  Terminal,
  Lock,
  Unlock
} from 'lucide-react';
import { api } from '../services/api';
import { CollectorStatus, CollectorEventRecord } from '../types';
import { CyberCard } from '../components/common/CyberCard';
import { PageHeader } from '../components/common/PageHeader';
import { StatusBadge } from '../components/common/StatusBadge';
import { EmptyState } from '../components/common/EmptyState';

export const AnalysisPage: React.FC<{ onNavigate: (tab: string) => void }> = ({ onNavigate }) => {
  // State
  const [collectorStatus, setCollectorStatus] = useState<CollectorStatus | null>(null);
  const [events, setEvents] = useState<CollectorEventRecord[]>([]);
  const [totalEvents, setTotalEvents] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [channelFilter, setChannelFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [pageOffset, setPageOffset] = useState<number>(0);
  const PAGE_LIMIT = 50;

  // Selected event modal
  const [selectedRecord, setSelectedRecord] = useState<CollectorEventRecord | null>(null);
  const [activeModalTab, setActiveModalTab] = useState<'facts' | 'model' | 'security'>('facts');

  // Relative time tracker
  const [nowTick, setNowTick] = useState<number>(Date.now());

  useEffect(() => {
    const timer = setInterval(() => setNowTick(Date.now()), 2000);
    return () => clearInterval(timer);
  }, []);

  // Fetch collector status
  const fetchStatus = async () => {
    try {
      const stat = await api.getCollectorStatus();
      setCollectorStatus(stat);
    } catch (e: any) {
      console.error('Failed to fetch collector status:', e);
    }
  };

  // Fetch events matching current filters
  const fetchEvents = async (silent: boolean = false) => {
    if (!silent) setRefreshing(true);
    try {
      const res = await api.getCollectorEvents({
        time_range: timeRange,
        category: categoryFilter !== 'all' ? categoryFilter : undefined,
        channel: channelFilter !== 'all' ? channelFilter : undefined,
        search: searchQuery.trim() || undefined,
        limit: PAGE_LIMIT,
        offset: pageOffset
      });
      setEvents(res.events || []);
      setTotalEvents(res.total || 0);
      setErrorMsg(null);
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to load live events');
    } finally {
      if (!silent) setRefreshing(false);
      setLoading(false);
    }
  };

  // Initial load and filter change
  useEffect(() => {
    fetchStatus();
    fetchEvents(false);
  }, [timeRange, categoryFilter, channelFilter, pageOffset]);

  // Handle search with debounce
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchEvents(false);
    }, 400);
    return () => clearTimeout(delayDebounce);
  }, [searchQuery]);

  // Continuous auto-refresh polling (every 5 seconds)
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchStatus();
      fetchEvents(true);
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, timeRange, categoryFilter, channelFilter, searchQuery, pageOffset]);

  // Pause / Resume handler
  const handleTogglePause = async () => {
    try {
      if (collectorStatus?.is_paused) {
        const updated = await api.resumeCollector();
        setCollectorStatus(updated);
      } else {
        const updated = await api.pauseCollector();
        setCollectorStatus(updated);
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to update collector state');
    }
  };

  // Poll now handler
  const handlePollNow = async () => {
    try {
      setRefreshing(true);
      await api.pollCollectorNow();
      await fetchStatus();
      await fetchEvents(false);
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to trigger collection pass');
    } finally {
      setRefreshing(false);
    }
  };

  // Compute relative time string from ISO timestamp
  const getRelativeTime = (isoString?: string | null) => {
    if (!isoString) return 'Never';
    const diffMs = nowTick - new Date(isoString).getTime();
    if (diffMs < 0 || diffMs < 3000) return 'Just now';
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return `${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    return `${diffHr}h ago`;
  };

  const counts24h = collectorStatus?.counts_24h || {
    total: 0,
    normal: 0,
    medium: 0,
    anomalous: 0,
    unclassified: 0
  };

  return (
    <div className="space-y-6">
      {/* Page Title & Breadcrumb Header */}
      <PageHeader
        title="Live System Log Telemetry & Anomaly Analysis"
        subtitle="Automatic real-time Windows Event Log collection from host system with three-level ML classification and SHAP explainability"
        badge="Real-Time Host Ingestion"
      />

      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-300 text-xs font-mono flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="text-rose-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 1. Collector Telemetry Status Banner */}
      <CyberCard className="p-5 overflow-hidden" glow="cyan" hoverEffect={false}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Left: Host & Connection Status */}
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              {/* Overall Status Badge */}
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-[#070D1A] border border-cyan-500/40">
                <span
                  className={`w-2 h-2 rounded-full ${
                    collectorStatus?.status === 'Connected'
                      ? 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse'
                      : collectorStatus?.status === 'Paused'
                      ? 'bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.8)]'
                      : 'bg-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.8)]'
                  }`}
                />
                <span className="text-white uppercase tracking-wider">
                  COLLECTOR: {collectorStatus?.status || 'INITIALIZING'}
                </span>
              </div>

              {/* Hostname Pill */}
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono bg-[#070D1A] border border-[#1E3050] text-slate-300">
                <Server className="w-3.5 h-3.5 text-cyan-400" />
                <span>HOST: <b className="text-white">{collectorStatus?.hostname || 'WINDOWS-HOST'}</b></span>
              </div>

              {/* Last Collection Timestamp */}
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono bg-[#070D1A] border border-[#1E3050] text-slate-400">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>LAST POLL: <b className="text-cyan-300">{getRelativeTime(collectorStatus?.last_collection_time)}</b></span>
              </div>
            </div>

            {/* Channels Accessibility Indicator */}
            <div className="flex flex-wrap items-center gap-2 text-xs font-mono pt-1">
              <span className="text-slate-400 text-[11px] uppercase tracking-wider">Monitored Channels:</span>

              {/* System Channel */}
              <span
                className={`px-2 py-0.5 rounded text-[11px] border flex items-center gap-1 ${
                  collectorStatus?.channels?.System?.status === 'Connected'
                    ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300'
                    : 'bg-slate-900 border-slate-700 text-slate-400'
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                System
              </span>

              {/* Application Channel */}
              <span
                className={`px-2 py-0.5 rounded text-[11px] border flex items-center gap-1 ${
                  collectorStatus?.channels?.Application?.status === 'Connected'
                    ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300'
                    : 'bg-slate-900 border-slate-700 text-slate-400'
                }`}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Application
              </span>

              {/* Security Channel */}
              <span
                className={`px-2 py-0.5 rounded text-[11px] border flex items-center gap-1 ${
                  collectorStatus?.channels?.Security?.status === 'Connected'
                    ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-300'
                    : collectorStatus?.channels?.Security?.status === 'Permission Denied'
                    ? 'bg-amber-950/60 border-amber-500/40 text-amber-300'
                    : 'bg-slate-900 border-slate-700 text-slate-400'
                }`}
                title={collectorStatus?.channels?.Security?.error || undefined}
              >
                {collectorStatus?.channels?.Security?.status === 'Connected' ? (
                  <Unlock className="w-3 h-3 text-emerald-400" />
                ) : (
                  <Lock className="w-3 h-3 text-amber-400" />
                )}
                Security
                {collectorStatus?.channels?.Security?.status === 'Permission Denied' && (
                  <span className="text-[9px] text-amber-400 ml-0.5">(Admin Req)</span>
                )}
              </span>
            </div>
          </div>

          {/* Right: Operational Controls */}
          <div className="flex flex-wrap items-center gap-2.5 font-mono text-xs">
            {/* Auto-Refresh Toggle */}
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1.5 rounded-lg border flex items-center gap-1.5 transition-all cursor-pointer ${
                autoRefresh
                  ? 'bg-cyan-950/80 border-cyan-500/50 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.2)]'
                  : 'bg-[#070D1A] border-[#1E3050] text-slate-400 hover:text-white'
              }`}
            >
              <Radio className={`w-3.5 h-3.5 ${autoRefresh ? 'text-cyan-400 animate-pulse' : 'text-slate-500'}`} />
              <span>Auto-Poll (5s)</span>
            </button>

            {/* Pause / Resume */}
            <button
              onClick={handleTogglePause}
              className="px-3 py-1.5 rounded-lg bg-[#070D1A] border border-[#1E3050] hover:border-cyan-500/50 text-slate-300 hover:text-white flex items-center gap-1.5 transition-all cursor-pointer shadow-sm"
            >
              {collectorStatus?.is_paused ? (
                <>
                  <Play className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Resume Collection</span>
                </>
              ) : (
                <>
                  <Pause className="w-3.5 h-3.5 text-amber-400" />
                  <span>Pause Collection</span>
                </>
              )}
            </button>

            {/* Poll Now Button */}
            <button
              onClick={handlePollNow}
              disabled={refreshing}
              className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold flex items-center gap-1.5 transition-all shadow-[0_0_12px_rgba(6,182,212,0.3)] cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              <span>Poll Now</span>
            </button>
          </div>
        </div>
      </CyberCard>

      {/* 2. 24-Hour Telemetry KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* Total Events in 24h */}
        <CyberCard className="p-4 space-y-1" glow="cyan">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono uppercase tracking-wider">
            <span>24h Ingested</span>
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">{counts24h.total}</div>
          <div className="text-[10px] text-cyan-400 font-mono">Real Windows logs</div>
        </CyberCard>

        {/* Normal Count */}
        <CyberCard className="p-4 space-y-1" glow="emerald">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono uppercase tracking-wider">
            <span>Normal Events</span>
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 font-mono">{counts24h.normal}</div>
          <div className="text-[10px] text-slate-400 font-mono">Prob &lt; 0.30</div>
        </CyberCard>

        {/* Medium Count */}
        <CyberCard className="p-4 space-y-1" glow="amber">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono uppercase tracking-wider">
            <span>Medium Risk</span>
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-400 font-mono">{counts24h.medium}</div>
          <div className="text-[10px] text-slate-400 font-mono">Prob 0.30–0.70</div>
        </CyberCard>

        {/* Anomalous Count */}
        <CyberCard className="p-4 space-y-1" glow="rose">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono uppercase tracking-wider">
            <span>Anomalies</span>
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-2xl font-black text-rose-400 font-mono">{counts24h.anomalous}</div>
          <div className="text-[10px] text-slate-400 font-mono">Prob &ge; 0.70</div>
        </CyberCard>

        {/* Unclassified Count */}
        <CyberCard className="p-4 space-y-1 col-span-2 sm:col-span-1" glow="none">
          <div className="flex items-center justify-between text-slate-400 text-[10px] font-mono uppercase tracking-wider">
            <span>Unclassified</span>
            <Info className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <div className="text-2xl font-black text-slate-300 font-mono">{counts24h.unclassified}</div>
          <div className="text-[10px] text-slate-500 font-mono">Awaiting Model Schema</div>
        </CyberCard>
      </div>

      {/* 3. Filter Bar */}
      <CyberCard className="p-4 space-y-3" glow="none" hoverEffect={false}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono">
          {/* Time Range Selector */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-slate-400 text-[11px] uppercase mr-1">Time:</span>
            {[
              { id: '1h', label: '1 Hour' },
              { id: '6h', label: '6 Hours' },
              { id: '12h', label: '12 Hours' },
              { id: '24h', label: '24 Hours' },
              { id: '7d', label: '7 Days' },
              { id: 'all', label: 'All History' }
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => {
                  setTimeRange(t.id);
                  setPageOffset(0);
                }}
                className={`px-2.5 py-1 rounded-lg text-xs transition-all cursor-pointer ${
                  timeRange === t.id
                    ? 'bg-cyan-600 text-white font-bold shadow-[0_0_8px_rgba(6,182,212,0.4)]'
                    : 'bg-[#070D1A] text-slate-400 hover:text-white border border-[#1E3050]'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Category & Channel Dropdowns */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Category Dropdown */}
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400 text-[11px] uppercase">Risk:</span>
              <select
                value={categoryFilter}
                onChange={(e) => {
                  setCategoryFilter(e.target.value);
                  setPageOffset(0);
                }}
                className="px-2.5 py-1 rounded-lg bg-[#070D1A] border border-[#1E3050] text-slate-200 focus:border-cyan-400 outline-none cursor-pointer"
              >
                <option value="all">All Categories</option>
                <option value="Normal">Normal</option>
                <option value="Medium">Medium Risk</option>
                <option value="Anomalous">Anomalous</option>
                <option value="Unclassified">Unclassified</option>
              </select>
            </div>

            {/* Channel Dropdown */}
            <div className="flex items-center gap-1.5">
              <span className="text-slate-400 text-[11px] uppercase">Channel:</span>
              <select
                value={channelFilter}
                onChange={(e) => {
                  setChannelFilter(e.target.value);
                  setPageOffset(0);
                }}
                className="px-2.5 py-1 rounded-lg bg-[#070D1A] border border-[#1E3050] text-slate-200 focus:border-cyan-400 outline-none cursor-pointer"
              >
                <option value="all">All Channels</option>
                <option value="System">System</option>
                <option value="Application">Application</option>
                <option value="Security">Security</option>
              </select>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search events by provider name, event ID, or message text..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPageOffset(0);
            }}
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-[#070D1A] border border-[#1E3050] text-xs font-mono text-white placeholder-slate-500 focus:border-cyan-400 outline-none transition-colors"
          />
        </div>
      </CyberCard>

      {/* 4. Continuously Updating Live Event Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400">
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span>Showing {events.length} of {totalEvents} matching events</span>
          </span>
          {refreshing && <span className="text-cyan-400 animate-pulse">Syncing events...</span>}
        </div>

        {loading && events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-3">
            <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
            <span className="font-mono text-xs tracking-wider uppercase text-cyan-300">
              Reading Windows System Telemetry...
            </span>
          </div>
        ) : events.length === 0 ? (
          <CyberCard className="p-8 text-center" glow="none">
            <EmptyState
              title="No Windows Events In Range"
              description="No events match the selected time range and filters. Try adjusting the time window or clearing search terms."
              icon={Activity}
            />
          </CyberCard>
        ) : (
          <CyberCard className="overflow-hidden p-0" glow="cyan" hoverEffect={false}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#070D1A] text-slate-400 uppercase text-[10px] border-b border-[#1E3050]">
                  <tr>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Provider / Application</th>
                    <th className="p-3">Channel</th>
                    <th className="p-3">Event ID</th>
                    <th className="p-3">Severity</th>
                    <th className="p-3">Event Message</th>
                    <th className="p-3">Classification</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1E3050]/60 text-slate-300">
                  {events.map((r) => {
                    const cat = r.category || 'Unclassified';

                    return (
                      <tr key={r.id} className="hover:bg-[#121E36]/40 transition-colors">
                        {/* Timestamp */}
                        <td className="p-3 text-slate-400 whitespace-nowrap text-[11px]">
                          {r.timestamp ? r.timestamp.substring(0, 19).replace('T', ' ') : 'N/A'}
                        </td>

                        {/* Provider */}
                        <td className="p-3 font-semibold text-cyan-300 whitespace-nowrap max-w-[180px] truncate" title={r.provider || r.app_name}>
                          {r.provider || r.app_name || 'System'}
                        </td>

                        {/* Channel */}
                        <td className="p-3 text-slate-300 whitespace-nowrap">
                          <span className="px-1.5 py-0.5 rounded bg-[#070D1A] border border-[#1E3050] text-[10px] text-cyan-400">
                            {r.channel || 'System'}
                          </span>
                        </td>

                        {/* Event ID */}
                        <td className="p-3 text-slate-300 whitespace-nowrap">
                          <span className="text-white font-bold">{r.event_id || '-'}</span>
                        </td>

                        {/* Severity */}
                        <td className="p-3 whitespace-nowrap">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] border ${
                              r.severity_label === 'Error' || r.severity_label === 'Critical'
                                ? 'bg-rose-950/60 border-rose-500/40 text-rose-300'
                                : r.severity_label === 'Warning'
                                ? 'bg-amber-950/60 border-amber-500/40 text-amber-300'
                                : 'bg-[#070D1A] border-[#1E3050] text-slate-300'
                            }`}
                          >
                            {r.severity_label || 'Information'}
                          </span>
                        </td>

                        {/* Message preview */}
                        <td className="p-3 text-slate-300 max-w-sm truncate" title={r.message || r.raw_log}>
                          {r.message || r.raw_log}
                        </td>

                        {/* Classification */}
                        <td className="p-3 whitespace-nowrap">
                          <StatusBadge status={cat.toLowerCase()} size="sm" />
                        </td>

                        {/* Actions */}
                        <td className="p-3 text-right whitespace-nowrap">
                          <button
                            onClick={() => {
                              setSelectedRecord(r);
                              setActiveModalTab('facts');
                            }}
                            className="px-2.5 py-1 rounded-lg bg-[#070D1A] border border-cyan-500/30 hover:border-cyan-400 text-cyan-300 text-[11px] inline-flex items-center gap-1 transition-all cursor-pointer shadow-sm"
                          >
                            <Eye className="w-3 h-3" />
                            <span>Details</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {totalEvents > PAGE_LIMIT && (
              <div className="p-3 border-t border-[#1E3050]/80 bg-[#070D1A] flex items-center justify-between text-xs font-mono text-slate-400">
                <span>
                  Showing {pageOffset + 1}–{Math.min(pageOffset + PAGE_LIMIT, totalEvents)} of {totalEvents}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    disabled={pageOffset === 0}
                    onClick={() => setPageOffset(Math.max(0, pageOffset - PAGE_LIMIT))}
                    className="px-2.5 py-1 rounded bg-[#0A1224] border border-[#1E3050] text-slate-300 hover:text-white disabled:opacity-40 cursor-pointer"
                  >
                    Previous
                  </button>
                  <button
                    disabled={pageOffset + PAGE_LIMIT >= totalEvents}
                    onClick={() => setPageOffset(pageOffset + PAGE_LIMIT)}
                    className="px-2.5 py-1 rounded bg-[#0A1224] border border-[#1E3050] text-slate-300 hover:text-white disabled:opacity-40 cursor-pointer"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </CyberCard>
        )}
      </div>

      {/* 5. Event Details Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
          <CyberCard className="max-w-3xl w-full p-6 space-y-4 max-h-[92vh] overflow-y-auto" glow="cyan" hoverEffect={false}>
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-[#1E3050]/80 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-sm text-white">Windows Event Telemetry Inspection</h3>
                  <StatusBadge status={(selectedRecord.category || 'unclassified').toLowerCase()} size="md" />
                </div>
                <div className="text-xs text-slate-400 font-mono mt-1">
                  ID: {selectedRecord.id} • Channel: <span className="text-cyan-300 font-bold">{selectedRecord.channel}</span> • Record ID: #{selectedRecord.record_id}
                </div>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#121E36] transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Raw Event Box */}
            <div className="p-3 rounded-xl bg-[#050811] border border-[#1E3050]">
              <div className="text-[10px] text-slate-500 uppercase font-mono mb-1">Raw Event Payload</div>
              <div className="text-xs font-mono text-cyan-200 break-words leading-relaxed">
                {selectedRecord.raw_log}
              </div>
            </div>

            {/* 3 Section Tabs */}
            <div className="flex items-center gap-2 border-b border-[#1E3050]/80 pb-2 text-xs font-mono">
              <button
                onClick={() => setActiveModalTab('facts')}
                className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                  activeModalTab === 'facts'
                    ? 'bg-cyan-600 text-white font-bold shadow-[0_0_10px_rgba(6,182,212,0.4)]'
                    : 'text-slate-400 hover:text-white bg-[#070D1A]'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>1. Observed Facts</span>
              </button>

              <button
                onClick={() => setActiveModalTab('model')}
                className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                  activeModalTab === 'model'
                    ? 'bg-cyan-600 text-white font-bold shadow-[0_0_10px_rgba(6,182,212,0.4)]'
                    : 'text-slate-400 hover:text-white bg-[#070D1A]'
                }`}
              >
                <Cpu className="w-3.5 h-3.5" />
                <span>2. Model Explanation & SHAP</span>
              </button>

              <button
                onClick={() => setActiveModalTab('security')}
                className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer ${
                  activeModalTab === 'security'
                    ? 'bg-cyan-600 text-white font-bold shadow-[0_0_10px_rgba(6,182,212,0.4)]'
                    : 'text-slate-400 hover:text-white bg-[#070D1A]'
                }`}
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>3. Security Interpretation</span>
              </button>
            </div>

            {/* TAB 1: Observed Facts */}
            {activeModalTab === 'facts' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
                  <div className="text-[11px] font-bold text-cyan-300 uppercase">Windows Event Metadata</div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                    <div className="flex justify-between border-b border-[#1E3050]/50 pb-1">
                      <span className="text-slate-400">Timestamp:</span>
                      <span className="text-white">{selectedRecord.timestamp}</span>
                    </div>
                    <div className="flex justify-between border-b border-[#1E3050]/50 pb-1">
                      <span className="text-slate-400">Channel:</span>
                      <span className="text-cyan-300 font-bold">{selectedRecord.channel || 'System'}</span>
                    </div>
                    <div className="flex justify-between border-b border-[#1E3050]/50 pb-1">
                      <span className="text-slate-400">Event ID:</span>
                      <span className="text-white font-bold">{selectedRecord.event_id || '-'}</span>
                    </div>
                    <div className="flex justify-between border-b border-[#1E3050]/50 pb-1">
                      <span className="text-slate-400">Record ID:</span>
                      <span className="text-slate-300">#{selectedRecord.record_id || '-'}</span>
                    </div>
                    <div className="flex justify-between border-b border-[#1E3050]/50 pb-1">
                      <span className="text-slate-400">Provider / Application:</span>
                      <span className="text-cyan-300">{selectedRecord.provider || selectedRecord.app_name}</span>
                    </div>
                    <div className="flex justify-between border-b border-[#1E3050]/50 pb-1">
                      <span className="text-slate-400">Severity Level:</span>
                      <span className="text-white">{selectedRecord.severity_label || 'Information'}</span>
                    </div>
                    <div className="flex justify-between border-b border-[#1E3050]/50 pb-1">
                      <span className="text-slate-400">Computer / Hostname:</span>
                      <span className="text-white">{selectedRecord.hostname || 'localhost'}</span>
                    </div>
                    <div className="flex justify-between border-b border-[#1E3050]/50 pb-1">
                      <span className="text-slate-400">Security User SID:</span>
                      <span className="text-amber-300 truncate max-w-[180px]">{selectedRecord.observed_facts?.detected_user || 'None'}</span>
                    </div>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
                  <div className="text-[11px] font-bold text-slate-300 uppercase">Observed Behavioral Flags</div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px]">
                    <div className={`p-2 rounded-lg border ${selectedRecord.observed_facts?.has_error_flag ? 'bg-rose-950/60 border-rose-500/50 text-rose-300' : 'bg-[#050811] border-[#1E3050] text-slate-500'}`}>
                      <span>Error Indicator: <b>{selectedRecord.observed_facts?.has_error_flag ? 'YES' : 'NO'}</b></span>
                    </div>
                    <div className={`p-2 rounded-lg border ${selectedRecord.observed_facts?.has_auth_flag ? 'bg-blue-950/60 border-blue-500/50 text-blue-300' : 'bg-[#050811] border-[#1E3050] text-slate-500'}`}>
                      <span>Auth Activity: <b>{selectedRecord.observed_facts?.has_auth_flag ? 'YES' : 'NO'}</b></span>
                    </div>
                    <div className={`p-2 rounded-lg border ${selectedRecord.observed_facts?.has_failed_auth_flag ? 'bg-rose-950/60 border-rose-500/50 text-rose-300' : 'bg-[#050811] border-[#1E3050] text-slate-500'}`}>
                      <span>Auth Failure: <b>{selectedRecord.observed_facts?.has_failed_auth_flag ? 'YES' : 'NO'}</b></span>
                    </div>
                    <div className={`p-2 rounded-lg border ${selectedRecord.observed_facts?.has_warning_flag ? 'bg-amber-950/60 border-amber-500/50 text-amber-300' : 'bg-[#050811] border-[#1E3050] text-slate-500'}`}>
                      <span>Warning Level: <b>{selectedRecord.observed_facts?.has_warning_flag ? 'YES' : 'NO'}</b></span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: Model Explanation */}
            {activeModalTab === 'model' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
                  <div className="text-[11px] font-bold text-cyan-300 uppercase">Model Inference Decision</div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px]">
                    <div className="p-2.5 rounded-lg bg-[#050811] border border-[#1E3050]">
                      <span className="text-[10px] text-slate-400 uppercase block">Category</span>
                      <span className="text-sm font-bold text-white">{selectedRecord.category}</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-[#050811] border border-[#1E3050]">
                      <span className="text-[10px] text-slate-400 uppercase block">Risk Score</span>
                      <span className="text-sm font-bold text-cyan-300">
                        {selectedRecord.risk_score !== null && selectedRecord.risk_score !== undefined
                          ? `${(selectedRecord.risk_score * 100).toFixed(1)}%`
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-[#050811] border border-[#1E3050]">
                      <span className="text-[10px] text-slate-400 uppercase block">Confidence</span>
                      <span className="text-sm font-bold text-slate-300">
                        {selectedRecord.confidence !== null && selectedRecord.confidence !== undefined
                          ? `${(selectedRecord.confidence * 100).toFixed(1)}%`
                          : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <div className="pt-2 text-xs text-slate-300 leading-relaxed font-sans">
                    <strong>Explanation Summary: </strong>
                    <span>{selectedRecord.explanation_summary || 'No explanation available.'}</span>
                  </div>
                </div>

                {/* SHAP Contributions */}
                {selectedRecord.shap && selectedRecord.shap.available && selectedRecord.shap.contributions?.length > 0 ? (
                  <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050] space-y-2">
                    <div className="text-[11px] font-bold text-cyan-300 uppercase">SHAP Feature Contributions</div>
                    <div className="space-y-1.5 text-[11px]">
                      {selectedRecord.shap.contributions.map((c, i) => (
                        <div key={i} className="flex items-center justify-between p-1.5 rounded bg-[#050811] border border-[#1E3050]/60">
                          <span className="text-slate-300">{c.feature}</span>
                          <span className={`font-bold ${c.direction === 'anomaly' ? 'text-rose-400' : 'text-cyan-400'}`}>
                            {c.contribution > 0 ? `+${c.contribution.toFixed(4)}` : c.contribution.toFixed(4)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050] text-slate-400 text-xs">
                    SHAP feature contributions are not calculated for unclassified events or when no compatible tree model is active.
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: Security Interpretation */}
            {activeModalTab === 'security' && (
              <div className="space-y-3 font-mono text-xs">
                <div className="p-4 rounded-xl bg-[#070D1A] border border-amber-500/30 space-y-2">
                  <div className="flex items-center gap-2 text-amber-300 font-bold text-xs uppercase">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    <span>Operational SOC Interpretation</span>
                  </div>
                  <p className="text-xs text-slate-300 font-sans leading-relaxed pt-1">
                    {selectedRecord.security_interpretation ||
                      'Event collected directly from Windows Event Log. Statistical anomaly classification requires an active, compatible trained model.'}
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#070D1A] border border-[#1E3050] text-slate-400 text-[11px] font-sans leading-relaxed">
                  <strong>Analyst Note:</strong> A model anomaly detection flag denotes statistical divergence from baseline system behavior. It does not constitute proof of a cyberattack. Always corroborate with network telemetry and security controls.
                </div>
              </div>
            )}
          </CyberCard>
        </div>
      )}
    </div>
  );
};

export default AnalysisPage;
