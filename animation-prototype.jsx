import { useState, useEffect, useRef, useCallback } from "react";

const NODES = [
  { id: "vigil", label: "VIGIL", sub: "auditor", x: 0.5, y: 0.48, score: null, color: "#22c55e", radius: 64, glow: true },
  { id: "tradingbot", label: "TradingBot", x: 0.28, y: 0.18, score: 0.97, color: "#22c55e", radius: 38 },
  { id: "defiagent", label: "DeFiAgent", x: 0.78, y: 0.15, score: 0.99, color: "#22c55e", radius: 40 },
  { id: "uniswap", label: "Uniswap", x: 0.2, y: 0.42, score: 0.99, color: "#22c55e", radius: 36 },
  { id: "nftbot", label: "NFTBot", x: 0.26, y: 0.7, score: 0.82, color: "#a855f7", radius: 34 },
  { id: "flagged", label: "Flagged", x: 0.85, y: 0.42, score: 0.12, color: "#ef4444", radius: 32 },
  { id: "unknown", label: "Unknown", x: 0.76, y: 0.68, score: 0.41, color: "#f59e0b", radius: 38 },
];

const EDGES = [
  { from: "vigil", to: "tradingbot", color: "#22c55e" },
  { from: "vigil", to: "defiagent", color: "#22c55e" },
  { from: "vigil", to: "uniswap", color: "#22c55e" },
  { from: "vigil", to: "nftbot", color: "#a855f7" },
  { from: "vigil", to: "flagged", color: "#ef4444" },
  { from: "vigil", to: "unknown", color: "#f59e0b" },
  { from: "tradingbot", to: "uniswap", color: "#22c55e" },
  { from: "defiagent", to: "flagged", color: "#ef4444" },
  { from: "nftbot", to: "unknown", color: "#f59e0b" },
];

const PIPELINE_STAGES = [
  { id: "perception", label: "Perception", sub: "Statistical filter, z-score baselines", color: "#22c55e", layer: 1 },
  { id: "policy", label: "Policy", sub: "Natural language rules, boundaries", color: "#6366f1", layer: 2 },
  { id: "reasoning", label: "Reasoning", sub: "Intent analysis, drift detection", color: "#f59e0b", layer: 3 },
  { id: "signal", label: "Signal", sub: "ERC-8004 receipt, reputation update", color: "#a855f7", layer: 4 },
];

/* clip edge endpoint to circle border */
function clipToCircle(ax, ay, bx, by, r) {
  const dx = bx - ax, dy = by - ay;
  const dist = Math.sqrt(dx * dx + dy * dy);
  if (dist === 0) return { x: ax, y: ay };
  return { x: ax + (dx / dist) * r, y: ay + (dy / dist) * r };
}

