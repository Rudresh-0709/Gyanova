"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { BackgroundBeams } from "@/components/ui/background-beams";
import Link from "next/link";
import {
    ArrowLeft,
    ChevronLeft,
    ChevronRight,
    Play,
    Pause,
    Volume2,
    VolumeX,
    X,
} from "lucide-react";

// ─── Types ──────────────────────────────────────────────────────────────
interface NarrationSegment {
    text: string;
    audio_url: string | null;
    segment_index: number;
}

interface SlideEntry {
    slide_id: string;
    title: string;
    html_doc: string;           // single-section HTML document
    narration_segments: NarrationSegment[];
    subtopic_name: string;
}

// ─── Helpers ────────────────────────────────────────────────────────────

const BACKEND_URL = "http://localhost:8000";

/**
 * Convert a filesystem audio_url from the backend into an HTTP URL
 * that can be fetched from the static mount.
 *
 * e.g. "d:/DATA/.../audio_output/slides/sub_1_xyz/segment_1.mp3"
 *   → "http://localhost:8000/audio/slides/sub_1_xyz/segment_1.mp3"
 */
function toAudioHttpUrl(fsPath: string | null): string | null {
    if (!fsPath) return null;
    // Normalise separators
    const normalised = fsPath.replace(/\\/g, "/");
    const marker = "audio_output/";
    const idx = normalised.indexOf(marker);
    if (idx === -1) return null;
    const relative = normalised.slice(idx + marker.length);
    return `${BACKEND_URL}/audio/${relative}`;
}

/**
 * Generate a simple "Intro" slide HTML for the lesson opening.
 */
