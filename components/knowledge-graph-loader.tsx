"use client";

import { AnimatePresence, motion, useMotionValue, useSpring } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";

interface KnowledgeGraphLoaderProps {
    status?: string;
    onReady?: () => void;
    className?: string;
}

interface GraphNode {
    id: string;
    x: number;
    y: number;
    delay: number;
    size: number;
}

interface GraphEdge {
    id: string;
    from: string;
    to: string;
    delay: number;
}

const EASE_OUT: [number, number, number, number] = [0.22, 1, 0.36, 1];
const CAMERA_EASE: [number, number, number, number] = [0.45, 0, 0.55, 1];
const COPY_STEPS = [
    "Understanding your topic...",
    "Structuring concepts...",
    "Connecting ideas...",
    "Building visual explanations...",
];

const NODES: GraphNode[] = [
    { id: "core", x: 0, y: 0, delay: 0.1, size: 5.2 },
    { id: "n1", x: 30, y: -8, delay: 0.28, size: 3.8 },
    { id: "n2", x: 10, y: -32, delay: 0.43, size: 3.6 },
    { id: "n3", x: -24, y: -20, delay: 0.58, size: 3.5 },
    { id: "n4", x: -34, y: 12, delay: 0.73, size: 3.9 },
    { id: "n5", x: -8, y: 34, delay: 0.88, size: 3.6 },
    { id: "n6", x: 24, y: 28, delay: 1.03, size: 3.7 },
    { id: "n7", x: 48, y: -30, delay: 1.18, size: 3.4 },
    { id: "n8", x: -48, y: -34, delay: 1.33, size: 3.4 },
];

const EDGES: GraphEdge[] = [
    { id: "e1", from: "core", to: "n1", delay: 0.35 },
    { id: "e2", from: "core", to: "n2", delay: 0.5 },
    { id: "e3", from: "core", to: "n3", delay: 0.65 },
    { id: "e4", from: "core", to: "n4", delay: 0.8 },
    { id: "e5", from: "core", to: "n5", delay: 0.95 },
    { id: "e6", from: "core", to: "n6", delay: 1.1 },
    { id: "e7", from: "n1", to: "n2", delay: 1.25 },
    { id: "e8", from: "n2", to: "n3", delay: 1.4 },
    { id: "e9", from: "n3", to: "n4", delay: 1.55 },
    { id: "e10", from: "n4", to: "n5", delay: 1.7 },
    { id: "e11", from: "n5", to: "n6", delay: 1.85 },
    { id: "e12", from: "n1", to: "n7", delay: 2 },
    { id: "e13", from: "n3", to: "n8", delay: 2.15 },
];

const READY_STATUSES = ["preview_ready", "completed", "ready", "first_slide_ready"];

const STATUS_TEXT_MAP: Record<string, string> = {
    pending: "Understanding your topic...",
    planning: "Structuring concepts...",
    planning_completed: "Structuring concepts...",
    processing: "Connecting ideas...",
    preview_ready: "Building visual explanations...",
    completed: "Building visual explanations...",
};

function normalizeStatus(status?: string): string {
    return (status || "").trim().toLowerCase();
}

function resolveStatusText(status?: string): string | null {
    const normalized = normalizeStatus(status);
    if (!normalized) {
        return null;
    }
    if (STATUS_TEXT_MAP[normalized]) {
        return STATUS_TEXT_MAP[normalized];
    }
    return status || null;
}

function isReadyStatus(status?: string): boolean {
    const normalized = normalizeStatus(status);
    return READY_STATUSES.includes(normalized);
}

