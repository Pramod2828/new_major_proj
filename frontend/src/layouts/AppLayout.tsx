import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  Activity,
  Database,
  Cpu,
  BarChart2,
  Search,
  Sliders,
  Layers,
  Download,
  Settings,
  RefreshCw,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
  Wifi,
  WifiOff,
  Clock,
  ExternalLink,
  Info
} from 'lucide-react';
import { api } from '../services/api';
import { StatusBadge } from '../components/common/StatusBadge';

interface AppLayoutProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  currentTab,
  setCurrentTab,
  children,
}) => {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [activeModel, setActiveModel] = useState<any>(null);
  const [systemHealthy, setSystemHealthy] = useState<boolean>(true);
  const [loadingStatus, setLoadingStatus] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<string>('');

  const fetchStatus = async () => {
    try {
      setLoadingStatus(true);
      const health = await api.getHealth();
      setSystemHealthy(health.status === 'healthy');
      const active = await api.getActiveModel();
      if (active.active) {
        setActiveModel(active.model);
      } else {
        setActiveModel(null);
      }
    } catch {
      setSystemHealthy(false);
      setActiveModel(null);
    } finally {
      setLoadingStatus(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 20000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toTimeString().substring(0, 8) + ' UTC');
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const navItems = [
    { id: 'dashboard', label: 'SOC Dashboard', icon: Activity, short: 'Overview' },
    { id: 'datasets', label: 'Dataset Manager', icon: Database, short: 'Data' },
    { id: 'analysis', label: 'Live Log Analysis', icon: Search, short: 'Inference' },

    { id: 'shap', label: 'SHAP Explainability', icon: Sliders, short: 'Explain' },
    { id: 'history', label: 'Anomaly History', icon: Layers, short: 'Audit' },
    { id: 'reports', label: 'Audit Reports', icon: Download, short: 'Reports' },
    { id: 'settings', label: 'Settings & Status', icon: Settings, short: 'Config' },
    { id: 'about', label: 'About Project', icon: Info, short: 'About' },
  ];

  return (
    <div className="flex h-screen w-screen bg-[#060913] text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <motion.aside
        animate={{ width: collapsed ? 76 : 260 }}
        transition={{ duration: 0.25, ease: 'easeInOut' }}
        className="bg-[#0B1222]/95 border-r border-[#1E3050]/80 flex flex-col justify-between shrink-0 z-30 shadow-2xl relative"
      >
        <div>
          {/* Brand Header */}
          <div className="h-16 px-4 border-b border-[#1E3050]/80 flex items-center justify-between">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="p-2 rounded-xl bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.25)] shrink-0">
                <Shield className="w-5 h-5" />
              </div>
              {!collapsed && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="overflow-hidden whitespace-nowrap"
                >
                  <div className="font-extrabold text-sm tracking-wider text-white flex items-center gap-1.5">
                    <span>SMART-LOG</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-900/60 text-cyan-300 font-mono border border-cyan-500/30">
                      v1.0
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 font-medium tracking-tight">Enterprise Syslog SOC</p>
                </motion.div>
              )}
            </div>

            <button
              onClick={() => setCollapsed(!collapsed)}
              title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#15233E] transition-colors"
            >
              {collapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
            </button>
          </div>

          {/* Active Model Mini Pill (When expanded) */}
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="m-3 p-3 rounded-xl bg-[#070D1A]/90 border border-[#1E3050]/90 shadow-sm"
            >
              <div className="flex items-center justify-between text-[10px] uppercase font-mono tracking-wider text-slate-400 mb-1">
                <span>Active Model</span>
                <button onClick={fetchStatus} title="Refresh Model">
                  <RefreshCw className={`w-3 h-3 hover:text-cyan-400 ${loadingStatus ? 'animate-spin text-cyan-400' : ''}`} />
                </button>
              </div>

              {activeModel ? (
                <div>
                  <div className="text-xs font-semibold text-cyan-300 truncate flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)] shrink-0 animate-pulse" />
                    <span className="truncate">{activeModel.name}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                    {activeModel.algorithm.toUpperCase()} • v{activeModel.version}
                  </div>
                </div>
              ) : (
                <div className="text-[11px] text-amber-400 font-mono flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.8)] shrink-0" />
                  <span>No Model Active</span>
                </div>
              )}
            </motion.div>
          )}

          {/* Navigation Links */}
          <nav className="p-2 space-y-1 mt-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <div key={item.id} className="relative group">
                  <button
                    onClick={() => setCurrentTab(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-gradient-to-r from-cyan-950/80 to-blue-950/40 text-cyan-300 border-l-2 border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.15)] font-semibold'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-[#121E36]/60 border-l-2 border-transparent'
                    } ${collapsed ? 'justify-center px-0' : ''}`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-cyan-400' : 'text-slate-400 group-hover:text-cyan-300'}`} />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                  </button>

                  {/* Tooltip when collapsed */}
                  {collapsed && (
                    <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 px-2.5 py-1 rounded-md bg-[#0D182E] border border-cyan-500/30 text-white text-xs font-mono whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                      {item.label}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
        </div>

        {/* Bottom Health Bar */}
        <div className="p-3 border-t border-[#1E3050]/80 bg-[#070D1A]/80">
          <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} text-xs`}>
            {!collapsed && (
              <span className="text-slate-400 text-[11px] flex items-center gap-1.5 font-mono">
                {systemHealthy ? <Wifi className="w-3.5 h-3.5 text-emerald-400" /> : <WifiOff className="w-3.5 h-3.5 text-rose-400" />}
                REST API
              </span>
            )}
            <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded ${
              systemHealthy ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30' : 'bg-rose-950 text-rose-400 border border-rose-500/30'
            }`}>
              {systemHealthy ? (collapsed ? 'LIVE' : 'ONLINE') : 'OFFLINE'}
            </span>
          </div>
        </div>
      </motion.aside>

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        {/* Subtle scanline effect across top */}
        <div className="scanline-effect" />

        {/* Top Header */}
        <header className="h-16 bg-[#0B1222]/90 border-b border-[#1E3050]/80 px-6 flex items-center justify-between shrink-0 backdrop-blur-md z-20">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-bold text-white tracking-wider uppercase font-mono flex items-center gap-2">
              <span className="text-cyan-400">SOC</span>
              <span className="text-slate-600">/</span>
              <span>{navItems.find((n) => n.id === currentTab)?.label || 'Dashboard'}</span>
            </h1>
            <span className="hidden sm:inline-flex px-2 py-0.5 rounded-full bg-[#121F38] text-[10px] font-mono text-cyan-400 border border-cyan-500/30">
              ENTERPRISE EDITION
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            {/* Clock */}
            <div className="hidden md:flex items-center gap-1.5 text-slate-400 px-3 py-1 rounded-lg bg-[#070D1A] border border-[#1E3050]">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <span>{currentTime}</span>
            </div>

            {/* Backend Heartbeat */}
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-[#070D1A] border border-[#1E3050]">
              <span className={`w-2 h-2 rounded-full ${systemHealthy ? 'bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse' : 'bg-rose-400 shadow-[0_0_8px_rgba(244,63,94,0.8)]'}`} />
              <span className="text-slate-300 font-semibold">{systemHealthy ? 'API CONNECTED' : 'DISCONNECTED'}</span>
            </div>

            {/* Refresh Action */}
            <button
              onClick={fetchStatus}
              title="Refresh Global Telemetry"
              className="p-1.5 rounded-lg bg-[#070D1A] border border-[#1E3050] hover:border-cyan-500/40 text-slate-300 hover:text-white transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingStatus ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
          </div>
        </header>

        {/* Scrollable Main Canvas */}
        <main className="flex-1 overflow-y-auto cyber-grid-bg cyber-radial-glow p-6 md:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentTab}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="max-w-7xl mx-auto"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
};
