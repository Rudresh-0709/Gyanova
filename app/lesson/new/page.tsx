"use client";

import React, { useState, useRef, useEffect } from "react";
import { BackgroundBeams } from "@/components/ui/background-beams";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, Sparkles, BookOpen, GraduationCap, Mic2, ChevronDown, Check, Target, Layers } from "lucide-react";
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
        teacher_gender: "Female", // Default, hidden for now
    });

    const { data: session, status } = useSession();
    const router = useRouter();
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [generationStatus, setGenerationStatus] = useState<string>("");


    useEffect(() => {
        if (status === "unauthenticated") {
            router.push("/");
        }
    }, [status, router]);

    if (status === "loading") {
        return (
            <div className="min-h-screen w-full bg-background-light dark:bg-background-dark flex items-center justify-center">
                <BackgroundBeams className="opacity-40" />
                <div className="text-white animate-pulse">Loading session...</div>
            </div>
        );
    }

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

        try {
            console.log("Generating lesson for:", formData);
            const response = await fetch("/api/lesson/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(formData),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Failed to start lesson generation");
            }

            const data = await response.json();
            console.log("Generation started, Task ID:", data.task_id);
            setGenerationStatus("Starting engine...");

            // Poll for completion
            let isComplete = false;
            let pollCount = 0;
            while (!isComplete) {
                await new Promise(resolve => setTimeout(resolve, 5000)); // wait 5 seconds before each poll
                pollCount++;
                if (pollCount > 1) setGenerationStatus("Drafting curriculum...");
                if (pollCount > 4) setGenerationStatus("Writing slide content...");
                if (pollCount > 10) setGenerationStatus("Synthesizing audio narrations...");
                if (pollCount > 20) setGenerationStatus("Rendering final output...");
                if (pollCount > 40) setGenerationStatus("Almost done...");

                const statusResponse = await fetch(`/api/lesson/generate?taskId=${data.task_id}`);

                if (!statusResponse.ok) {
                    throw new Error("Failed to check generation status");
                }

                const statusData = await statusResponse.json();
                console.log("Generation status:", statusData.status);

                if (statusData.status === "completed") {
                    isComplete = true;
                    console.log("Generation successful:", statusData.result);
                    // Navigate to lesson viewing page with generated taskId
                    router.push(`/lesson/${data.task_id}`);
                } else if (statusData.status === "failed") {
                    throw new Error(statusData.error || "Generation failed on the backend");
                }
                // If status is "pending" or "processing", the loop continues
            }

        } catch (err: any) {
            console.error("Generation error:", err);
            setError(err.message || "An unexpected error occurred.");
        } finally {
            setIsGenerating(false);
            setGenerationStatus("");
        }
    };

    const levelOptions = [
        { value: "Beginner", label: "Beginner", subLabel: "New to the subject" },
        { value: "Intermediate", label: "Intermediate", subLabel: "Some prior knowledge" },
        { value: "Advanced", label: "Advanced", subLabel: "Expert looking for depth" },
        { value: "Expert", label: "Expert", subLabel: "Deep technical dive" },
    ];

    const goalOptions = [
        { value: "Understand Core Concepts", label: "Understand Core Concepts", subLabel: "Foundational knowledge" },
        { value: "Practical Application", label: "Practical Application", subLabel: "Apply to real problems" },
        { value: "Exam Preparation", label: "Exam Preparation", subLabel: "Focus on key facts" },
        { value: "Problem Solving", label: "Problem Solving", subLabel: "Learn by doing" },
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

    return (
        <div className="min-h-screen w-full bg-background-light dark:bg-background-dark relative flex flex-col items-center justify-center antialiased overflow-hidden">
            <BackgroundBeams className="opacity-40" />

            <div className="z-10 w-full max-w-4xl px-4 sm:px-6">
                <div className="mb-8">
                    <Link href="/" className="inline-flex items-center text-sm text-gray-500 hover:text-white transition-colors mb-6 group">
                        <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" /> Back to Home
                    </Link>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5 }}
                        className="text-center"
                    >
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold mb-4">
                            <Sparkles className="w-3 h-3" />
                            <span>New Session</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-bold font-display text-white mb-4 bg-clip-text text-transparent bg-gradient-to-b from-neutral-50 to-neutral-400">
                            What do you want to learn today?
                        </h1>
                        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                            Your personal tutor will structure a lesson specifically for you.
                        </p>
                    </motion.div>
                </div>

                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                    className="w-full bg-gray-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl relative overflow-visible group"
                >
                    <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none" />
                    <div className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none" />

                    <form onSubmit={handleSubmit} className="space-y-8 relative z-10">
                        {/* Section 1: What You Want to Learn */}
                        <div className="space-y-4">
                            <h3 className="text-sm uppercase tracking-wider text-gray-500 font-semibold border-b border-white/5 pb-2">
                                1. What You Want to Learn
                            </h3>
                            <div className="space-y-2">
                                <label htmlFor="topic" className="block text-sm font-medium text-gray-300 ml-1">
                                    Topic / Subject
                                </label>
                                <div className="relative group/input">
                                    <input
                                        type="text"
                                        id="topic"
                                        name="topic"
                                        value={formData.topic}
                                        onChange={handleInputChange}
                                        placeholder="e.g. Quantum Mechanics, The French Revolution, How do LLMs work?"
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-6 py-4 text-xl text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-transparent transition-all shadow-inner"
                                        autoFocus
                                    />
                                    <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary/20 to-secondary/20 opacity-0 group-hover/input:opacity-100 -z-10 blur-md transition-opacity duration-300" />
                                </div>
                            </div>
                        </div>

                        {/* Section 2: Your Learning Context */}
                        <div className="space-y-4">
                            <h3 className="text-sm uppercase tracking-wider text-gray-500 font-semibold border-b border-white/5 pb-2">
                                2. Your Learning Context
                            </h3>
                            <div className="grid md:grid-cols-2 gap-6">
                                <CustomSelect
                                    label="Current Level"
                                    icon={Layers}
                                    value={formData.current_level}
                                    options={levelOptions}
                                    onChange={(value) => handleSelectChange("current_level", value)}
                                />
                                <CustomSelect
                                    label="Learning Goal"
                                    icon={Target}
                                    value={formData.learning_goal}
                                    options={goalOptions}
                                    onChange={(value) => handleSelectChange("learning_goal", value)}
                                />
                            </div>
                        </div>

                        {/* Section 3: How You Want It Taught */}
                        <div className="space-y-4">
                            <h3 className="text-sm uppercase tracking-wider text-gray-500 font-semibold border-b border-white/5 pb-2">
                                3. How You Want It Taught
                            </h3>
                            <div className="grid md:grid-cols-2 gap-6">
                                <CustomSelect
                                    label="Teaching Style"
                                    icon={Mic2}
                                    value={formData.preferred_method}
                                    options={methodOptions}
                                    onChange={(value) => handleSelectChange("preferred_method", value)}
                                />
                                <CustomSelect
                                    label="Lesson Depth"
                                    icon={BookOpen}
                                    value={formData.granularity}
                                    options={granularityOptions}
                                    onChange={(value) => handleSelectChange("granularity", value)}
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
                                {error}
                            </div>
                        )}

                        <div className="pt-8 flex justify-center">
                            <ShimmerButton
                                type="submit"
                                className={cn("w-full md:w-auto px-8 text-lg", isGenerating && "opacity-50 cursor-not-allowed")}
                                disabled={isGenerating}
                            >
                                {isGenerating ? (
                                    <span className="flex items-center gap-2">
                                        <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                                        {generationStatus || "Generating..."}
                                    </span>
                                ) : (
                                    "Generate Lesson Plan"
                                )}
                            </ShimmerButton>
                        </div>
                    </form>
                </motion.div>
            </div>
        </div>
    );
}
