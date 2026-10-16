import React from 'react';
import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';

export const CyberShield3D: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`relative flex items-center justify-center select-none ${className}`}>
      {/* Ambient Pulsing Glow behind emblem */}
      <div className="absolute w-36 h-36 rounded-full bg-cyan-500/15 blur-2xl animate-pulse" />
      <div className="absolute w-28 h-28 rounded-full bg-blue-600/10 blur-xl" />

      {/* Rotating Outer Cyber Orbit Ring */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
        className="absolute w-32 h-32 rounded-full border border-dashed border-cyan-500/30"
      />

      {/* Counter-rotating Segmented Middle Ring */}
      <motion.div
        animate={{ rotate: -360 }}
        transition={{ duration: 18, repeat: Infinity, ease: 'linear' }}
        className="absolute w-24 h-24 rounded-full border-t border-b border-cyan-400/50 border-l-transparent border-r-transparent"
      />

      {/* Hexagonal Radar Frame */}
      <motion.div
        animate={{ scale: [1, 1.04, 1] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
        className="relative z-10 w-16 h-16 rounded-2xl bg-gradient-to-br from-[#0E1A33] to-[#0A1224] border border-cyan-500/40 shadow-[0_0_25px_rgba(6,182,212,0.3)] flex items-center justify-center transform-gpu"
        style={{
          boxShadow: '0 0 20px rgba(6, 182, 212, 0.25), inset 0 0 15px rgba(6, 182, 212, 0.15)',
        }}
      >
        {/* Holographic Shield Icon */}
        <Shield className="w-8 h-8 text-cyan-400 drop-shadow-[0_0_10px_rgba(6,182,212,0.6)]" />

        {/* Core Beacon Dot */}
        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyan-400" />
      </motion.div>
    </div>
  );
};