function generateIntroHtml(topic: string, title?: string): string {
    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Introduction</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            body { 
                margin: 0; 
                background: #0a0f1a; 
                color: white; 
                font-family: 'Inter', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                text-align: center;
                overflow: hidden;
            }
            .content { padding: 2rem; max-width: 800px; animation: fadeIn 1s ease-out; }
            h1 { font-size: 4rem; font-weight: 800; margin: 0.5rem 0 1.5rem 0; color: white; line-height: 1.1; }
            p { font-size: 1.25rem; opacity: 0.5; text-transform: uppercase; letter-spacing: 0.2em; font-weight: 500; }
            .glow { 
                position: absolute; width: 600px; height: 600px; 
                background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, rgba(99,102,241,0) 70%); 
                z-index: -1; 
            }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        </style>
    </head>
    <body>
        <div class="glow"></div>
        <div class="content">
            <p>Lesson Introduction</p>
            <h1>${topic}</h1>
        </div>
        <script>
            // Signal readiness immediately
            window.parent.postMessage({ type: 'iframeReady' }, '*');
            
            // Intersection relay
            window.addEventListener('mousemove', function() { window.parent.postMessage({ type: 'userInteraction' }, '*'); });
        </script>
    </body>
    </html>`;
}

/**
 * Take a full HTML deck (potentially many <section>s) and return an
 * array of single-section HTML documents.  Each keeps the original
 * <head> styles/links + a small override so 100 vh sizing doesn't
 * force inner scrolling.
 */
function splitDeckIntoSlides(html: string): string[] {
    try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, "text/html");
        const sections = Array.from(doc.querySelectorAll("section"));
        const headLinks = Array.from(doc.head.querySelectorAll("link"))
            .map((l) => l.outerHTML)
            .join("");
        const styleTag = doc.head.querySelector("style")?.outerHTML || "";

        // Override: let the section fill the viewport naturally
        const overrideStyles = `<style>
            .gyml-deck{height:100%!important;overflow:hidden!important;}
            section{height:100%!important;overflow:hidden!important;}
            body{margin:0!important;height:100%!important;overflow:hidden!important;}
            html{height:100%!important;}
        </style>`;

        // Inject a bridge script that:
        //   1. Monkey-patches SlideAnimator prototype to prevent auto-reveal
        //   2. Listens for postMessage commands from the parent player
        //   3. Signals readiness to the parent once initialized
        const bridgeScript = `<script>
        (function() {
            var _ready = false;
            var _commandQueue = [];
            var _animator = null;

            // Use a more robust way to block auto-reveal: 
            // Monkey-patch the prototype if it exists, or wait for it.
            function patchSlideAnimator() {
                if (window.SlideAnimator && !window.SlideAnimator._patched) {
                    var proto = window.SlideAnimator.prototype;
                    var origRevealAll = proto.revealAll;
                    
                    // The real revealAll that we can trigger via message
                    proto._realRevealAll = origRevealAll;
                    
                    // The blocked one that renderer calls at 100ms
                    proto.revealAll = function() {
                        console.log("SlideAnimator: blocked auto-revealAll");
                    };
                    
                    window.SlideAnimator._patched = true;
                    return true;
                }
                return false;
            }

            // Poll for animator instance and prototype
            var _initInterval = setInterval(function() {
                patchSlideAnimator();
                
                if (window.slideAnimators && Object.keys(window.slideAnimators).length > 0) {
                    _animator = Object.values(window.slideAnimators)[0];
                    
                    // Ensure it starts reset
                    if (_animator.reset) _animator.reset();

                    clearInterval(_initInterval);
                    _ready = true;

                    // Process any commands that arrived before we were ready
                    _commandQueue.forEach(function(cmd) { handleCommand(cmd); });
                    _commandQueue = [];

                    // Tell the parent we are ready
                    window.parent.postMessage({ type: 'iframeReady' }, '*');
                }
            }, 10);

            function handleCommand(data) {
                if (!_animator) return;
                switch (data.type) {
                    case 'revealSegment':
                        if (_animator.revealSegment) _animator.revealSegment(data.index);
                        break;
                    case 'revealAll':
                        // Use the real one we saved on the prototype
                        if (_animator._realRevealAll) _animator._realRevealAll();
                        else if (_animator.revealAll) _animator.revealAll();
                        break;
                    case 'reset':
                        if (_animator.reset) _animator.reset();
                        break;
                }
            }

            // Listen for commands from parent
            window.addEventListener('message', function(e) {
                var data = e.data;
                if (!data || !data.type) return;
                if (!_ready) {
                    _commandQueue.push(data);
                    return;
                }
                handleCommand(data);
            });
            
            // Interaction relay
            window.addEventListener('mousemove', function() { window.parent.postMessage({ type: 'userInteraction' }, '*'); });
            window.addEventListener('mousedown', function() { window.parent.postMessage({ type: 'userInteraction' }, '*'); });
        })();
        <\/script>`;

        // Also grab inline scripts (the SlideAnimator code)
        const bodyScripts = Array.from(doc.body.querySelectorAll("script"))
            .map((s) => s.outerHTML)
            .join("");

        if (sections.length === 0) return [html];

        return sections.map(
            (sec) =>
                `<html><head>${headLinks}${styleTag}${overrideStyles}</head>` +
                `<body><div class="gyml-deck">${sec.outerHTML}</div>${bodyScripts}${bridgeScript}</body></html>`
        );
    } catch {
        return [html];
    }
}

// ─── Component ──────────────────────────────────────────────────────────

export default function LessonViewPage() {
    const params = useParams();
    const router = useRouter();
    const taskId = params.id as string;

    // Data
    const [lessonData, setLessonData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [slideList, setSlideList] = useState<SlideEntry[]>([]);

    // Player state
    const [currentSlideIdx, setCurrentSlideIdx] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [currentSegIdx, setCurrentSegIdx] = useState(-1);
    const [showControls, setShowControls] = useState(true);
    const [iframeReady, setIframeReady] = useState(false);

    // Refs (used to avoid stale closures in callbacks)
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const iframeRef = useRef<HTMLIFrameElement | null>(null);
    const controlsTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const slideIdxRef = useRef(0);
    const segIdxRef = useRef(-1);
    const isPlayingRef = useRef(false);
    const playSegmentRef = useRef<(slideIdx: number, segIdx: number) => void>(() => { });

    // ─── Fetch lesson data (Polling) ──────────────────────────────────
    useEffect(() => {
        let pollTimer: ReturnType<typeof setTimeout>;

        const fetchLesson = async () => {
            try {
                const response = await fetch(
                    `/api/lesson/generate?taskId=${taskId}`
                );
                if (!response.ok) throw new Error("Failed to load lesson");
                const data = await response.json();

                // Always update result if present (could have more slides)
                if (data.result) {
                    setLessonData(data.result);
                }

                if (data.status === "completed") {
                    setLoading(false);
                    // stop polling
                } else if (data.status === "failed") {
                    setError("This lesson failed to generate.");
                    setLoading(false);
                } else if (data.status === "processing" || data.status === "pending" || data.status === "planning_completed") {
                    // Still cooking? If we have SOME slides, we can stop "initial loading" 
                    // but WE MUST KEEP POLLING.
                    if (data.result && Object.keys(data.result.slides || {}).length > 0) {
                        setLoading(false);
                    }
                    pollTimer = setTimeout(fetchLesson, 3000);
                } else {
                    setError("Lesson not found.");
                    setLoading(false);
                }
            } catch (err: any) {
                setError(err.message || "An error occurred");
                setLoading(false);
            }
        };

        if (taskId) fetchLesson();
        return () => clearTimeout(pollTimer);
    }, [taskId]);

    // ─── Build flattened slide list ─────────────────────────────────────
    useEffect(() => {
        if (!lessonData) return;
        const list: SlideEntry[] = [];

        // 1. Prepend Lesson Intro if available
        if (lessonData.lesson_intro_narration) {
            const intro = lessonData.lesson_intro_narration;
            list.push({
                slide_id: "lesson_intro",
                title: "Introduction",
                html_doc: generateIntroHtml(lessonData.topic || lessonData.user_input || "Lesson"),
                narration_segments: [
                    {
                        text: intro.narration_text || "Welcome to the lesson.",
                        audio_url: toAudioHttpUrl(intro.audio_url),
                        segment_index: 0,
                    },
                ],
                subtopic_name: "Getting Started",
            });
        }

        lessonData.sub_topics?.forEach((sub: any) => {
            const slides = lessonData.slides?.[sub.id] || [];
            slides.forEach((slide: any) => {
                const docs = splitDeckIntoSlides(slide.html_content || "");
                docs.forEach((doc, docIdx) => {
                    list.push({
                        slide_id: `${slide.slide_id || "unknown"}_${docIdx}`,
                        title: slide.title || sub.name || "Slide",
                        html_doc: doc,
                        narration_segments: (
                            slide.narration_segments || []
                        ).map((seg: any) => ({
                            ...seg,
                            audio_url: toAudioHttpUrl(seg.audio_url),
                        })),
                        subtopic_name: sub.name || "",
                    });
                });
            });
        });

        setSlideList(prev => {
            // Only update if the length changed to avoid unnecessary re-renders
            if (prev.length !== list.length) {
                return list;
            }
            return prev;
        });
    }, [lessonData]);

    // ─── Controls auto-hide ─────────────────────────────────────────────
    const resetControlsTimer = useCallback(() => {
        setShowControls(true);
        if (controlsTimerRef.current) clearTimeout(controlsTimerRef.current);
        controlsTimerRef.current = setTimeout(
            () => setShowControls(false),
            3000
        );
    }, []);

    useEffect(() => {
        resetControlsTimer();
        return () => {
            if (controlsTimerRef.current)
                clearTimeout(controlsTimerRef.current);
        };
    }, [resetControlsTimer]);

    // ─── Keep refs in sync with state ─────────────────────────────────────
    useEffect(() => { slideIdxRef.current = currentSlideIdx; }, [currentSlideIdx]);
    useEffect(() => { segIdxRef.current = currentSegIdx; }, [currentSegIdx]);
    useEffect(() => { isPlayingRef.current = isPlaying; }, [isPlaying]);

    // ─── Iframe messaging ───────────────────────────────────────────────
    const postToSlide = useCallback(
        (msg: any) => {
            iframeRef.current?.contentWindow?.postMessage(msg, "*");
        },
        []
    );

    // Listen for messages FROM the iframe (readiness + user interaction)
    useEffect(() => {
        const handleMessage = (e: MessageEvent) => {
            if (e.data?.type === "userInteraction") {
                resetControlsTimer();
            }
            if (e.data?.type === "iframeReady") {
                setIframeReady(true);
            }
        };
        window.addEventListener("message", handleMessage);
        return () => window.removeEventListener("message", handleMessage);
    }, [resetControlsTimer]);

    // ─── Audio playback engine ──────────────────────────────────────────
    const playSegment = useCallback(
        (slideIdx: number, segIdx: number) => {
            if (slideIdx >= slideList.length) return;
            const slide = slideList[slideIdx];
            const segments = slide.narration_segments;

            // If no more segments in this slide, auto-advance
            if (segIdx >= segments.length) {
                // Safety: Reveal all cards before moving to next slide
                postToSlide({ type: "revealAll" });

                // Small pause before advancing
                setTimeout(() => {
                    if (slideIdx < slideList.length - 1) {
                        setCurrentSlideIdx(slideIdx + 1);
                        setCurrentSegIdx(-1);
                    } else {
                        setIsPlaying(false); // end of deck
                    }
                }, 800);
                return;
            }

            const seg = segments[segIdx];
            setCurrentSegIdx(segIdx);

            // Reveal animation segment in the iframe
            postToSlide({ type: "revealSegment", index: segIdx });

            // Play audio
            if (seg.audio_url && audioRef.current) {
                audioRef.current.src = seg.audio_url;
                audioRef.current.muted = isMuted;
                audioRef.current
                    .play()
                    .catch(() => {
                        // Autoplay blocked — advance anyway after a delay
                        setTimeout(
                            () => playSegment(slideIdx, segIdx + 1),
                            2000
                        );
                    });
            } else {
                // No audio for this segment — advance after brief delay
                setTimeout(() => playSegment(slideIdx, segIdx + 1), 1500);
            }
        },
        [slideList, isMuted, postToSlide]
    );

    // Keep playSegmentRef up to date
    useEffect(() => { playSegmentRef.current = playSegment; }, [playSegment]);

    // When audio ends → play next segment (uses refs to avoid stale closures)
    useEffect(() => {
        const audio = audioRef.current;
        if (!audio) return;
        const onEnded = () => {
            if (isPlayingRef.current) {
                playSegmentRef.current(slideIdxRef.current, segIdxRef.current + 1);
            }
        };
        audio.addEventListener("ended", onEnded);
        return () => audio.removeEventListener("ended", onEnded);
    }, [slideList.length]); // re-run when slides load (audio element appears in DOM)

    // ─── Start playing when slide changes (if isPlaying) ────────────────
    // Reset iframeReady when the slide changes (iframe remounts)
    useEffect(() => {
        setIframeReady(false);
    }, [currentSlideIdx, slideList.length]); // reset if list changes too

    // When iframe signals ready AND we're playing, start from segment 0
    useEffect(() => {
        if (!iframeReady || !isPlaying || slideList.length === 0) return;

        // If we are already mid-way through a slide (segIdx >= 0), don't restart from 0
        if (segIdxRef.current >= 0) return;

        // Iframe just signaled ready — start from segment 0
        postToSlide({ type: "reset" });
        const t = setTimeout(() => {
            playSegment(currentSlideIdx, 0);
        }, 150);
        return () => clearTimeout(t);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [iframeReady, isPlaying, currentSlideIdx, slideList.length]);

    // When isPlaying changes (pause/resume) WITHOUT a slide change:
    // Resume from current segment instead of restarting
    useEffect(() => {
        if (!iframeReady || slideList.length === 0) return;
        if (isPlaying && segIdxRef.current >= 0) {
            // Resuming — play the next segment from where we left off
            const audio = audioRef.current;
            if (audio && audio.src && audio.paused) {
                audio.play().catch(() => { });
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isPlaying]);

    // ─── Auto-start on first load ───────────────────────────────────────
    useEffect(() => {
        if (iframeReady && slideList.length > 0 && !isPlaying) {
            // Iframe is ready, start playing
            const t = setTimeout(() => setIsPlaying(true), 150);
            return () => clearTimeout(t);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [iframeReady, slideList.length]);

    // ─── If no narration segments, reveal all immediately ───────────────
    useEffect(() => {
        if (slideList.length === 0) return;
        const slide = slideList[currentSlideIdx];
        if (!slide) return;
        const hasAudio = slide.narration_segments.some((s) => s.audio_url);
        if (!hasAudio) {
            // No audio → reveal all cards immediately
            const t = setTimeout(
                () => postToSlide({ type: "revealAll" }),
                500
            );
            return () => clearTimeout(t);
        }
    }, [currentSlideIdx, slideList, postToSlide]);



    // ─── Keyboard navigation ────────────────────────────────────────────
    useEffect(() => {
        const onKey = (e: KeyboardEvent) => {
            resetControlsTimer();
            switch (e.key) {
                case "ArrowRight":
                case " ":
                    e.preventDefault();
                    goNext();
                    break;
                case "ArrowLeft":
                    e.preventDefault();
                    goPrev();
                    break;
                case "Escape":
                    router.push("/lesson/new");
                    break;
                case "m":
                    setIsMuted((m) => !m);
                    break;
            }
        };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [slideList.length, currentSlideIdx]);

    // ─── Navigation handlers ────────────────────────────────────────────
    const goNext = () => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
        }
        if (currentSlideIdx < slideList.length - 1) {
            setCurrentSlideIdx((i) => i + 1);
            setCurrentSegIdx(-1);
        }
    };

    const goPrev = () => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
        }
        if (currentSlideIdx > 0) {
            setCurrentSlideIdx((i) => i - 1);
            setCurrentSegIdx(-1);
        }
    };

    const togglePlayPause = () => {
        if (isPlaying) {
            audioRef.current?.pause();
            setIsPlaying(false);
        } else {
            setIsPlaying(true);
        }
    };

    const toggleMute = () => {
        setIsMuted((m) => {
            if (audioRef.current) audioRef.current.muted = !m;
            return !m;
        });
    };

    // ─── Progress ───────────────────────────────────────────────────────
    const currentSlide = slideList[currentSlideIdx];
    const totalSegments = currentSlide?.narration_segments.length || 0;
    const segProgress =
        totalSegments > 0
            ? ((currentSegIdx + 1) / totalSegments) * 100
            : 100;

    // ─── Renders ────────────────────────────────────────────────────────

    // Loading state
    if (loading) {
        return (
            <div className="min-h-screen w-full bg-[#0a0f1a] flex items-center justify-center relative">
                <BackgroundBeams className="opacity-40" />
                <div className="text-white z-10 flex flex-col items-center gap-4">
                    <div className="w-8 h-8 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
                    <p className="animate-pulse">Loading Lesson...</p>
                </div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="min-h-screen w-full bg-[#0a0f1a] flex flex-col items-center justify-center p-4 relative">
                <BackgroundBeams className="opacity-40" />
                <div className="bg-red-500/10 border border-red-500/20 text-red-100 p-6 rounded-2xl z-10 max-w-md text-center">
                    <h2 className="text-2xl font-bold mb-2">Oops!</h2>
                    <p className="mb-6 opacity-80">{error}</p>
                    <Link
                        href="/lesson/new"
                        className="px-6 py-2 bg-red-500 hover:bg-red-600 rounded-xl transition-colors font-semibold"
                    >
                        Try Again
                    </Link>
                </div>
            </div>
        );
    }

    if (!lessonData || slideList.length === 0) return null;

    return (
        <div
            className="fixed inset-0 bg-[#0a0f1a] z-50 flex flex-col"
            onMouseMove={resetControlsTimer}
            onClick={resetControlsTimer}
        >
            {/* Hidden audio element */}
            <audio ref={audioRef} preload="auto" />

            {/* ─── Top bar ─────────────────────────────────────────── */}
            <div
                className={`absolute top-0 left-0 right-0 z-30 transition-opacity duration-300 ${showControls ? "opacity-100" : "opacity-0 pointer-events-none"
                    }`}
            >
                {/* Narration progress bar */}
                <div className="h-1 bg-white/10 w-full">
                    <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500 ease-out"
                        style={{ width: `${segProgress}%` }}
                    />
                </div>

                <div className="flex items-center justify-between px-4 py-3">
                    {/* Back button */}
                    <button
                        onClick={() => router.push("/lesson/new")}
                        className="flex items-center gap-2 text-white/70 hover:text-white transition-colors text-sm"
                    >
                        <X className="w-5 h-5" />
                        <span className="hidden sm:inline">Exit</span>
                    </button>

                    {/* Slide info */}
                    <div className="text-center">
                        <p className="text-white/50 text-xs uppercase tracking-wider">
                            {currentSlide?.subtopic_name}
                        </p>
                        <p className="text-white/80 text-sm font-medium mt-0.5">
                            {currentSlide?.title}
                        </p>
                    </div>

                    {/* Slide counter */}
                    <div className="text-white/50 text-sm font-mono">
                        {currentSlideIdx + 1} / {slideList.length}
                    </div>
                </div>
            </div>

            {/* ─── Slide iframe ────────────────────────────────────── */}
            <div className="flex-1 relative">
                <iframe
                    ref={iframeRef}
                    key={currentSlideIdx}
                    title={`Slide ${currentSlideIdx + 1}`}
                    className="absolute inset-0 w-full h-full border-0"
                    srcDoc={currentSlide?.html_doc}
                    sandbox="allow-same-origin allow-scripts"
                />
            </div>

            {/* ─── Bottom controls ─────────────────────────────────── */}
            <div
                className={`absolute bottom-0 left-0 right-0 z-30 transition-opacity duration-300 ${showControls ? "opacity-100" : "opacity-0 pointer-events-none"
                    }`}
            >
                {/* Slide progress dots */}
                <div className="flex justify-center gap-1.5 pb-3">
                    {slideList.map((_, i) => (
                        <button
                            key={i}
                            onClick={() => {
                                if (audioRef.current) {
                                    audioRef.current.pause();
                                    audioRef.current.currentTime = 0;
                                }
                                setCurrentSlideIdx(i);
                                setCurrentSegIdx(-1);
                            }}
                            className={`w-2 h-2 rounded-full transition-all duration-300 ${i === currentSlideIdx
                                ? "bg-indigo-400 w-6"
                                : i < currentSlideIdx
                                    ? "bg-white/40"
                                    : "bg-white/15"
                                }`}
                        />
                    ))}
                </div>

                <div className="flex items-center justify-between px-6 pb-6">
                    {/* Previous */}
                    <button
                        onClick={goPrev}
                        disabled={currentSlideIdx === 0}
                        className="p-3 rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-20 disabled:cursor-not-allowed transition-all text-white backdrop-blur-sm"
                    >
                        <ChevronLeft className="w-6 h-6" />
                    </button>

                    {/* Center controls */}
                    <div className="flex items-center gap-3">
                        <button
                            onClick={toggleMute}
                            className="p-2.5 rounded-full bg-white/10 hover:bg-white/20 transition-all text-white backdrop-blur-sm"
                        >
                            {isMuted ? (
                                <VolumeX className="w-5 h-5" />
                            ) : (
                                <Volume2 className="w-5 h-5" />
                            )}
                        </button>

                        <button
                            onClick={togglePlayPause}
                            className="p-4 rounded-full bg-indigo-500 hover:bg-indigo-600 transition-all text-white shadow-lg shadow-indigo-500/30"
                        >
                            {isPlaying ? (
                                <Pause className="w-6 h-6" />
                            ) : (
                                <Play className="w-6 h-6 ml-0.5" />
                            )}
                        </button>

                        <div className="w-10" /> {/* spacer */}
                    </div>

                    {/* Next */}
                    <button
                        onClick={goNext}
                        disabled={currentSlideIdx === slideList.length - 1}
                        className="p-3 rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-20 disabled:cursor-not-allowed transition-all text-white backdrop-blur-sm"
                    >
                        <ChevronRight className="w-6 h-6" />
                    </button>
                </div>
            </div>

            {/* ─── Side navigation (hover areas) ──────────────────── */}
            <div
                className="absolute left-0 top-1/2 -translate-y-1/2 w-16 h-32 cursor-pointer z-20"
                onClick={goPrev}
            />
            <div
                className="absolute right-0 top-1/2 -translate-y-1/2 w-16 h-32 cursor-pointer z-20"
                onClick={goNext}
            />
        </div>
    );
}