export function KnowledgeGraphLoader({ status, onReady, className = "" }: KnowledgeGraphLoaderProps) {
    const [copyIndex, setCopyIndex] = useState(0);
    const [isExiting, setIsExiting] = useState(false);
    const [isVisible, setIsVisible] = useState(true);
    const readyCallbackRef = useRef(false);
    const containerRef = useRef<HTMLDivElement | null>(null);

    const mouseX = useMotionValue(0);
    const mouseY = useMotionValue(0);
    const graphX = useSpring(mouseX, { stiffness: 60, damping: 18, mass: 0.6 });
    const graphY = useSpring(mouseY, { stiffness: 60, damping: 18, mass: 0.6 });

    const displayTextFromStatus = resolveStatusText(status);

    useEffect(() => {
        if (displayTextFromStatus) {
            return;
        }
        const timer = window.setInterval(() => {
            setCopyIndex((prev) => (prev + 1) % COPY_STEPS.length);
        }, 2600);
        return () => window.clearInterval(timer);
    }, [displayTextFromStatus]);

    useEffect(() => {
        if (!isReadyStatus(status) || readyCallbackRef.current) {
            return;
        }
        readyCallbackRef.current = true;
        setIsExiting(true);

        const exitTimer = window.setTimeout(() => {
            setIsVisible(false);
            onReady?.();
        }, 850);

        return () => window.clearTimeout(exitTimer);
    }, [status, onReady]);

    const nodeById = useMemo(() => {
        const entries = NODES.map((node) => [node.id, node] as const);
        return Object.fromEntries(entries);
    }, []);

    const particles = useMemo(
        () =>
            Array.from({ length: 28 }).map((_, index) => ({
                id: `p-${index}`,
                left: 4 + (index * 37) % 92,
                top: 6 + (index * 29) % 88,
                size: index % 4 === 0 ? 2 : 1,
                duration: 14 + (index % 6) * 3,
                driftX: (index % 2 === 0 ? 1 : -1) * (3 + (index % 5)),
                driftY: (index % 3 === 0 ? 1 : -1) * (4 + (index % 4)),
                delay: index * 0.14,
            })),
        []
    );

    const handleMouseMove = (event: React.MouseEvent<HTMLDivElement>) => {
        const element = containerRef.current;
        if (!element) {
            return;
        }
        const rect = element.getBoundingClientRect();
        const px = (event.clientX - rect.left) / rect.width - 0.5;
        const py = (event.clientY - rect.top) / rect.height - 0.5;
        mouseX.set(px * 18);
        mouseY.set(py * 16);
    };

    const handleMouseLeave = () => {
        mouseX.set(0);
        mouseY.set(0);
    };

    const activeCopy = displayTextFromStatus || COPY_STEPS[copyIndex];

    return (
        <AnimatePresence mode="wait">
            {isVisible && (
                <motion.div
                    key="knowledge-loader"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0, filter: "blur(8px)" }}
                    transition={{ duration: 0.9, ease: EASE_OUT }}
                    className={`relative flex min-h-[460px] w-full items-center justify-center overflow-hidden rounded-[28px] border border-slate-500/10 bg-[#020617] ${className}`}
                    ref={containerRef}
                    onMouseMove={handleMouseMove}
                    onMouseLeave={handleMouseLeave}
                >
                    <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_25%,rgba(14,116,144,0.16),transparent_45%),radial-gradient(circle_at_80%_20%,rgba(56,189,248,0.1),transparent_42%),radial-gradient(circle_at_50%_80%,rgba(30,64,175,0.12),transparent_48%)]" />
                    <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(2,6,23,0.25)_0%,rgba(2,6,23,0.92)_100%)]" />
                    <div className="pointer-events-none absolute inset-0 opacity-[0.07] [background-image:radial-gradient(circle_at_1px_1px,rgba(148,163,184,0.5)_1px,transparent_0)] [background-size:22px_22px]" />

                    {particles.map((particle) => (
                        <motion.span
                            key={particle.id}
                            className="pointer-events-none absolute rounded-full bg-cyan-100/35"
                            style={{
                                width: particle.size,
                                height: particle.size,
                                left: `${particle.left}%`,
                                top: `${particle.top}%`,
                            }}
                            animate={{
                                x: [0, particle.driftX, 0],
                                y: [0, -particle.driftY, 0],
                                opacity: [0.15, 0.4, 0.15],
                            }}
                            transition={{
                                duration: particle.duration,
                                delay: particle.delay,
                                repeat: Infinity,
                                ease: CAMERA_EASE,
                            }}
                        />
                    ))}

                    <motion.div
                        className="relative z-10 flex w-full max-w-3xl flex-col items-center justify-center px-6 pb-8 pt-10"
                        animate={{ scale: [1, 1.05, 1] }}
                        transition={{ duration: 10, repeat: Infinity, ease: CAMERA_EASE }}
                    >
                        <motion.div style={{ x: graphX, y: graphY }} className="w-[min(78vw,540px)]">
                            <svg viewBox="-70 -70 140 140" className="h-auto w-full" role="img" aria-label="Knowledge graph loading animation">
                                <defs>
                                    <filter id="edgeGlow" x="-40%" y="-40%" width="180%" height="180%">
                                        <feGaussianBlur stdDeviation="1.4" result="blur" />
                                        <feMerge>
                                            <feMergeNode in="blur" />
                                            <feMergeNode in="SourceGraphic" />
                                        </feMerge>
                                    </filter>
                                    <filter id="nodeGlow" x="-60%" y="-60%" width="220%" height="220%">
                                        <feGaussianBlur stdDeviation="2.1" result="blur" />
                                        <feMerge>
                                            <feMergeNode in="blur" />
                                            <feMergeNode in="SourceGraphic" />
                                        </feMerge>
                                    </filter>
                                </defs>

                                {EDGES.map((edge) => {
                                    const from = nodeById[edge.from];
                                    const to = nodeById[edge.to];
                                    if (!from || !to) {
                                        return null;
                                    }

                                    return (
                                        <g key={edge.id}>
                                            <motion.line
                                                x1={from.x}
                                                y1={from.y}
                                                x2={to.x}
                                                y2={to.y}
                                                stroke="rgba(125,211,252,0.42)"
                                                strokeWidth="0.7"
                                                strokeLinecap="round"
                                                initial={{ pathLength: 0, opacity: 0 }}
                                                animate={{ pathLength: 1, opacity: 0.62 }}
                                                transition={{ duration: 1.3, delay: edge.delay, ease: EASE_OUT }}
                                            />
                                            <motion.line
                                                x1={from.x}
                                                y1={from.y}
                                                x2={to.x}
                                                y2={to.y}
                                                stroke="rgba(56,189,248,0.5)"
                                                strokeWidth="0.38"
                                                strokeLinecap="round"
                                                filter="url(#edgeGlow)"
                                                initial={{ pathLength: 0, opacity: 0 }}
                                                animate={{ pathLength: 1, opacity: [0, 0.55, 0.2] }}
                                                transition={{
                                                    duration: 1.8,
                                                    delay: edge.delay + 0.05,
                                                    ease: EASE_OUT,
                                                    repeat: Infinity,
                                                    repeatDelay: 4.2,
                                                }}
                                            />
                                        </g>
                                    );
                                })}

                                {NODES.map((node) => (
                                    <motion.g
                                        key={node.id}
                                        initial={{ opacity: 0, scale: 0.6 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        transition={{ duration: 0.9, delay: node.delay, ease: EASE_OUT }}
                                    >
                                        <motion.circle
                                            cx={node.x}
                                            cy={node.y}
                                            r={node.size * 1.8}
                                            fill="rgba(56,189,248,0.16)"
                                            filter="url(#nodeGlow)"
                                            initial={{ scale: 0.3, opacity: 0 }}
                                            animate={{ scale: [0.5, 1.5, 2], opacity: [0, 0.34, 0] }}
                                            transition={{ duration: 1.4, delay: node.delay + 0.02, ease: EASE_OUT }}
                                        />
                                        <motion.circle
                                            cx={node.x}
                                            cy={node.y}
                                            r={node.size}
                                            fill="rgba(186,230,253,0.95)"
                                            filter="url(#nodeGlow)"
                                            animate={{
                                                r: [node.size, node.size * 1.08, node.size],
                                                opacity: [0.9, 1, 0.9],
                                            }}
                                            transition={{
                                                duration: 3.8,
                                                delay: node.delay,
                                                repeat: Infinity,
                                                ease: CAMERA_EASE,
                                            }}
                                        />
                                        <motion.circle
                                            cx={node.x}
                                            cy={node.y}
                                            r={Math.max(node.size * 0.42, 1.2)}
                                            fill="rgba(255,255,255,0.98)"
                                            animate={{ opacity: [0.8, 1, 0.8] }}
                                            transition={{
                                                duration: 2.8,
                                                delay: node.delay * 0.7,
                                                repeat: Infinity,
                                                ease: CAMERA_EASE,
                                            }}
                                        />
                                    </motion.g>
                                ))}
                            </svg>
                        </motion.div>

                        <div className="mt-8 flex min-h-7 items-center justify-center">
                            <AnimatePresence mode="wait">
                                <motion.p
                                    key={activeCopy}
                                    initial={{ opacity: 0, y: 6 }}
                                    animate={{ opacity: isExiting ? 0 : 0.84, y: isExiting ? -6 : 0 }}
                                    exit={{ opacity: 0, y: -6 }}
                                    transition={{ duration: 0.72, ease: EASE_OUT }}
                                    className="select-none text-center text-sm font-medium tracking-[0.03em] text-slate-200/90"
                                >
                                    {activeCopy}
                                </motion.p>
                            </AnimatePresence>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
