"use client";

import React, { useState, useRef, useEffect } from "react";
import { BackgroundBeams } from "@/components/ui/background-beams";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Sparkles, BookOpen, Mic2, ChevronDown, Check, Target, Layers } from "lucide-react";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

interface Option {
    value: string;
    label: string;
    subLabel?: string;
}

interface CustomSelectProps {
    label: string;
    icon: React.ElementType;
    value: string;
    options: Option[];
    onChange: (value: string) => void;
}

interface SlidePlan {
    title: string;
    goal: string;
}

interface PlanData {
    topic: string;
    sub_topics: Array<{ id: string; name: string }>;
    plans: Record<string, SlidePlan[]>;
}

interface LessonRenderResult {
    lesson_intro_narration?: unknown;
    slides?: Record<string, Array<{ html_content?: string | null }> | undefined>;
}

function hasRenderableSlides(
    result: LessonRenderResult | null | undefined
): boolean {
    /**
     * Return true only when we have actual renderable content.
     * - Intro narration presence alone is NOT sufficient (just metadata).
     * - We need at least one slide with actual html_content string.
     * The viewer can synthesize intro HTML from topic if needed, but
     * requires real slides for content.
     */
    const slideGroups = Object.values(result?.slides || {});
    return slideGroups.some((slides) =>
        Array.isArray(slides) &&
        slides.some(
            (slide) =>
                typeof slide?.html_content === "string" &&
                slide.html_content.trim().length > 0
        )
    );
}

async function readJsonSafe(response: Response, fallback: any = null) {
    const raw = await response.text();
    if (!raw || !raw.trim()) {
        return fallback;
    }
    try {
        return JSON.parse(raw);
    } catch {
        return fallback;
    }
}

