"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
    X,
    ChevronRight,
    BookOpen,
    Eye,
    Loader2,
    Trophy,
    CheckCircle2,
    XCircle,
    RotateCcw,
    Sparkles,
} from "lucide-react";

// ─── Types ──────────────────────────────────────────────────────────────

interface QuizQuestion {
    id: string;
    question: string;
    options: string[];
    correct_index: number;
    explanation: string;
    related_slide_id: string;
    related_concept: string;
}

interface AnswerState {
    selectedIndex: number | null;
    isCorrect: boolean | null;
    explanationViewed: boolean;
    slideReviewed: boolean;
    attempts: number;
}

interface QuizWizardProps {
    isOpen: boolean;
    onClose: () => void;
    taskId: string;
    subtopicId: string;
    subtopicName: string;
    onNavigateToSlide: (slideId: string) => void;
    prefetchedData?: any;
}

type QuizPhase = "loading" | "question" | "feedback" | "completed";

// ─── Component ──────────────────────────────────────────────────────────

export function QuizWizard({
    isOpen,
    onClose,
    taskId,
    subtopicId,
    subtopicName,
    onNavigateToSlide,
    prefetchedData,
}: QuizWizardProps) {
    // Quiz data
    const [questions, setQuestions] = useState<QuizQuestion[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [phase, setPhase] = useState<QuizPhase>("loading");
    const [error, setError] = useState<string | null>(null);

    // Per-question answer tracking
    const [answers, setAnswers] = useState<Record<string, AnswerState>>({});
    const [selectedOption, setSelectedOption] = useState<number | null>(null);

    // Score
    const [score, setScore] = useState(0);

    // Slide review state
    const [isReviewingSlide, setIsReviewingSlide] = useState(false);

    // Animation
    const [isTransitioning, setIsTransitioning] = useState(false);
    const cardRef = useRef<HTMLDivElement>(null);

    // ─── Fetch quiz data ──────────────────────────────────────────────
    useEffect(() => {
        if (!isOpen || !taskId || !subtopicId) return;

        let cancelled = false;

        const loadQuiz = async () => {
            setPhase("loading");
            setError(null);
            setCurrentIndex(0);
            setAnswers({});
            setScore(0);
            setSelectedOption(null);

            if (prefetchedData && prefetchedData.questions?.length > 0) {
                setQuestions(prefetchedData.questions);
                setPhase("question");
                return;
            }

            try {
                const res = await fetch("/api/quiz", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        task_id: taskId,
                        subtopic_id: subtopicId,
                    }),
                });

                if (!res.ok) {
                    const err = await res.json().catch(() => ({}));
                    throw new Error(
                        err.error || "Failed to generate quiz"
                    );
                }

                const data = await res.json();

                if (cancelled) return;

                if (!data.questions || data.questions.length === 0) {
                    throw new Error("No questions generated");
                }

                setQuestions(data.questions);
                setPhase("question");
            } catch (err: any) {
                if (!cancelled) {
                    setError(
                        err.message || "Failed to generate quiz. Please try again."
                    );
                    setPhase("loading");
                }
            }
        };

        loadQuiz();
        return () => {
            cancelled = true;
        };
    }, [isOpen, taskId, subtopicId, prefetchedData]);

    // ─── Current question helpers ─────────────────────────────────────
    const currentQuestion = questions[currentIndex];
    const currentAnswer = currentQuestion
        ? answers[currentQuestion.id]
        : undefined;
    const totalQuestions = questions.length;

    // ─── Handle option selection ──────────────────────────────────────
    const handleSelectOption = useCallback(
        (optionIndex: number) => {
            if (!currentQuestion || phase !== "question") return;
            // Don't allow re-selection if already answered correctly
            if (currentAnswer?.isCorrect) return;

            setSelectedOption(optionIndex);

            const isCorrect = optionIndex === currentQuestion.correct_index;

            setAnswers((prev) => {
                const existing = prev[currentQuestion.id] || {
                    selectedIndex: null,
                    isCorrect: null,
                    explanationViewed: false,
                    slideReviewed: false,
                    attempts: 0,
                };

                return {
                    ...prev,
                    [currentQuestion.id]: {
                        ...existing,
                        selectedIndex: optionIndex,
                        isCorrect,
                        attempts: existing.attempts + 1,
                    },
                };
            });

            if (isCorrect) {
                setScore((s) => s + 1);
            }

            // Transition to feedback after a brief moment
            setTimeout(() => setPhase("feedback"), 300);
        },
        [currentQuestion, currentAnswer, phase]
    );

    // ─── Reveal answer ───────────────────────────────────────────────
    const handleRevealAnswer = useCallback(() => {
        if (!currentQuestion) return;

        setAnswers((prev) => ({
            ...prev,
            [currentQuestion.id]: {
                ...(prev[currentQuestion.id] || {
                    selectedIndex: null,
                    isCorrect: false,
                    slideReviewed: false,
                    attempts: 1,
                }),
                explanationViewed: true,
            },
        }));
    }, [currentQuestion]);

    // ─── Review slide ────────────────────────────────────────────────
    const handleReviewSlide = useCallback(() => {
        if (!currentQuestion) return;

        setAnswers((prev) => ({
            ...prev,
            [currentQuestion.id]: {
                ...(prev[currentQuestion.id] || {
                    selectedIndex: null,
                    isCorrect: false,
                    explanationViewed: false,
                    attempts: 1,
                }),
                slideReviewed: true,
            },
        }));

        setIsReviewingSlide(true);
        onNavigateToSlide(currentQuestion.related_slide_id);
    }, [currentQuestion, onNavigateToSlide]);

    // ─── Return from slide review ────────────────────────────────────
    const handleReturnFromReview = useCallback(() => {
        setIsReviewingSlide(false);
    }, []);

    // ─── Go to next question ─────────────────────────────────────────
    const handleNext = useCallback(() => {
        if (currentIndex >= totalQuestions - 1) {
            setPhase("completed");
            return;
        }

        setIsTransitioning(true);
        setTimeout(() => {
            setCurrentIndex((i) => i + 1);
            setSelectedOption(null);
            setPhase("question");
            setIsTransitioning(false);
        }, 250);
    }, [currentIndex, totalQuestions]);

    // ─── Retry current question ──────────────────────────────────────
    const handleRetry = useCallback(() => {
        setSelectedOption(null);
        setPhase("question");
    }, []);

    // ─── Keyboard handling ───────────────────────────────────────────
    useEffect(() => {
        if (!isOpen) return;

        const onKey = (e: KeyboardEvent) => {
            e.stopPropagation();

            if (e.key === "Escape") {
                if (isReviewingSlide) {
                    handleReturnFromReview();
                }
                // Don't close quiz on escape — keep it deliberate
            }
        };

        window.addEventListener("keydown", onKey, true);
        return () => window.removeEventListener("keydown", onKey, true);
    }, [isOpen, isReviewingSlide, handleReturnFromReview]);

    // ─── Don't render if closed ──────────────────────────────────────
    if (!isOpen) return null;

    // ─── Return-to-quiz floating button (shown when reviewing a slide)
    if (isReviewingSlide) {
        return (
            <div
                className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[60]"
                style={{ animation: "slideUp 0.3s ease-out" }}
            >
                <button
                    onClick={handleReturnFromReview}
                    className="flex items-center gap-2.5 px-6 py-3 rounded-2xl text-white font-semibold text-sm shadow-2xl transition-all hover:scale-105 active:scale-95"
                    style={{
                        background: "linear-gradient(135deg, #6366f1, #7c3aed)",
                        boxShadow:
                            "0 8px 32px rgba(99, 102, 241, 0.4), 0 0 0 1px rgba(255,255,255,0.1)",
                    }}
                >
                    <RotateCcw className="w-4 h-4" />
                    Return to Quiz
                </button>
            </div>
        );
    }

    // ─── Progress percentage ─────────────────────────────────────────
    const progressPct =
        totalQuestions > 0
            ? ((currentIndex + (phase === "completed" ? 1 : 0)) /
                  totalQuestions) *
              100
            : 0;

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 z-[55]"
                style={{
                    background: "rgba(11, 15, 30, 0.95)",
                    backdropFilter: "blur(16px)",
                    WebkitBackdropFilter: "blur(16px)",
                }}
                onClick={(e) => e.stopPropagation()}
                onKeyDown={(e) => e.stopPropagation()}
            />

            {/* Quiz Container */}
            <div
                className="fixed inset-0 z-[56] flex flex-col items-center p-4 md:p-12 overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
                onKeyDown={(e) => e.stopPropagation()}
            >
                <div
                    ref={cardRef}
                    className="w-full max-w-[800px] flex flex-col flex-1"
                    style={{
                        animation: "quizFadeIn 0.4s ease-out",
                    }}
                >
                    {/* ─── Header ─────────────────────────────── */}
                    <div
                        className="shrink-0 pb-6 mb-6"
                        style={{
                            borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                        }}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                                <div
                                    className="w-10 h-10 rounded-xl flex items-center justify-center"
                                    style={{
                                        background:
                                            "linear-gradient(135deg, #6366f1, #8b5cf6)",
                                    }}
                                >
                                    <Sparkles className="w-5 h-5 text-white" />
                                </div>
                                <div>
                                    <p className="text-sm font-semibold text-white/90 leading-tight">
                                        Knowledge Check
                                    </p>
                                    <p className="text-[11px] text-white/40 leading-tight">
                                        {subtopicName.length > 40
                                            ? subtopicName.slice(0, 40) + "…"
                                            : subtopicName}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={onClose}
                                className="p-1.5 rounded-lg hover:bg-white/10 transition-colors text-white/40 hover:text-white/70"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        {/* Progress bar */}
                        {phase !== "loading" && (
                            <div className="flex items-center gap-3">
                                <div className="flex-1 h-1.5 rounded-full bg-white/8 overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all duration-500 ease-out"
                                        style={{
                                            width: `${progressPct}%`,
                                            background:
                                                "linear-gradient(90deg, #6366f1, #8b5cf6)",
                                        }}
                                    />
                                </div>
                                <span className="text-xs text-white/40 font-mono shrink-0">
                                    {phase === "completed"
                                        ? `${totalQuestions}/${totalQuestions}`
                                        : `${currentIndex + 1}/${totalQuestions}`}
                                </span>
                            </div>
                        )}
                    </div>

                    {/* ─── Body ───────────────────────────────── */}
                    <div
                        className="flex-1 overflow-y-auto px-6 py-5"
                        style={{
                            opacity: isTransitioning ? 0 : 1,
                            transform: isTransitioning
                                ? "translateX(20px)"
                                : "translateX(0)",
                            transition:
                                "opacity 0.25s ease, transform 0.25s ease",
                        }}
                    >
                        {/* Loading State */}
                        {phase === "loading" && !error && (
                            <div className="flex flex-col items-center justify-center h-full gap-4 py-16">
                                <div className="relative">
                                    <div
                                        className="w-14 h-14 rounded-2xl flex items-center justify-center"
                                        style={{
                                            background:
                                                "rgba(99, 102, 241, 0.12)",
                                        }}
                                    >
                                        <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
                                    </div>
                                </div>
                                <div className="text-center">
                                    <p className="text-sm text-white/70 font-medium">
                                        Generating your quiz…
                                    </p>
                                    <p className="text-xs text-white/35 mt-1">
                                        Analyzing what you&apos;ve learned
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Error State */}
                        {error && (
                            <div className="flex flex-col items-center justify-center h-full gap-4 py-16">
                                <div
                                    className="w-14 h-14 rounded-2xl flex items-center justify-center"
                                    style={{
                                        background: "rgba(239, 68, 68, 0.12)",
                                    }}
                                >
                                    <XCircle className="w-6 h-6 text-red-400" />
                                </div>
                                <div className="text-center">
                                    <p className="text-sm text-white/70 font-medium">
                                        {error}
                                    </p>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="px-5 py-2 rounded-xl text-sm font-medium text-white/80 hover:text-white transition-colors"
                                    style={{
                                        background: "rgba(255, 255, 255, 0.08)",
                                        border: "1px solid rgba(255, 255, 255, 0.1)",
                                    }}
                                >
                                    Skip Quiz
                                </button>
                            </div>
                        )}

                        {/* Question Phase */}
                        {phase === "question" && currentQuestion && (
                            <div>
                                {/* Concept tag */}
                                <div className="mb-4">
                                    <span
                                        className="inline-block px-3 py-1 rounded-full text-[11px] font-medium uppercase tracking-wider"
                                        style={{
                                            background:
                                                "rgba(99, 102, 241, 0.12)",
                                            color: "rgba(129, 140, 248, 0.9)",
                                        }}
                                    >
                                        {currentQuestion.related_concept}
                                    </span>
                                </div>

                                {/* Question text */}
                                <h2 className="text-lg font-semibold text-white/90 leading-relaxed mb-6">
                                    {currentQuestion.question}
                                </h2>

                                {/* Options */}
                                <div className="space-y-3">
                                    {currentQuestion.options.map(
                                        (option, idx) => {
                                            const letter = String.fromCharCode(
                                                65 + idx
                                            );
                                            const isSelected =
                                                selectedOption === idx;

                                            return (
                                                <button
                                                    key={idx}
                                                    onClick={() =>
                                                        handleSelectOption(idx)
                                                    }
                                                    className="w-full text-left px-4 py-3.5 rounded-xl transition-all duration-200 flex items-start gap-3 group"
                                                    style={{
                                                        background: isSelected
                                                            ? "rgba(99, 102, 241, 0.15)"
                                                            : "rgba(255, 255, 255, 0.04)",
                                                        border: isSelected
                                                            ? "1px solid rgba(99, 102, 241, 0.4)"
                                                            : "1px solid rgba(255, 255, 255, 0.06)",
                                                    }}
                                                >
                                                    <span
                                                        className="shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold mt-0.5 transition-all"
                                                        style={{
                                                            background:
                                                                isSelected
                                                                    ? "linear-gradient(135deg, #6366f1, #7c3aed)"
                                                                    : "rgba(255, 255, 255, 0.08)",
                                                            color: isSelected
                                                                ? "white"
                                                                : "rgba(255, 255, 255, 0.5)",
                                                        }}
                                                    >
                                                        {letter}
                                                    </span>
                                                    <span className="text-sm text-white/80 leading-relaxed pt-0.5 group-hover:text-white/95 transition-colors">
                                                        {option}
                                                    </span>
                                                </button>
                                            );
                                        }
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Feedback Phase */}
                        {phase === "feedback" && currentQuestion && (
                            <div>
                                {/* Result banner */}
                                {currentAnswer?.isCorrect ? (
                                    /* ── Correct ── */
                                    <div
                                        className="flex items-center gap-3 px-4 py-3.5 rounded-xl mb-5"
                                        style={{
                                            background:
                                                "rgba(34, 197, 94, 0.1)",
                                            border: "1px solid rgba(34, 197, 94, 0.2)",
                                        }}
                                    >
                                        <CheckCircle2 className="w-5 h-5 text-green-400 shrink-0" />
                                        <span className="text-sm font-medium text-green-300">
                                            Nice, that&apos;s correct!
                                        </span>
                                    </div>
                                ) : (
                                    /* ── Incorrect ── */
                                    <div
                                        className="flex items-center gap-3 px-4 py-3.5 rounded-xl mb-5"
                                        style={{
                                            background:
                                                "rgba(245, 158, 11, 0.1)",
                                            border: "1px solid rgba(245, 158, 11, 0.2)",
                                        }}
                                    >
                                        <XCircle className="w-5 h-5 text-amber-400 shrink-0" />
                                        <span className="text-sm font-medium text-amber-300">
                                            Not quite — let&apos;s review this
                                        </span>
                                    </div>
                                )}

                                {/* Question + selected answer display */}
                                <div className="mb-5">
                                    <p className="text-sm text-white/50 mb-2">
                                        {currentQuestion.question}
                                    </p>
                                    <div className="space-y-2">
                                        {currentQuestion.options.map(
                                            (option, idx) => {
                                                const letter =
                                                    String.fromCharCode(
                                                        65 + idx
                                                    );
                                                const isCorrectOption =
                                                    idx ===
                                                    currentQuestion.correct_index;
                                                const wasSelected =
                                                    idx ===
                                                    currentAnswer?.selectedIndex;
                                                const showCorrect =
                                                    currentAnswer?.isCorrect ||
                                                    currentAnswer?.explanationViewed;

                                                let bg =
                                                    "rgba(255, 255, 255, 0.03)";
                                                let border =
                                                    "1px solid rgba(255, 255, 255, 0.04)";
                                                let textColor =
                                                    "rgba(255, 255, 255, 0.4)";
                                                let letterBg =
                                                    "rgba(255, 255, 255, 0.06)";
                                                let letterColor =
                                                    "rgba(255, 255, 255, 0.3)";

                                                if (
                                                    isCorrectOption &&
                                                    showCorrect
                                                ) {
                                                    bg =
                                                        "rgba(34, 197, 94, 0.08)";
                                                    border =
                                                        "1px solid rgba(34, 197, 94, 0.25)";
                                                    textColor =
                                                        "rgba(134, 239, 172, 0.9)";
                                                    letterBg =
                                                        "linear-gradient(135deg, #22c55e, #16a34a)";
                                                    letterColor = "white";
                                                } else if (
                                                    wasSelected &&
                                                    !currentAnswer?.isCorrect
                                                ) {
                                                    bg =
                                                        "rgba(239, 68, 68, 0.06)";
                                                    border =
                                                        "1px solid rgba(239, 68, 68, 0.15)";
                                                    textColor =
                                                        "rgba(252, 165, 165, 0.8)";
                                                    letterBg =
                                                        "rgba(239, 68, 68, 0.2)";
                                                    letterColor =
                                                        "rgba(252, 165, 165, 0.8)";
                                                }

                                                return (
                                                    <div
                                                        key={idx}
                                                        className="flex items-start gap-3 px-3.5 py-2.5 rounded-lg"
                                                        style={{
                                                            background: bg,
                                                            border,
                                                        }}
                                                    >
                                                        <span
                                                            className="shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-bold"
                                                            style={{
                                                                background:
                                                                    letterBg,
                                                                color: letterColor,
                                                            }}
                                                        >
                                                            {letter}
                                                        </span>
                                                        <span
                                                            className="text-sm leading-relaxed"
                                                            style={{
                                                                color: textColor,
                                                            }}
                                                        >
                                                            {option}
                                                        </span>
                                                    </div>
                                                );
                                            }
                                        )}
                                    </div>
                                </div>

                                {/* Action buttons (incorrect path) */}
                                {!currentAnswer?.isCorrect &&
                                    !currentAnswer?.explanationViewed && (
                                        <div className="flex gap-3">
                                            <button
                                                onClick={handleRevealAnswer}
                                                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all hover:scale-[1.02] active:scale-[0.98]"
                                                style={{
                                                    background:
                                                        "rgba(99, 102, 241, 0.12)",
                                                    border: "1px solid rgba(99, 102, 241, 0.25)",
                                                    color: "rgba(165, 180, 252, 0.95)",
                                                }}
                                            >
                                                <Eye className="w-4 h-4" />
                                                Reveal Answer
                                            </button>
                                            <button
                                                onClick={handleReviewSlide}
                                                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all hover:scale-[1.02] active:scale-[0.98]"
                                                style={{
                                                    background:
                                                        "rgba(255, 255, 255, 0.06)",
                                                    border: "1px solid rgba(255, 255, 255, 0.1)",
                                                    color: "rgba(255, 255, 255, 0.75)",
                                                }}
                                            >
                                                <BookOpen className="w-4 h-4" />
                                                Review Slide
                                            </button>
                                        </div>
                                    )}

                                {/* Explanation (shown after reveal) */}
                                {currentAnswer?.explanationViewed && (
                                    <div
                                        className="px-4 py-3.5 rounded-xl mb-4"
                                        style={{
                                            background:
                                                "rgba(99, 102, 241, 0.06)",
                                            border: "1px solid rgba(99, 102, 241, 0.12)",
                                            animation:
                                                "quizFadeIn 0.3s ease-out",
                                        }}
                                    >
                                        <p className="text-xs text-indigo-300/60 font-medium uppercase tracking-wider mb-1.5">
                                            Explanation
                                        </p>
                                        <p className="text-sm text-white/70 leading-relaxed">
                                            {currentQuestion.explanation}
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Completed Phase */}
                        {phase === "completed" && (
                            <div className="flex flex-col items-center justify-center py-8 gap-6">
                                {/* Score ring */}
                                <div className="relative w-28 h-28">
                                    <svg
                                        className="w-full h-full -rotate-90"
                                        viewBox="0 0 100 100"
                                    >
                                        <circle
                                            cx="50"
                                            cy="50"
                                            r="42"
                                            fill="none"
                                            stroke="rgba(255,255,255,0.06)"
                                            strokeWidth="6"
                                        />
                                        <circle
                                            cx="50"
                                            cy="50"
                                            r="42"
                                            fill="none"
                                            stroke="url(#scoreGradient)"
                                            strokeWidth="6"
                                            strokeLinecap="round"
                                            strokeDasharray={`${
                                                (score / totalQuestions) *
                                                264
                                            } 264`}
                                            style={{
                                                transition:
                                                    "stroke-dasharray 1s ease-out",
                                            }}
                                        />
                                        <defs>
                                            <linearGradient
                                                id="scoreGradient"
                                                x1="0%"
                                                y1="0%"
                                                x2="100%"
                                                y2="0%"
                                            >
                                                <stop
                                                    offset="0%"
                                                    stopColor="#6366f1"
                                                />
                                                <stop
                                                    offset="100%"
                                                    stopColor="#8b5cf6"
                                                />
                                            </linearGradient>
                                        </defs>
                                    </svg>
                                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                                        <span className="text-2xl font-bold text-white">
                                            {score}
                                        </span>
                                        <span className="text-xs text-white/40">
                                            of {totalQuestions}
                                        </span>
                                    </div>
                                </div>

                                {/* Result message */}
                                <div className="text-center">
                                    {score === totalQuestions ? (
                                        <>
                                            <div className="flex items-center justify-center gap-2 mb-2">
                                                <Trophy className="w-5 h-5 text-yellow-400" />
                                                <h3 className="text-xl font-bold text-white">
                                                    Perfect!
                                                </h3>
                                            </div>
                                            <p className="text-sm text-white/50">
                                                You nailed every question. 🎉
                                            </p>
                                        </>
                                    ) : score >=
                                      Math.ceil(totalQuestions * 0.6) ? (
                                        <>
                                            <h3 className="text-xl font-bold text-white mb-1">
                                                Great job! 👏
                                            </h3>
                                            <p className="text-sm text-white/50">
                                                You have a solid understanding
                                                of this topic.
                                            </p>
                                        </>
                                    ) : (
                                        <>
                                            <h3 className="text-xl font-bold text-white mb-1">
                                                Keep practicing! 💪
                                            </h3>
                                            <p className="text-sm text-white/50">
                                                Review the slides and try again
                                                when you&apos;re ready.
                                            </p>
                                        </>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* ─── Footer ─────────────────────────────── */}
                    {phase !== "loading" && !error && (
                        <div
                            className="shrink-0 px-6 py-4"
                            style={{
                                borderTop:
                                    "1px solid rgba(255, 255, 255, 0.06)",
                            }}
                        >
                            {/* Correct feedback → Next */}
                            {phase === "feedback" &&
                                currentAnswer?.isCorrect && (
                                    <button
                                        onClick={handleNext}
                                        className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98]"
                                        style={{
                                            background:
                                                "linear-gradient(135deg, #6366f1, #7c3aed)",
                                            boxShadow:
                                                "0 4px 16px rgba(99, 102, 241, 0.3)",
                                        }}
                                    >
                                        {currentIndex < totalQuestions - 1
                                            ? "Next Question"
                                            : "See Results"}
                                        <ChevronRight className="w-4 h-4" />
                                    </button>
                                )}

                            {/* Incorrect + explanation viewed → Continue */}
                            {phase === "feedback" &&
                                !currentAnswer?.isCorrect &&
                                currentAnswer?.explanationViewed && (
                                    <div className="flex gap-3">
                                        <button
                                            onClick={handleRetry}
                                            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all hover:scale-[1.02] active:scale-[0.98]"
                                            style={{
                                                background:
                                                    "rgba(255, 255, 255, 0.06)",
                                                border: "1px solid rgba(255, 255, 255, 0.1)",
                                                color: "rgba(255, 255, 255, 0.75)",
                                            }}
                                        >
                                            <RotateCcw className="w-3.5 h-3.5" />
                                            Retry
                                        </button>
                                        <button
                                            onClick={handleNext}
                                            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98]"
                                            style={{
                                                background:
                                                    "linear-gradient(135deg, #6366f1, #7c3aed)",
                                                boxShadow:
                                                    "0 4px 16px rgba(99, 102, 241, 0.3)",
                                            }}
                                        >
                                            {currentIndex <
                                            totalQuestions - 1
                                                ? "Next Question"
                                                : "See Results"}
                                            <ChevronRight className="w-4 h-4" />
                                        </button>
                                    </div>
                                )}

                            {/* Completed → Continue Lesson */}
                            {phase === "completed" && (
                                <button
                                    onClick={onClose}
                                    className="w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98]"
                                    style={{
                                        background:
                                            "linear-gradient(135deg, #6366f1, #7c3aed)",
                                        boxShadow:
                                            "0 4px 16px rgba(99, 102, 241, 0.3)",
                                    }}
                                >
                                    Continue Lesson
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Animations */}
            <style jsx global>{`
                @keyframes quizFadeIn {
                    from {
                        opacity: 0;
                        transform: scale(0.95) translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1) translateY(0);
                    }
                }
                @keyframes slideUp {
                    from {
                        opacity: 0;
                        transform: translate(-50%, 20px);
                    }
                    to {
                        opacity: 1;
                        transform: translate(-50%, 0);
                    }
                }
            `}</style>
        </>
    );
}
