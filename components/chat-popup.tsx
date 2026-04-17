"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { X, Send, Loader2, MessageSquare, Sparkles } from "lucide-react";

interface ChatMessage {
    role: "user" | "assistant";
    content: string;
}

interface ChatPopupProps {
    isOpen: boolean;
    onClose: () => void;
    taskId: string;
    currentSlideTitle?: string;
    lessonTopic?: string;
}

export function ChatPopup({
    isOpen,
    onClose,
    taskId,
    currentSlideTitle,
    lessonTopic,
}: ChatPopupProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Focus input when popup opens
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 200);
        }
    }, [isOpen]);

    const sendMessage = useCallback(async () => {
        const question = input.trim();
        if (!question || isLoading) return;

        const userMessage: ChatMessage = { role: "user", content: question };
        const updatedHistory = [...messages, userMessage];
        setMessages(updatedHistory);
        setInput("");
        setIsLoading(true);

        try {
            const res = await fetch("/api/qna", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    task_id: taskId,
                    question,
                    chat_history: messages, // Send previous history (before this message)
                    current_slide_title: currentSlideTitle || null,
                }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || "Failed to get response");
            }

            const data = await res.json();
            setMessages([
                ...updatedHistory,
                { role: "assistant", content: data.answer },
            ]);
        } catch (err: any) {
            setMessages([
                ...updatedHistory,
                {
                    role: "assistant",
                    content: "Sorry, I couldn't process that. Please try again.",
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    }, [input, isLoading, messages, taskId, currentSlideTitle]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
        // Stop keyboard events from bubbling to the slide player
        e.stopPropagation();
    };

    if (!isOpen) return null;

    return (
        <div
            className="fixed bottom-24 right-6 z-50 w-[400px] max-w-[calc(100vw-2rem)] flex flex-col"
            style={{
                height: "min(520px, calc(100vh - 10rem))",
            }}
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => e.stopPropagation()}
        >
            {/* Glassmorphism container */}
            <div
                className="flex flex-col h-full rounded-2xl overflow-hidden shadow-2xl"
                style={{
                    background: "rgba(15, 20, 40, 0.85)",
                    backdropFilter: "blur(24px)",
                    WebkitBackdropFilter: "blur(24px)",
                    border: "1px solid rgba(99, 102, 241, 0.2)",
                }}
            >
                {/* ─── Header ─────────────────────────────────────── */}
                <div
                    className="flex items-center justify-between px-5 py-3.5 shrink-0"
                    style={{
                        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
                        background: "rgba(99, 102, 241, 0.08)",
                    }}
                >
                    <div className="flex items-center gap-2.5">
                        <div
                            className="w-8 h-8 rounded-lg flex items-center justify-center"
                            style={{
                                background:
                                    "linear-gradient(135deg, #6366f1, #8b5cf6)",
                            }}
                        >
                            <Sparkles className="w-4 h-4 text-white" />
                        </div>
                        <div>
                            <p className="text-sm font-semibold text-white/90 leading-tight">
                                Ask Teacher
                            </p>
                            <p className="text-[11px] text-white/40 leading-tight">
                                {lessonTopic
                                    ? `About: ${lessonTopic.length > 30 ? lessonTopic.slice(0, 30) + "…" : lessonTopic}`
                                    : "Ask anything about this lesson"}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-lg hover:bg-white/10 transition-colors text-white/50 hover:text-white"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* ─── Messages ───────────────────────────────────── */}
                <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 scrollbar-thin">
                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-full text-center px-6 gap-3 opacity-60">
                            <MessageSquare className="w-10 h-10 text-indigo-400/50" />
                            <div>
                                <p className="text-sm text-white/60 font-medium">
                                    Got a question?
                                </p>
                                <p className="text-xs text-white/35 mt-1">
                                    Ask about anything on the current
                                    slide or the lesson topic. I&apos;ll
                                    explain it your way.
                                </p>
                            </div>
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <div
                            key={i}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div
                                className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed ${
                                    msg.role === "user"
                                        ? "rounded-br-md"
                                        : "rounded-bl-md"
                                }`}
                                style={
                                    msg.role === "user"
                                        ? {
                                              background:
                                                  "linear-gradient(135deg, #6366f1, #7c3aed)",
                                              color: "white",
                                          }
                                        : {
                                              background:
                                                  "rgba(255, 255, 255, 0.07)",
                                              color: "rgba(255, 255, 255, 0.88)",
                                              border: "1px solid rgba(255, 255, 255, 0.06)",
                                          }
                                }
                            >
                                {msg.role === "assistant" ? (
                                    <div
                                        className="chat-answer-content"
                                        dangerouslySetInnerHTML={{
                                            __html: formatMarkdown(msg.content),
                                        }}
                                    />
                                ) : (
                                    msg.content
                                )}
                            </div>
                        </div>
                    ))}

                    {/* Loading indicator */}
                    {isLoading && (
                        <div className="flex justify-start">
                            <div
                                className="px-4 py-3 rounded-2xl rounded-bl-md flex items-center gap-2"
                                style={{
                                    background: "rgba(255, 255, 255, 0.07)",
                                    border: "1px solid rgba(255, 255, 255, 0.06)",
                                }}
                            >
                                <div className="flex gap-1">
                                    <span
                                        className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce"
                                        style={{ animationDelay: "0ms" }}
                                    />
                                    <span
                                        className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce"
                                        style={{ animationDelay: "150ms" }}
                                    />
                                    <span
                                        className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-bounce"
                                        style={{ animationDelay: "300ms" }}
                                    />
                                </div>
                                <span className="text-xs text-white/40 ml-1">
                                    Thinking...
                                </span>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* ─── Input ──────────────────────────────────────── */}
                <div
                    className="shrink-0 px-4 pb-4 pt-2"
                    style={{
                        borderTop: "1px solid rgba(255, 255, 255, 0.06)",
                    }}
                >
                    <div
                        className="flex items-center gap-2 rounded-xl px-3.5 py-2.5"
                        style={{
                            background: "rgba(255, 255, 255, 0.06)",
                            border: "1px solid rgba(255, 255, 255, 0.08)",
                        }}
                    >
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Type your question..."
                            disabled={isLoading}
                            className="flex-1 bg-transparent border-none outline-none text-sm text-white/90 placeholder-white/25 disabled:opacity-50"
                        />
                        <button
                            onClick={sendMessage}
                            disabled={!input.trim() || isLoading}
                            className="p-1.5 rounded-lg transition-all disabled:opacity-20"
                            style={{
                                background: input.trim()
                                    ? "linear-gradient(135deg, #6366f1, #7c3aed)"
                                    : "transparent",
                            }}
                        >
                            {isLoading ? (
                                <Loader2 className="w-4 h-4 text-white/60 animate-spin" />
                            ) : (
                                <Send className="w-4 h-4 text-white/80" />
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

/**
 * Minimal markdown → HTML for the assistant's responses.
 * Handles bold, inline code, code blocks, and line breaks.
 */
function formatMarkdown(text: string): string {
    return text
        // Code blocks (triple backticks)
        .replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre style="background:rgba(255,255,255,0.05);padding:8px 12px;border-radius:8px;overflow-x:auto;margin:6px 0;font-size:12px;"><code>$2</code></pre>')
        // Inline code
        .replace(/`([^`]+)`/g, '<code style="background:rgba(99,102,241,0.2);padding:1px 5px;border-radius:4px;font-size:12px;">$1</code>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        // Italic
        .replace(/\*(.+?)\*/g, "<em>$1</em>")
        // Bullet points
        .replace(/^[-•]\s+(.+)$/gm, '<div style="padding-left:12px;position:relative;margin:2px 0;">• $1</div>')
        // Numbered lists
        .replace(/^(\d+)\.\s+(.+)$/gm, '<div style="padding-left:12px;position:relative;margin:2px 0;">$1. $2</div>')
        // Line breaks
        .replace(/\n/g, "<br/>");
}
