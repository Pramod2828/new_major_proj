import React from 'react';
import { motion } from 'framer-motion';

interface CyberCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: 'cyan' | 'rose' | 'emerald' | 'amber' | 'none';
  hoverEffect?: boolean;
  onClick?: () => void;
}

export const CyberCard: React.FC<CyberCardProps> = ({
  children,
  className = '',
  glow = 'none',
  hoverEffect = true,
  onClick,
}) => {
  const glowStyles = {
    cyan: 'border-cyan-500/30 hover:border-cyan-400/60 hover:shadow-[0_0_25px_-5px_rgba(6,182,212,0.25)]',
    rose: 'border-rose-500/30 hover:border-rose-400/60 hover:shadow-[0_0_25px_-5px_rgba(244,63,94,0.25)]',
    emerald: 'border-emerald-500/30 hover:border-emerald-400/60 hover:shadow-[0_0_25px_-5px_rgba(16,185,129,0.25)]',
    amber: 'border-amber-500/30 hover:border-amber-400/60 hover:shadow-[0_0_25px_-5px_rgba(245,158,11,0.25)]',
    none: 'border-[#1E3050]/70 hover:border-cyan-500/40 hover:shadow-[0_0_20px_-5px_rgba(6,182,212,0.12)]',
  };

  return (
    <motion.div
      whileHover={hoverEffect ? { y: -3, transition: { duration: 0.2 } } : undefined}
      onClick={onClick}
      className={`relative rounded-xl bg-[#0D1526]/75 backdrop-blur-md border ${glowStyles[glow]} transition-all duration-300 ${className} ${onClick ? 'cursor-pointer' : ''}`}
    >
      {/* Corner micro-accents for high-tech aesthetic */}
      <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-cyan-400/30 rounded-tl pointer-events-none" />
      <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-cyan-400/30 rounded-tr pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-cyan-400/30 rounded-bl pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-cyan-400/30 rounded-br pointer-events-none" />

      {children}
    </motion.div>
  );
};