const LessonPlanPreview = ({
    planData,
    onConfirm,
    onCancel,
    isFinalizing,
    planningCompleted,
}: {
    planData: PlanData;
    onConfirm: (data: { topic: string, sub_topics: any[], plans: Record<string, SlidePlan[]> }) => void;
    onCancel: () => void;
    isFinalizing: boolean;
    planningCompleted: boolean;
}) => {
    const [editablePlans, setEditablePlans] = useState(planData?.plans || {});
    const [editableTopic, setEditableTopic] = useState(planData?.topic || "");
    const [editableSubTopics, setEditableSubTopics] = useState(planData?.sub_topics || []);
    const [revealedSlideCounts, setRevealedSlideCounts] = useState<Record<string, number>>({});

    // Ensure state updates if planData changes
    useEffect(() => {
        if (planData) {
            setEditablePlans(planData.plans || {});
            setEditableTopic(planData.topic || "");
            setEditableSubTopics(planData.sub_topics || []);
        }
    }, [planData]);

    useEffect(() => {
        setRevealedSlideCounts((prev) => {
            const next = { ...prev };
            for (const sub of editableSubTopics) {
                const subId = sub.id;
                const total = (editablePlans?.[subId] || []).length;
                if (next[subId] === undefined) {
                    next[subId] = 0;
                }
                if (next[subId] > total) {
                    next[subId] = total;
                }
            }
            return next;
        });
    }, [editablePlans, editableSubTopics]);

    useEffect(() => {
        const hasPendingReveal = editableSubTopics.some((sub) => {
            const total = (editablePlans?.[sub.id] || []).length;
            const shown = revealedSlideCounts[sub.id] ?? 0;
            return shown < total;
        });

        if (!hasPendingReveal) {
            return;
        }

        const timer = setTimeout(() => {
            setRevealedSlideCounts((prev) => {
                const next = { ...prev };
                for (const sub of editableSubTopics) {
                    const subId = sub.id;
                    const total = (editablePlans?.[subId] || []).length;
                    const shown = next[subId] ?? 0;
                    if (shown < total) {
                        next[subId] = shown + 1;
                        break;
                    }
                }
                return next;
            });
        }, 180);

        return () => clearTimeout(timer);
    }, [editablePlans, editableSubTopics, revealedSlideCounts]);

    const updateSlide = (subId: string, slideIdx: number, field: 'title' | 'goal', value: string) => {
        setEditablePlans(prev => {
            const next = { ...prev };
            const subPlans = [...(next[subId] || [])];
            if (subPlans[slideIdx]) {
                subPlans[slideIdx] = { ...subPlans[slideIdx], [field]: value };
            }
            next[subId] = subPlans;
            return next;
        });
    };

    const updateSubTopic = (id: string, name: string) => {
        setEditableSubTopics(prev => prev.map(s => s.id === id ? { ...s, name } : s));
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full bg-gray-900/50 backdrop-blur-xl border border-white/10 rounded-3xl p-8 shadow-2xl relative"
        >
            <div className="flex items-center justify-between mb-8 pb-6 border-b border-white/5 gap-4">
                <div className="flex-1">
                    <input
                        value={editableTopic}
                        onChange={(e) => setEditableTopic(e.target.value)}
                        className="text-2xl font-bold text-white mb-1 bg-transparent focus:outline-none focus:ring-1 focus:ring-indigo-500/50 rounded px-1 w-full"
                        placeholder="Lesson Topic"
                    />
                    <p className="text-gray-400 text-sm">Fine-tune your curriculum before generating content</p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                    <button
                        onClick={onCancel}
                        className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                    >
                        Cancel
                    </button>
                    {planningCompleted ? (
                        <ShimmerButton
                            onClick={() => onConfirm({
                                topic: editableTopic,
                                sub_topics: editableSubTopics,
                                plans: editablePlans
                            })}
                            disabled={isFinalizing}
                            className="h-10 px-6 text-sm"
                        >
                            {isFinalizing ? "Confirming..." : "Confirm & Generate"}
                        </ShimmerButton>
                    ) : (
                        <div className="px-4 py-2 text-xs font-mono uppercase tracking-widest text-indigo-300/70 border border-indigo-400/20 rounded-full bg-indigo-500/10">
                            Building full curriculum...
                        </div>
                    )}
                </div>
            </div>

            <div className="space-y-10 max-h-[60vh] overflow-y-auto pr-4 custom-scrollbar">
                {editableSubTopics.map((sub: any) => (
                    <div key={sub.id} className="space-y-4">
                        {(() => {
                            const allSlides = editablePlans?.[sub.id] || [];
                            const visibleCount = Math.min(revealedSlideCounts[sub.id] ?? 0, allSlides.length);
                            const visibleSlides = allSlides.slice(0, visibleCount);

                            return (
                                <>
                        <div className="flex items-center gap-3 text-indigo-400 font-semibold uppercase text-xs tracking-widest pl-1">
                            <Layers className="w-3.5 h-3.5" />
                            <input
                                value={sub.name}
                                onChange={(e) => updateSubTopic(sub.id, e.target.value)}
                                className="bg-transparent focus:outline-none focus:ring-1 focus:ring-indigo-500/30 rounded px-1 flex-1 py-1"
                                placeholder="Subtopic Name"
                            />
                        </div>
                        <div className="grid gap-3 pl-2 border-l border-white/5">
                            {allSlides.length > 0 ? (
                                <>
                                {visibleSlides.map((slide, idx) => (
                                    <div
                                        key={idx}
                                        className="p-4 rounded-xl bg-black/40 border border-white/5 hover:border-white/10 transition-colors group"
                                    >
                                        <div className="flex gap-4">
                                            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-white/5 flex items-center justify-center text-[10px] text-gray-500 font-mono mt-1">
                                                {idx + 1}
                                            </div>
                                            <div className="flex-1 space-y-3">
                                                <input
                                                    value={slide.title}
                                                    onChange={(e) => updateSlide(sub.id, idx, 'title', e.target.value)}
                                                    className="w-full bg-transparent text-white font-medium focus:outline-none focus:ring-1 focus:ring-indigo-500/50 rounded px-1"
                                                    placeholder="Slide Title"
                                                />
                                                <textarea
                                                    value={slide.goal}
                                                    onChange={(e) => updateSlide(sub.id, idx, 'goal', e.target.value)}
                                                    className="w-full bg-transparent text-gray-400 text-sm h-12 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 rounded px-1 resize-none"
                                                    placeholder="Learning Goal"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                                {visibleCount < allSlides.length && (
                                    <p className="text-[10px] font-mono text-indigo-300/60 uppercase tracking-widest px-1">
                                        Revealing slide titles... {visibleCount}/{allSlides.length}
                                    </p>
                                )}
                                </>
                            ) : (
                                <div className="space-y-4 animate-pulse p-4">
                                    <div className="h-4 bg-white/5 rounded w-3/4 mb-2"></div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="h-24 bg-white/5 rounded-xl"></div>
                                        <div className="h-24 bg-white/5 rounded-xl opacity-50"></div>
                                    </div>
                                    <p className="text-[10px] font-mono text-indigo-400/50 uppercase tracking-widest">Designing slides for this section...</p>
                                </div>
                            )}
                        </div>
                                </>
                            );
                        })()}
                    </div>
                ))}
            </div>
        </motion.div>
    );
};

const CustomSelect = ({ label, icon: Icon, value, options, onChange }: CustomSelectProps) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const selectedOption = options.find((opt) => opt.value === value) || options[0];

    return (
        <div className="space-y-2 relative" ref={containerRef}>
            <label className="block text-sm font-medium text-gray-400 ml-1 flex items-center gap-2">
                <Icon className="w-4 h-4" /> {label}
            </label>
            <div className="relative">
                <button
                    type="button"
                    onClick={() => setIsOpen(!isOpen)}
                    className={cn(
                        "w-full flex items-center justify-between bg-surface-dark/50 border border-white/10 rounded-xl px-4 py-3 text-left text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary/50 hover:bg-white/5 transition-all duration-200",
                        isOpen && "ring-2 ring-primary/50 bg-white/5"
                    )}
                >
                    <div className="flex flex-col truncate">
                        <span className="block font-medium text-sm">{selectedOption.label}</span>
                    </div>
                    <ChevronDown
                        className={cn("w-4 h-4 text-gray-500 transition-transform duration-200 flex-shrink-0 ml-2", isOpen && "transform rotate-180")}
                    />
                </button>

                <AnimatePresence>
                    {isOpen && (
                        <motion.div
                            initial={{ opacity: 0, y: -10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -10, scale: 0.95 }}
                            transition={{ duration: 0.1 }}
                            className="absolute z-50 mt-2 w-full bg-[#13151a] border border-white/10 rounded-xl shadow-2xl overflow-hidden max-h-60 overflow-y-auto custom-scrollbar"
                        >
                            <div className="p-1">
                                {options.map((option) => (
                                    <button
                                        key={option.value}
                                        type="button"
                                        onClick={() => {
                                            onChange(option.value);
                                            setIsOpen(false);
                                        }}
                                        className={cn(
                                            "w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-left text-sm transition-colors duration-150 group",
                                            value === option.value
                                                ? "bg-primary/20 text-primary-300"
                                                : "text-gray-400 hover:bg-white/5 hover:text-white"
                                        )}
                                    >
                                        <div className="flex flex-col">
                                            <span className={cn("font-medium", value === option.value && "text-white")}>
                                                {option.label}
                                            </span>
                                            {option.subLabel && (
                                                <span className="text-[10px] text-gray-500 group-hover:text-gray-400">
                                                    {option.subLabel}
                                                </span>
                                            )}
                                        </div>
                                        {value === option.value && (
                                            <Check className="w-4 h-4 text-primary shrink-0" />
                                        )}
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

const ShimmerButton = ({ children, className, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => {
    return (
        <button
            className={cn(
                "inline-flex h-14 animate-shimmer items-center justify-center rounded-full border border-slate-800 bg-[linear-gradient(110deg,#000103,45%,#1e2631,55%,#000103)] bg-[length:200%_100%] px-8 font-medium text-slate-400 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-50 hover:text-white shadow-lg hover:shadow-primary/20",
                className
            )}
            {...props}
        >
            {children}
        </button>
    );
};

export default function LessonInputPage() {
    const [formData, setFormData] = useState({
        topic: "",
        current_level: "Intermediate",
        learning_goal: "Understand Core Concepts",
        granularity: "Detailed",
        preferred_method: "Socratic",
        teacher_gender: "Female",
    });

    const { data: session, status } = useSession();
    const router = useRouter();

    // UI Phase State
    const [step, setStep] = useState<'form' | 'review' | 'generating'>('form');
    const [taskId, setTaskId] = useState<string | null>(null);
    const [planData, setPlanData] = useState<PlanData | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [generationStatus, setGenerationStatus] = useState<string>("");
    const [planningStatus, setPlanningStatus] = useState<"idle" | "pending" | "planning" | "planning_completed" | "failed">("idle");

    useEffect(() => {
        // Prevents mysterious redirects to home if the dev server reloads/session transiently fails.
        // We only redirect if strictly unauthenticated AND we aren't in the middle of a generation.
        if (status === "unauthenticated" && !isGenerating && step === 'form') {
            router.push("/");
        }
    }, [status, router, isGenerating, step]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSelectChange = (name: string, value: string) => {
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.topic.trim()) {
            setError("Please enter a topic.");
            return;
        }

        setIsGenerating(true);
        setError(null);
        setGenerationStatus("Starting engine...");
        setPlanningStatus("pending");

        try {
            const response = await fetch("/api/lesson/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });

            if (!response.ok) throw new Error("Failed to start planning");
            const data = await readJsonSafe(response, null);
            if (!data?.task_id) {
                throw new Error("Backend did not return a valid task id");
            }
            setTaskId(data.task_id);

            // Start Polling for Planning
            let planningComplete = false;
            while (!planningComplete) {
                await new Promise(r => setTimeout(r, 1500)); // Slightly faster polling
                const res = await fetch(`/api/lesson/generate?taskId=${data.task_id}`);

                if (!res.ok) {
                    const errorData = await readJsonSafe(res).catch(() => ({}));
                    throw new Error(errorData.error || `Server error (${res.status})`);
                }

                const statusData = await readJsonSafe(res, null);
                if (!statusData || typeof statusData !== "object") {
                    setGenerationStatus("Syncing planner state...");
                    continue;
                }
                const nextPlanningStatus = statusData.status === "planning_completed"
                    ? "planning_completed"
                    : statusData.status === "failed"
                        ? "failed"
                        : "planning";
                setPlanningStatus(nextPlanningStatus);

                if (statusData?.result?.unsupported_topic) {
                    const message =
                        statusData?.result?.unsupported_message ||
                        "Math-related slides are currently under working. Please try a non-math topic for now.";
                    setError(message);
                    setIsGenerating(false);
                    setStep("form");
                    setPlanningStatus("failed");
                    planningComplete = true;
                    continue;
                }

                // Proactively update planData if we have results, even if not fully complete
                if (statusData.result && (statusData.result.sub_topics?.length > 0 || Object.keys(statusData.result.plans || {}).length > 0)) {
                    setPlanData(statusData.result);
                    // If we have subtopics, we can show the review step early
                    if (statusData.result.sub_topics?.length > 0) {
                        setStep('review');
                        setIsGenerating(false);
                    }
                }

                if (statusData.status === "planning_completed") {
                    planningComplete = true;
                    setGenerationStatus("Curriculum ready!");
                    setPlanningStatus("planning_completed");
                    setIsGenerating(false);
                } else if (statusData.status === "failed") {
                    throw new Error(statusData.error || "Planning failed");
                } else {
                    setGenerationStatus("Expanding your personal curriculum...");
                }
            }
        } catch (err: any) {
            setError(err.message);
            setIsGenerating(false);
            setPlanningStatus("failed");
        }
    };

    const handleConfirmPlan = async (fullData: {
        topic: string,
        sub_topics: any[],
        plans: Record<string, SlidePlan[]>
    }) => {
        if (!taskId) return;
        if (planningStatus !== "planning_completed") {
            setError("Please wait until planning is fully complete before confirming.");
            return;
        }

        // Guard against stale task IDs that already failed in backend.
        // In that case, users should start a fresh lesson run.
        try {
            const precheck = await fetch(`/api/lesson/generate?taskId=${taskId}`);
            if (precheck.ok) {
                const precheckData = await readJsonSafe(precheck, null);
                if (precheckData.status === "failed") {
                    setError("Previous generation task failed. Please start a new lesson run.");
                    setTaskId(null);
                    setPlanData(null);
                    setPlanningStatus("failed");
                    setStep("form");
                    return;
                }
            }
        } catch {
            // If precheck fails, continue with normal confirm flow.
        }

        setIsGenerating(true);
        setStep('generating');
        setError(null);

        try {
            const response = await fetch(`/api/lesson/generate/${taskId}/confirm`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(fullData),
            });

            if (!response.ok) throw new Error("Failed to confirm plan");

            // Poll for Final Completion (Incremental)
            let pollCount = 0;
            while (true) {
                await new Promise(resolve => setTimeout(resolve, 3000));
                pollCount++;

                if (pollCount > 1) setGenerationStatus("Drafting first segment...");
                if (pollCount > 5) setGenerationStatus("Baking visuals and audio...");

                const res = await fetch(`/api/lesson/generate?taskId=${taskId}`);
                const statusData = await readJsonSafe(res, null);
                if (!statusData || typeof statusData !== "object") {
                    setGenerationStatus("Syncing generation state...");
                    continue;
                }

                if (statusData.status === "completed" || hasRenderableSlides(statusData.result)) {
                    router.push(`/lesson/${taskId}`);
                    break;
                } else if (statusData.status === "failed") {
                    throw new Error(statusData.error || "Generation failed");
                }
            }
        } catch (err: any) {
            setError(err.message);
            setIsGenerating(false);
            setStep('review');
        }
    };

    // Options (keep as is)
    const levelOptions = [
        { value: "Beginner", label: "Beginner", subLabel: "New to the subject" },
        { value: "Intermediate", label: "Intermediate", subLabel: "Some prior knowledge" },
        { value: "Advanced", label: "Advanced", subLabel: "Expert looking for depth" },
    ];
    const goalOptions = [
        { value: "Understand Core Concepts", label: "Understand Core Concepts", subLabel: "Foundational knowledge" },
        { value: "Practical Application", label: "Practical Application", subLabel: "Apply to real problems" },
        { value: "Exam Preparation", label: "Exam Preparation", subLabel: "Focus on key facts" },
    ];
    const granularityOptions = [
        { value: "Overview", label: "Overview", subLabel: "High-level summary" },
        { value: "Detailed", label: "Detailed", subLabel: "Standard curriculum" },
        { value: "Deep Dive", label: "Deep Dive", subLabel: "Comprehensive study" },
    ];
    const methodOptions = [
        { value: "Socratic", label: "Socratic", subLabel: "Learn through questions" },
        { value: "Direct Instruction", label: "Direct Instruction", subLabel: "Clear explanations" },
        { value: "Storytelling", label: "Storytelling", subLabel: "Learn through analogies" },
    ];

    if (status === "loading") {
        return (
            <div className="min-h-screen w-full bg-[#0a0f1a] flex items-center justify-center">
                <BackgroundBeams className="opacity-40" />
                <div className="text-indigo-400 animate-pulse font-mono tracking-widest uppercase text-sm">Initializing...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen w-full bg-[#0a0f1a] relative flex flex-col items-center justify-center antialiased overflow-hidden py-12">
            <BackgroundBeams className="opacity-20" />

            <div className="z-10 w-full max-w-4xl px-4 sm:px-6">
                {step === 'form' && (
                    <>
                        <div className="mb-12">
                            <Link href="/" className="inline-flex items-center text-sm text-gray-500 hover:text-white transition-colors mb-8 group">
                                <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" /> Back to Home
                            </Link>
                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center">
                                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold mb-6">
                                    <Sparkles className="w-3 h-3" />
                                    <span>AI Curriculum Engine</span>
                                </div>
                                <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
                                    Unlock Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Potential</span>
                                </h1>
                                <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                                    Your AI tutor will craft a personalized learning experience tailored to your specific needs and goals.
                                </p>
                            </motion.div>
                        </div>

                        <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="bg-gray-900/40 backdrop-blur-3xl border border-white/5 rounded-3xl p-8 shadow-2xl relative">
                            <form onSubmit={handleSubmit} className="space-y-8">
                                <div className="space-y-6">
                                    <div className="space-y-3">
                                        <label className="text-xs font-semibold text-indigo-400/80 uppercase tracking-widest ml-1">Learning Subject</label>
                                        <input
                                            type="text"
                                            name="topic"
                                            value={formData.topic}
                                            onChange={handleInputChange}
                                            placeholder="What would you like to master today?"
                                            className="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-5 text-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all font-medium"
                                        />
                                    </div>
                                    <div className="grid md:grid-cols-2 gap-6">
                                        <CustomSelect label="Current Knowledge" icon={Layers} value={formData.current_level} options={levelOptions} onChange={(v) => handleSelectChange("current_level", v)} />
                                        <CustomSelect label="Your Goal" icon={Target} value={formData.learning_goal} options={goalOptions} onChange={(v) => handleSelectChange("learning_goal", v)} />
                                    </div>
                                    <div className="grid md:grid-cols-2 gap-6">
                                        <CustomSelect label="Mental Model" icon={Mic2} value={formData.preferred_method} options={methodOptions} onChange={(v) => handleSelectChange("preferred_method", v)} />
                                        <CustomSelect label="Curriculum Depth" icon={BookOpen} value={formData.granularity} options={granularityOptions} onChange={(v) => handleSelectChange("granularity", v)} />
                                    </div>
                                </div>

                                {error && <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-100 text-sm text-center">{error}</div>}

                                <div className="pt-4 flex flex-col items-center gap-4">
                                    <ShimmerButton type="submit" className={cn("w-full md:w-auto min-w-[240px]", isGenerating && "opacity-50 pointer-events-none")}>
                                        {isGenerating ? "Preparing Deck..." : "Generate Lesson Design"}
                                    </ShimmerButton>
                                    {isGenerating && <p className="text-indigo-400/60 text-xs font-mono animate-pulse">{generationStatus}</p>}
                                </div>
                            </form>
                        </motion.div>
                    </>
                )}

                {step === 'review' && planData && (
                    <LessonPlanPreview
                        planData={planData}
                        onConfirm={handleConfirmPlan}
                        onCancel={() => setStep('form')}
                        isFinalizing={isGenerating}
                        planningCompleted={planningStatus === "planning_completed"}
                    />
                )}

                {step === 'generating' && (
                    <div className="flex flex-col items-center justify-center space-y-8 py-20">
                        <div className="relative">
                            <div className="w-24 h-24 border-4 border-indigo-500/10 border-t-indigo-500 rounded-full animate-spin" />
                            <div className="absolute inset-0 flex items-center justify-center">
                                <Sparkles className="w-8 h-8 text-indigo-400 animate-pulse" />
                            </div>
                        </div>
                        <div className="text-center space-y-3">
                            <h2 className="text-2xl font-bold text-white">Full Generation in Progress</h2>
                            <p className="text-indigo-400 font-mono text-sm animate-pulse tracking-wide">{generationStatus}</p>
                            <p className="text-gray-500 text-xs max-w-xs mx-auto">This may take a minute as we synthesize narrations and build custom visuals.</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
