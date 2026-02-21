"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { BackgroundBeams } from "@/components/ui/background-beams";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { motion } from "framer-motion";

export default function LessonViewPage() {
    const params = useParams();
    const router = useRouter();
    const taskId = params.id as string;

    const [lessonData, setLessonData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // flattened list of all slides (with html_doc property)
    const [slideList, setSlideList] = useState<any[]>([]);
    const [currentSlideIdx, setCurrentSlideIdx] = useState(0);
    const [fullscreen, setFullscreen] = useState(false);

    /**
     * The generation service returns a full HTML deck for every slide.  A deck
     * typically contains several <section> slides plus all of the <style> and
     * <link> references in the head.  To display a single slide we split the
     * document and rebuild a minimal page for each section.
     */
    /**
     * Return an array of single-slide HTML documents from the full deck.  Each
     * document includes the original head links/styles plus a small override so
     * that 100vh sizing doesn’t force inner scrolling.
     */
    const splitDeckIntoSlides = (html: string): string[] => {
        try {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");
            const sections = Array.from(doc.querySelectorAll("section"));
            const headLinks = Array.from(doc.head.querySelectorAll("link"))
                .map(l => l.outerHTML)
                .join("");
            const styleTag = doc.head.querySelector("style")?.outerHTML || "";
            const overrideStyles =
                `<style>.gyml-deck{height:auto!important;overflow:visible!important;} section{height:auto!important;overflow:visible!important;} body{margin:0!important;}</style>`;
            // also capture any inline scripts (e.g. initializer) from the original body
            const bodyScripts = Array.from(doc.body.querySelectorAll("script"))
                .map(s => s.outerHTML)
                .join("");

            if (sections.length === 0) {
                return [html];
            }
            return sections.map(sec =>
                `<html><head>${headLinks}${styleTag}${overrideStyles}</head>` +
                `<body><div class="gyml-deck">${sec.outerHTML}</div>${bodyScripts}</body></html>`
            );
        } catch {
            return [html];
        }
    };

    useEffect(() => {
        const fetchLesson = async () => {
            try {
                // Fetch the completed task from the Next.js proxy route
                const response = await fetch(`/api/lesson/generate?taskId=${taskId}`);
                if (!response.ok) {
                    throw new Error("Failed to load lesson");
                }
                const data = await response.json();

                if (data.status === "completed" && data.result) {
                    setLessonData(data.result);
                } else if (data.status === "failed") {
                    setError("This lesson failed to generate.");
                } else {
                    setError("Lesson is still generating or not found.");
                }
            } catch (err: any) {
                setError(err.message || "An error occurred");
            } finally {
                setLoading(false);
            }
        };

        if (taskId) {
            fetchLesson();
        }
    }, [taskId]);

    // build flattened slide list whenever lessonData changes
    useEffect(() => {
        if (!lessonData) return;
        const list: any[] = [];
        lessonData.sub_topics?.forEach((sub: any) => {
            const slides = lessonData.slides?.[sub.id] || [];
            slides.forEach((slide: any) => {
                const docs = splitDeckIntoSlides(slide.html_content);
                docs.forEach(doc => {
                    list.push({
                        ...slide,
                        html_doc: doc,
                    });
                });
            });
        });
        setSlideList(list);
        setCurrentSlideIdx(0);
    }, [lessonData]);

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

    if (!lessonData) return null;

    return (
        <div className="min-h-screen w-full bg-[#0a0f1a] relative text-white pb-20">
            <BackgroundBeams className="opacity-20 fixed inset-0 pointer-events-none" />

            <div className="max-w-6xl mx-auto px-4 sm:px-6 pt-12 relative z-10">
                <Link href="/lesson/new" className="inline-flex items-center text-sm text-gray-400 hover:text-white transition-colors mb-12 group">
                    <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" /> Back to Creation
                </Link>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <h1 className="text-4xl md:text-5xl font-bold font-display mb-6 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
                        {lessonData.topic || "Generated AI Curriculum"}
                    </h1>

                    {lessonData.intro_text && (
                        <div className="p-6 bg-white/5 border border-white/10 rounded-2xl mb-8 backdrop-blur-sm">
                            <h3 className="text-sm uppercase tracking-wider text-gray-400 font-semibold mb-3">Lesson Introduction</h3>
                            <p className="text-lg text-gray-200 leading-relaxed">
                                {lessonData.intro_text}
                            </p>
                        </div>
                    )}

                    {/* navigation controls */}
                    {slideList.length > 0 && (
                        <div className="flex items-center justify-between mb-4">
                            <button
                                onClick={() => setCurrentSlideIdx(i => Math.max(i - 1, 0))}
                                disabled={currentSlideIdx === 0}
                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded"
                            >
                                ← Previous
                            </button>
                            <span className="text-sm text-gray-300">
                                {currentSlideIdx + 1} / {slideList.length}
                            </span>
                            <button
                                onClick={() => setCurrentSlideIdx(i => Math.min(i + 1, slideList.length - 1))}
                                disabled={currentSlideIdx === slideList.length - 1}
                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded"
                            >
                                Next →
                            </button>
                            <button
                                onClick={() => setFullscreen(true)}
                                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded ml-4"
                            >
                                Fullscreen
                            </button>
                        </div>
                    )}

                    {/* single slide viewer */}
                    {slideList.length > 0 ? (
                        <div className="bg-black/40 border border-white/10 rounded-2xl overflow-hidden backdrop-blur-sm flex flex-col">
                            {/* Slide Visual Content */}
                            <div className="relative aspect-video bg-gray-900 border-b border-white/10">
                                <iframe
                                    title={`Slide ${currentSlideIdx + 1}`}
                                    className="absolute inset-0 w-full h-full border-0 bg-transparent"
                                    srcDoc={slideList[currentSlideIdx].html_doc}
                                    sandbox="allow-same-origin allow-scripts"
                                />
                            </div>

                            {/* Slide Details (no audio or text) */}
                            <div className="p-5 flex-1 flex flex-col">
                                <h4 className="text-lg font-medium text-gray-200 mb-2">
                                    {slideList[currentSlideIdx].title}
                                </h4>
                            </div>
                        </div>
                    ) : (
                        <p className="text-gray-400">No slides available.</p>
                    )}

                    {/* fullscreen overlay */}
                    {fullscreen && slideList.length > 0 && (
                        <div
                            className="fixed inset-0 z-50 bg-[#0a0f1a] flex items-center justify-center"
                            onClick={() => setFullscreen(false)}
                        >
                            <iframe
                                title={`Slide full ${currentSlideIdx + 1}`}
                                className="w-full h-full border-0"
                                srcDoc={slideList[currentSlideIdx].html_doc}
                                sandbox="allow-same-origin allow-scripts"
                            />
                        </div>
                    )}
                </motion.div>
            </div>
        </div>
    );
}