/* graph edge particles */
function useParticles(edges, nodeMap, w, h, active) {
  const [particles, setParticles] = useState([]);
  const raf = useRef();
  const prev = useRef(0);

  useEffect(() => {
    if (!active || w === 0) return;
    const pts = edges.flatMap((e, ei) =>
      Array.from({ length: 3 }, (_, i) => ({
        id: `${ei}-${i}`, edge: ei, t: i / 3,
        speed: 0.002 + Math.random() * 0.003,
        size: 2 + Math.random() * 2,
      }))
    );
    setParticles(pts);
    const tick = (ts) => {
      const dt = ts - prev.current; prev.current = ts;
      if (dt > 100) { raf.current = requestAnimationFrame(tick); return; }
      setParticles(p => p.map(pt => ({ ...pt, t: (pt.t + pt.speed * (dt / 16)) % 1 })));
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [active, edges, w, h]);

  return particles.map(pt => {
    const e = edges[pt.edge];
    const a = nodeMap[e.from], b = nodeMap[e.to];
    if (!a || !b) return null;
    const ax = a.x * w, ay = a.y * h, bx = b.x * w, by = b.y * h;
    const start = clipToCircle(ax, ay, bx, by, a.radius + 6);
    const end = clipToCircle(bx, by, ax, ay, b.radius + 6);
    return { ...pt, x: start.x + (end.x - start.x) * pt.t, y: start.y + (end.y - start.y) * pt.t, color: e.color };
  }).filter(Boolean);
}

function lerpColor(c1, c2, t) {
  const r = Math.round(parseInt(c1.slice(1, 3), 16) * (1 - t) + parseInt(c2.slice(1, 3), 16) * t);
  const g = Math.round(parseInt(c1.slice(3, 5), 16) * (1 - t) + parseInt(c2.slice(3, 5), 16) * t);
  const b = Math.round(parseInt(c1.slice(5, 7), 16) * (1 - t) + parseInt(c2.slice(5, 7), 16) * t);
  return `rgb(${r},${g},${b})`;
}

/* ── Graph View ── */
function GraphView({ width, height }) {
  const [hovered, setHovered] = useState(null);
  const [appeared, setAppeared] = useState(false);
  const nodeMap = {}; NODES.forEach(n => { nodeMap[n.id] = n; });
  const particles = useParticles(EDGES, nodeMap, width, height, appeared);

  useEffect(() => { const t = setTimeout(() => setAppeared(true), 100); return () => clearTimeout(t); }, []);

  const scoreColor = s => s >= 0.9 ? "#22c55e" : s >= 0.7 ? "#a855f7" : s >= 0.3 ? "#f59e0b" : "#ef4444";

  return (
    <svg width={width} height={height} style={{ position: "absolute", top: 0, left: 0 }}>
      <defs>
        {NODES.map(n => (
          <radialGradient key={`glow-${n.id}`} id={`glow-${n.id}`}>
            <stop offset="0%" stopColor={n.color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={n.color} stopOpacity="0" />
          </radialGradient>
        ))}
        <filter id="bloom"><feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" /><feComposite in="SourceGraphic" in2="blur" operator="over" /></filter>
        <filter id="particleBloom"><feGaussianBlur stdDeviation="3" /></filter>
        {["#22c55e", "#a855f7", "#ef4444", "#f59e0b"].map(c => (
          <marker key={`arr-${c}`} id={`arr-${c.replace("#", "")}`} viewBox="0 0 10 8" refX="9" refY="4" markerWidth="7" markerHeight="5.5" orient="auto">
            <path d="M0,1 L8,4 L0,7 Z" fill={c} fillOpacity="0.7" />
          </marker>
        ))}
      </defs>

      {/* edges clipped to borders */}
      {EDGES.map((e, i) => {
        const a = nodeMap[e.from], b = nodeMap[e.to];
        const ax = a.x * width, ay = a.y * height, bx = b.x * width, by = b.y * height;
        const start = clipToCircle(ax, ay, bx, by, a.radius + 6);
        const end = clipToCircle(bx, by, ax, ay, b.radius + 12);
        const isH = hovered === e.from || hovered === e.to;
        return (
          <g key={i}>
            {isH && <line x1={start.x} y1={start.y} x2={end.x} y2={end.y} stroke={e.color} strokeWidth={5} strokeOpacity={0.1} filter="url(#bloom)" />}
            <line
              x1={start.x} y1={start.y} x2={end.x} y2={end.y}
              stroke={e.color} strokeWidth={isH ? 2 : 1}
              strokeOpacity={appeared ? (isH ? 0.7 : 0.2) : 0}
              markerEnd={`url(#arr-${e.color.replace("#", "")})`}
              style={{ transition: "stroke-opacity 1.2s ease, stroke-width 0.3s ease" }}
            />
          </g>
        );
      })}

      {/* particles */}
      {particles.map(pt => (
        <g key={pt.id}>
          <circle cx={pt.x} cy={pt.y} r={pt.size * 2.5} fill={pt.color} opacity={0.15} filter="url(#particleBloom)" />
          <circle cx={pt.x} cy={pt.y} r={pt.size} fill={pt.color} opacity={0.7} />
        </g>
      ))}

      {/* nodes */}
      {NODES.map((n, i) => {
        const cx = n.x * width, cy = n.y * height;
        const isH = hovered === n.id;
        return (
          <g key={n.id}
            style={{
              transform: `translate(${cx}px, ${cy}px) scale(${appeared ? (isH ? 1.08 : 1) : 0.3})`,
              opacity: appeared ? 1 : 0,
              transition: `transform 0.8s cubic-bezier(0.16,1,0.3,1) ${i * 0.08}s, opacity 0.6s ease ${i * 0.08}s`,
              cursor: "pointer", transformOrigin: "0 0",
            }}
            onMouseEnter={() => setHovered(n.id)} onMouseLeave={() => setHovered(null)}
          >
            <circle cx={0} cy={0} r={n.radius * 2.2} fill={`url(#glow-${n.id})`} opacity={isH ? 1 : 0.5} style={{ transition: "opacity 0.3s" }} />
            <circle cx={0} cy={0} r={n.radius} fill="rgba(10,10,15,0.9)" stroke={n.color} strokeWidth={isH ? 2.5 : 1.5} strokeOpacity={isH ? 0.9 : 0.5} style={{ transition: "all 0.3s" }} />
            <text y={n.id === "vigil" ? -8 : (n.score !== null ? -6 : 0)} textAnchor="middle" fill={n.color}
              fontSize={n.id === "vigil" ? 22 : 13} fontWeight="700" fontFamily="'JetBrains Mono', monospace"
              style={{ letterSpacing: n.id === "vigil" ? "3px" : "0.5px" }}>
              {n.label}
            </text>
            {n.id === "vigil" && <text y={14} textAnchor="middle" fill={n.color} fontSize={11} fontFamily="'JetBrains Mono', monospace" opacity={0.5}>auditor</text>}
            {n.score !== null && <text y={12} textAnchor="middle" fill={scoreColor(n.score)} fontSize={12} fontWeight="600" fontFamily="'JetBrains Mono', monospace">{n.score.toFixed(2)}</text>}
          </g>
        );
      })}
    </svg>
  );
}

/* ── Pipeline View ── */
function PipelineView({ width, height }) {
  const [appeared, setAppeared] = useState(false);
  const [activeStage, setActiveStage] = useState(null);
  const [dashOffset, setDashOffset] = useState(0);
  const [arrowT, setArrowT] = useState(0);
  const raf2 = useRef();

  useEffect(() => { const t = setTimeout(() => setAppeared(true), 100); return () => clearTimeout(t); }, []);

  useEffect(() => {
    let prev = 0;
    const tick = ts => {
      const dt = prev ? ts - prev : 0;
      prev = ts;
      setDashOffset(d => (d - dt * 0.06) % 1000);
      setArrowT(t => (t + dt * 0.00035) % 1);
      raf2.current = requestAnimationFrame(tick);
    };
    raf2.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf2.current);
  }, []);

  const stages = PIPELINE_STAGES;
  const boxW = Math.min(120, width * 0.12);
  const boxH = Math.min(52, height * 0.11);
  const gapCount = stages.length - 1;
  const availGap = width - stages.length * boxW - 60;
  const gap = Math.max(80, availGap / gapCount);
  const totalSpan = stages.length * boxW + gapCount * gap;
  const startX = (width - totalSpan) / 2;
  const cy = height * 0.42;

  const boxes = stages.map((s, i) => ({ ...s, bx: startX + i * (boxW + gap), by: cy - boxH / 2 }));

  const arrows = [];
  for (let i = 0; i < boxes.length - 1; i++) {
    arrows.push({
      x1: boxes[i].bx + boxW, y1: cy,
      x2: boxes[i + 1].bx, y2: cy,
      fromColor: boxes[i].color, toColor: boxes[i + 1].color,
    });
  }

  // Animated arrow chevrons per segment
  const NUM_ARROWS = 4;
  const arrowSize = 6;

  return (
    <svg width={width} height={height} style={{ position: "absolute", top: 0, left: 0 }}>
      <defs>
        {stages.map(s => (
          <radialGradient key={`pg-${s.id}`} id={`pg-${s.id}`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={s.color} stopOpacity="0.1" />
            <stop offset="100%" stopColor={s.color} stopOpacity="0" />
          </radialGradient>
        ))}
        <filter id="pbloom"><feGaussianBlur stdDeviation="5" /></filter>
        {stages.map(s => (
          <marker key={`parr-${s.id}`} id={`parr-${s.id}`} viewBox="0 0 12 10" refX="11" refY="5" markerWidth="14" markerHeight="10" orient="auto">
            <path d="M0,1.5 L10,5 L0,8.5 Z" fill={s.color} fillOpacity="0.9" />
          </marker>
        ))}
        {arrows.map((a, i) => (
          <linearGradient key={`ag-${i}`} id={`ag-${i}`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={a.fromColor} /><stop offset="100%" stopColor={a.toColor} />
          </linearGradient>
        ))}
      </defs>

      {/* arrows between boxes */}
      {arrows.map((a, i) => {
        const nextStage = stages[i + 1];
        const pad = 4;
        const ax1 = a.x1 + pad, ax2 = a.x2 - pad;
        const len = ax2 - ax1;
        return (
          <g key={`arrow-${i}`}>
            {/* wide glow trail */}
            <line x1={ax1} y1={a.y1} x2={ax2} y2={a.y2}
              stroke={`url(#ag-${i})`} strokeWidth={8} strokeOpacity={appeared ? 0.05 : 0} filter="url(#pbloom)"
              style={{ transition: `stroke-opacity 0.6s ease ${0.4 + i * 0.15}s` }} />
            {/* solid base line */}
            <line x1={ax1} y1={a.y1} x2={ax2} y2={a.y2}
              stroke={`url(#ag-${i})`} strokeWidth={1.5} strokeOpacity={appeared ? 0.2 : 0}
              style={{ transition: `stroke-opacity 0.8s ease ${0.4 + i * 0.15}s` }} />
            {/* animated flowing segments */}
            <line x1={ax1} y1={a.y1} x2={ax2} y2={a.y2}
              stroke={`url(#ag-${i})`} strokeWidth={2.5} strokeOpacity={appeared ? 0.45 : 0}
              strokeDasharray={`${len * 0.15} ${len * 0.1}`}
              strokeDashoffset={dashOffset}
              strokeLinecap="round"
              style={{ transition: `stroke-opacity 0.8s ease ${0.4 + i * 0.15}s` }} />
            {/* arrowhead */}
            <line x1={ax1} y1={a.y1} x2={ax2} y2={a.y2}
              stroke="transparent" strokeWidth={1}
              markerEnd={`url(#parr-${nextStage.id})`} />
          </g>
        );
      })}

      {/* animated flowing arrows along connections */}
      {appeared && arrows.map((a, i) => {
        const pad = 4;
        const ax1 = a.x1 + pad, ax2 = a.x2 - pad;
        const len = ax2 - ax1;
        return Array.from({ length: NUM_ARROWS }, (_, j) => {
          const t = ((arrowT * NUM_ARROWS + j) / NUM_ARROWS) % 1;
          const x = ax1 + len * t;
          const opacity = Math.sin(t * Math.PI) * 0.7 + 0.1; // fade at edges
          const color = lerpColor(a.fromColor, a.toColor, t);
          return (
            <g key={`fa-${i}-${j}`} style={{ opacity }}>
              {/* glow behind arrow */}
              <circle cx={x} cy={cy} r={arrowSize * 1.8} fill={color} opacity={0.12} filter="url(#pbloom)" />
              {/* chevron arrow shape */}
              <polygon
                points={`${x - arrowSize},${cy - arrowSize * 0.6} ${x + arrowSize},${cy} ${x - arrowSize},${cy + arrowSize * 0.6}`}
                fill={color}
                opacity={0.85}
              />
              {/* trailing line */}
              <line
                x1={x - arrowSize * 2.5} y1={cy} x2={x - arrowSize} y2={cy}
                stroke={color} strokeWidth={2} strokeOpacity={0.4}
                strokeLinecap="round"
              />
            </g>
          );
        });
      })}

      {/* stage boxes */}
      {boxes.map((s, i) => {
        const isH = activeStage === s.id;
        return (
          <g key={s.id}
            style={{
              opacity: appeared ? 1 : 0, transform: `translateY(${appeared ? 0 : 20}px)`,
              transition: `opacity 0.6s ease ${i * 0.12}s, transform 0.6s cubic-bezier(0.16,1,0.3,1) ${i * 0.12}s`,
              cursor: "pointer",
            }}
            onMouseEnter={() => setActiveStage(s.id)} onMouseLeave={() => setActiveStage(null)}
          >
            {/* glow */}
            <rect x={s.bx - 18} y={s.by - 18} width={boxW + 36} height={boxH + 36} rx={16}
              fill={`url(#pg-${s.id})`} opacity={isH ? 1 : 0.4} style={{ transition: "opacity 0.3s" }} />
            {/* box */}
            <rect x={s.bx} y={s.by} width={boxW} height={boxH} rx={8}
              fill="rgba(10,10,18,0.92)" stroke={s.color}
              strokeWidth={isH ? 2 : 1.2} strokeOpacity={isH ? 0.85 : 0.35}
              style={{ transition: "all 0.3s", filter: isH ? `drop-shadow(0 0 14px ${s.color}55)` : "none" }} />
            {/* layer badge */}
            <text x={s.bx + boxW - 8} y={s.by + 12} textAnchor="end" fill={s.color} fontSize={7} fontWeight="600" fontFamily="'JetBrains Mono', monospace" opacity={0.35}>
              {s.layer}
            </text>
            {/* full label */}
            <text x={s.bx + boxW / 2} y={s.by + boxH / 2 + 5} textAnchor="middle" fill={s.color} fontSize={14} fontWeight="700" fontFamily="'JetBrains Mono', monospace">
              {s.label}
            </text>
          </g>
        );
      })}

      {/* flow label */}
      <g style={{ opacity: appeared ? 1 : 0, transition: "opacity 1s ease 0.8s" }}>
        <text x={width / 2} y={cy + boxH / 2 + 40} textAnchor="middle" fill="#334155" fontSize={11} fontFamily="'JetBrains Mono', monospace" letterSpacing="4px">
          DATA FLOW
        </text>
        <text x={width / 2 + 48} y={cy + boxH / 2 + 40} fill="#334155" fontSize={11} fontFamily="'JetBrains Mono', monospace">
          →
        </text>
      </g>
    </svg>
  );
}

/* ── Background particles ── */
function BgParticles({ width, height }) {
  const [dots, setDots] = useState([]);
  const raf = useRef();
  useEffect(() => {
    if (!width) return;
    const pts = Array.from({ length: 40 }, () => ({
      x: Math.random() * width, y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.15, vy: (Math.random() - 0.5) * 0.15,
      r: 1 + Math.random() * 1.5, o: 0.08 + Math.random() * 0.12,
    }));
    setDots(pts);
    let prev = 0;
    const tick = ts => {
      const dt = ts - prev; prev = ts;
      if (dt > 100) { raf.current = requestAnimationFrame(tick); return; }
      setDots(d => d.map(p => {
        let nx = p.x + p.vx * dt * 0.06, ny = p.y + p.vy * dt * 0.06;
        if (nx < 0 || nx > width) p.vx *= -1;
        if (ny < 0 || ny > height) p.vy *= -1;
        return { ...p, x: Math.max(0, Math.min(width, nx)), y: Math.max(0, Math.min(height, ny)) };
      }));
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [width, height]);

  return (
    <svg width={width} height={height} style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none" }}>
      {dots.map((d, i) => <circle key={i} cx={d.x} cy={d.y} r={d.r} fill="#94a3b8" opacity={d.o} />)}
    </svg>
  );
}

/* ── Main ── */
export default function App() {
  const [view, setView] = useState("graph");
  const containerRef = useRef(null);
  const [dims, setDims] = useState({ w: 0, h: 0 });

  const measure = useCallback(() => {
    if (containerRef.current) {
      const r = containerRef.current.getBoundingClientRect();
      setDims({ w: r.width, h: r.height });
    }
  }, []);

  useEffect(() => { measure(); window.addEventListener("resize", measure); return () => window.removeEventListener("resize", measure); }, [measure]);
  useEffect(() => { measure(); }, [view, measure]);

  return (
    <div style={{
      width: "100%", height: "100vh", background: "#0a0a0f",
      fontFamily: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace",
      display: "flex", flexDirection: "column", overflow: "hidden", position: "relative",
    }}>
      <div style={{ position: "absolute", inset: 0, pointerEvents: "none",
        background: "radial-gradient(ellipse at 40% 40%, rgba(34,197,94,0.04) 0%, transparent 60%), radial-gradient(ellipse at 80% 60%, rgba(99,102,241,0.03) 0%, transparent 50%)" }} />

      {/* header */}
      <div style={{ padding: "20px 28px", display: "flex", alignItems: "center", justifyContent: "space-between",
        borderBottom: "1px solid rgba(255,255,255,0.06)", position: "relative", zIndex: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 12px rgba(34,197,94,0.6)" }} />
          <span style={{ color: "#22c55e", fontSize: 15, fontWeight: 700, letterSpacing: 3 }}>VIGIL</span>
          <span style={{ color: "#475569", fontSize: 12, marginLeft: 4 }}>v0.4.2</span>
        </div>
        <div style={{ display: "flex", background: "rgba(255,255,255,0.04)", borderRadius: 8, padding: 3, gap: 2 }}>
          {[{ key: "graph", label: "Network Graph" }, { key: "pipeline", label: "Pipeline" }].map(v => (
            <button key={v.key} onClick={() => setView(v.key)} style={{
              padding: "8px 20px", borderRadius: 6, border: "none", cursor: "pointer",
              fontSize: 12, fontWeight: 600, fontFamily: "inherit", letterSpacing: 0.5,
              transition: "all 0.25s ease",
              background: view === v.key ? "rgba(255,255,255,0.08)" : "transparent",
              color: view === v.key ? "#e2e8f0" : "#64748b",
              boxShadow: view === v.key ? "0 1px 4px rgba(0,0,0,0.3)" : "none",
            }}>{v.label}</button>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ color: "#22c55e", fontSize: 11 }}>6 agents monitored</span>
          <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e", animation: "blink 2s infinite" }} />
        </div>
      </div>

      {/* canvas */}
      <div ref={containerRef} style={{ flex: 1, position: "relative", overflow: "hidden" }}>
        {dims.w > 0 && (
          <>
            <BgParticles width={dims.w} height={dims.h} />
            <div key={view} style={{ position: "absolute", inset: 0, animation: "fadeIn 0.5s ease forwards" }}>
              {view === "graph" ? <GraphView width={dims.w} height={dims.h} /> : <PipelineView width={dims.w} height={dims.h} />}
            </div>
          </>
        )}
      </div>

      {/* bottom bar */}
      <div style={{ padding: "12px 28px", borderTop: "1px solid rgba(255,255,255,0.06)",
        display: "flex", justifyContent: "space-between", alignItems: "center",
        fontSize: 11, color: "#475569", position: "relative", zIndex: 10 }}>
        <span>Last scan: 2.4s ago</span>
        <div style={{ display: "flex", gap: 20 }}>
          <span>Latency: <span style={{ color: "#22c55e" }}>12ms</span></span>
          <span>Throughput: <span style={{ color: "#6366f1" }}>1.2k tx/s</span></span>
          <span>Anomalies: <span style={{ color: "#f59e0b" }}>2</span></span>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700;800&display=swap');
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
      `}</style>
    </div>
  );
}
