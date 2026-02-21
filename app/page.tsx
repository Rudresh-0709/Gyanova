
import { TypewriterEffect } from "@/components/ui/typewriter-effect";
import Link from "next/link";
import { BackgroundBeams } from "@/components/ui/background-beams";
import { Button } from "@/components/ui/moving-border";
import { BentoGrid, BentoGridItem } from "@/components/ui/bento-grid";
import { TextGenerateEffect } from "@/components/ui/text-generate-effect";
import { CardContainer, CardBody, CardItem } from "@/components/ui/3d-card";
import { Navbar } from "@/components/Navbar";

export default function Home() {
  return (
    <div className="bg-background-light dark:bg-background-dark text-gray-900 dark:text-gray-100 font-sans min-h-screen antialiased selection:bg-primary selection:text-white transition-colors duration-300 dark">

      <Navbar />
      <section className="relative pt-32 pb-20 overflow-hidden dark:bg-background-dark">
        <BackgroundBeams className="absolute inset-0 z-0 opacity-40" />
        <div className="absolute inset-0 grid-bg opacity-30 pointer-events-none z-0"></div>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] hero-glow pointer-events-none"></div>
        <div className="absolute top-20 right-0 w-96 h-96 bg-secondary/20 rounded-full blur-3xl pointer-events-none mix-blend-screen"></div>
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-primary/20 rounded-full blur-3xl pointer-events-none mix-blend-screen"></div>
        <div className="relative max-w-7xl mx-auto px-6 text-center z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-100 dark:border-indigo-500/30 text-indigo-600 dark:text-indigo-300 text-xs font-semibold mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            Tutor Engine v2.0 Now Live
          </div>
          <div className="h-[8rem] md:h-[10rem] flex justify-center items-center relative z-10">
            <TypewriterEffect
              words={[
                { text: "Your" },
                { text: "Personal" },
                { text: "AI", className: "text-primary dark:text-primary" },
                { text: "Tutor", className: "text-primary dark:text-primary" },
              ]}
            />
          </div>
          <p className="text-lg md:text-xl text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto leading-relaxed">
            Learn any subject with an intelligent tutor that explains complex ideas clearly,
            provides structured curricula, and adapts to your questions.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-10">
            <Link href="/lesson/new">
              <Button
                borderRadius="1.75rem"
                containerClassName="hover:scale-105 transition-transform duration-200"
                className="bg-white dark:bg-background-dark text-gray-900 dark:text-white font-semibold border-neutral-200 dark:border-slate-800"
              >
                Start Learning
              </Button>
            </Link>
            <button className="glass-panel text-gray-800 dark:text-white font-medium px-8 py-4 rounded-lg hover:bg-white/10 transition-colors flex items-center justify-center gap-2">
              <span className="material-symbols-outlined text-gray-500 dark:text-gray-400">
                play_circle
              </span>
              See A Lesson In Progress
            </button>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-500 mb-16 font-medium">
            Designed for people who want to truly understand.
          </p>
          <div className="relative max-w-6xl mx-auto rounded-xl border border-gray-200 dark:border-white/10 shadow-2xl bg-white dark:bg-surface-dark overflow-hidden group">
            <div className="h-10 border-b border-gray-200 dark:border-white/5 bg-gray-50 dark:bg-black/40 flex items-center px-4 gap-2 justify-between">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              </div>
              <div className="px-3 py-1 rounded bg-gray-200 dark:bg-white/5 text-xs text-gray-500 font-mono flex items-center gap-2">
                <span className="material-symbols-outlined text-[10px]">
                  lock
                </span>
                gyanova.app/engine/generate
              </div>
              <div className="w-10"></div>
            </div>
            <div className="flex h-[550px] text-left">
              <div className="w-1/3 border-r border-gray-200 dark:border-white/5 bg-gray-50 dark:bg-black/20 p-6 flex flex-col">
                <div className="flex items-center justify-between mb-6">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                    Curriculum Tree
                  </span>
                  <span className="text-xs text-green-400 font-mono animate-pulse">
                    Generating...
                  </span>
                </div>
                <div className="space-y-3 relative">
                  <div className="absolute left-[11px] top-6 bottom-6 w-0.5 bg-gray-200 dark:bg-white/10"></div>
                  <div className="relative flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center z-10 shrink-0">
                      <span className="material-symbols-outlined text-white text-[14px]">
                        school
                      </span>
                    </div>
                    <div className="flex-1 bg-white dark:bg-surface-dark border border-gray-200 dark:border-white/10 p-3 rounded-lg shadow-sm">
                      <div className="font-semibold text-sm text-gray-900 dark:text-white">
                        Topic: Neural Networks
                      </div>
                    </div>
                  </div>
                  <div
                    className="relative flex items-center gap-3 pl-8 animate-fade-in-up"
                    style={{ animationDelay: "0.1s" }}
                  >
                    <div className="absolute left-[11px] top-1/2 w-6 h-0.5 bg-gray-200 dark:bg-white/10"></div>
                    <div className="w-5 h-5 rounded-full bg-secondary flex items-center justify-center z-10 shrink-0 border-2 border-background-dark">
                      <span className="material-symbols-outlined text-white text-[10px]">
                        check
                      </span>
                    </div>
                    <div className="flex-1 bg-white dark:bg-surface-dark border border-gray-200 dark:border-white/10 p-2.5 rounded-lg">
                      <div className="font-medium text-xs text-gray-900 dark:text-gray-200">
                        1. Perceptron Basics
                      </div>
                    </div>
                  </div>
                  <div
                    className="relative flex items-center gap-3 pl-8 animate-fade-in-up"
                    style={{ animationDelay: "0.3s" }}
                  >
                    <div className="absolute left-[11px] top-1/2 w-6 h-0.5 bg-gray-200 dark:bg-white/10"></div>
                    <div className="w-5 h-5 rounded-full bg-secondary flex items-center justify-center z-10 shrink-0 border-2 border-background-dark">
                      <span className="material-symbols-outlined text-white text-[10px]">
                        sync
                      </span>
                    </div>
                    <div className="flex-1 bg-indigo-500/10 border border-indigo-500/30 p-2.5 rounded-lg">
                      <div className="font-medium text-xs text-indigo-300">
                        2. Backpropagation
                      </div>
                      <div className="text-[10px] text-indigo-400/70 mt-1">
                        Generating Flowchart...
                      </div>
                    </div>
                  </div>
                  <div className="relative flex items-center gap-3 pl-8 opacity-50">
                    <div className="absolute left-[11px] top-1/2 w-6 h-0.5 bg-gray-200 dark:bg-white/10"></div>
                    <div className="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center z-10 shrink-0 border-2 border-background-dark">
                      <span className="material-symbols-outlined text-gray-400 text-[10px]">
                        schedule
                      </span>
                    </div>
                    <div className="flex-1 bg-white/5 border border-white/5 p-2.5 rounded-lg">
                      <div className="font-medium text-xs text-gray-500">
                        3. Gradient Descent
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex-1 bg-white dark:bg-[#13151a] p-8 relative flex flex-col justify-center items-center">
                <div className="absolute top-4 right-4 flex gap-2">
                  <div className="bg-black/30 backdrop-blur px-3 py-1 rounded text-xs text-white font-mono flex items-center gap-2 border border-white/10">
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>{" "}
                    REC (Narration)
                  </div>
                </div>
                <div className="w-full max-w-2xl bg-white dark:bg-surface-dark aspect-video rounded-xl shadow-2xl border border-gray-200 dark:border-white/10 p-8 flex flex-col relative overflow-hidden">
                  <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:20px_20px]"></div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white font-display mb-2 relative z-10">
                    Backpropagation Logic
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-8 max-w-md relative z-10">
                    Calculating the gradient of the loss function with respect
                    to the weights.
                  </p>
                  <div className="flex-1 flex items-center justify-center gap-4 relative z-10">
                    <div className="p-3 bg-indigo-500/10 border border-indigo-500/40 rounded text-xs text-indigo-300 font-mono w-24 text-center">
                      Input Layer
                    </div>
                    <div className="h-0.5 w-8 bg-gray-600"></div>
                    <div className="p-3 bg-purple-500/10 border border-purple-500/40 rounded text-xs text-purple-300 font-mono w-24 text-center ring-2 ring-purple-500/50 ring-offset-2 ring-offset-black animate-pulse">
                      Hidden Layer
                    </div>
                    <div className="h-0.5 w-8 bg-gray-600"></div>
                    <div className="p-3 bg-gray-800 border border-gray-700 rounded text-xs text-gray-500 font-mono w-24 text-center border-dashed">
                      Output
                    </div>
                  </div>
                  <div className="absolute top-1/2 left-1/2 transform translate-x-4 translate-y-4">
                    <span className="material-symbols-outlined text-primary text-2xl drop-shadow-lg">
                      near_me
                    </span>
                    <div className="bg-primary text-white text-[10px] px-2 py-0.5 rounded ml-4 mt-[-10px]">
                      Generating Diagram...
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="py-24 bg-gray-50 dark:bg-[#0b0c0f]">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold font-display text-gray-900 dark:text-white mb-4">
              How GYANOVA Teaches
            </h2>
            <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              A pedagogical approach designed for deep understanding.
            </p>
          </div>
          <div className="relative grid md:grid-cols-4 gap-8">
            <div className="hidden md:block absolute top-12 left-[12%] right-[12%] h-0.5 bg-gradient-to-r from-transparent via-indigo-500/30 to-transparent border-t border-dashed border-indigo-500/50 z-0"></div>

            <div className="relative z-10 text-center group">
              <div className="w-20 h-20 mx-auto bg-white dark:bg-surface-dark border border-gray-200 dark:border-white/10 rounded-full flex items-center justify-center shadow-lg mb-6 group-hover:border-primary/50 transition-colors duration-300">
                <span className="material-symbols-outlined text-3xl text-gray-400 group-hover:text-primary transition-colors">
                  psychology
                </span>
              </div>
              <div className="bg-white dark:bg-surface-dark border border-gray-200 dark:border-white/5 p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                <div className="text-primary font-mono text-sm mb-2 font-bold">
                  01. UNDERSTAND
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                  Analyze the Topic
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Your tutor scans the subject matter to identify core concepts and prerequisites.
                </p>
              </div>
            </div>

            <div className="relative z-10 text-center group">
              <div className="w-20 h-20 mx-auto bg-white dark:bg-surface-dark border border-gray-200 dark:border-white/10 rounded-full flex items-center justify-center shadow-lg mb-6 group-hover:border-secondary/50 transition-colors duration-300">
                <span className="material-symbols-outlined text-3xl text-gray-400 group-hover:text-secondary transition-colors">
                  account_tree
                </span>
              </div>
              <div className="bg-white dark:bg-surface-dark border border-gray-200 dark:border-white/5 p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                <div className="text-secondary font-mono text-sm mb-2 font-bold">
                  02. STRUCTURE
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                  Logical Flow
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Breaks complex ideas into a logical curriculum tree, ensuring smooth scaffolding.
                </p>
              </div>
            </div>

            <div className="relative z-10 text-center group">
              <div className="w-20 h-20 mx-auto bg-white dark:bg-surface-dark border border-gray-200 dark:border-white/10 rounded-full flex items-center justify-center shadow-lg mb-6 group-hover:border-pink-500/50 transition-colors duration-300">
                <span className="material-symbols-outlined text-3xl text-gray-400 group-hover:text-pink-500 transition-colors">
                  record_voice_over
                </span>
              </div>
              <div className="bg-white dark:bg-surface-dark border border-gray-200 dark:border-white/5 p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                <div className="text-pink-500 font-mono text-sm mb-2 font-bold">
                  03. TEACH
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                  Step-by-Step
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Explains each concept clearly with synced narration and generated diagrams.
                </p>
              </div>
            </div>

            <div className="relative z-10 text-center group">
              <div className="w-20 h-20 mx-auto bg-white dark:bg-surface-dark border border-gray-200 dark:border-white/10 rounded-full flex items-center justify-center shadow-lg mb-6 group-hover:border-blue-500/50 transition-colors duration-300">
                <span className="material-symbols-outlined text-3xl text-gray-400 group-hover:text-blue-500 transition-colors">
                  chat
                </span>
              </div>
              <div className="bg-white dark:bg-surface-dark border border-gray-200 dark:border-white/5 p-6 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                <div className="text-blue-500 font-mono text-sm mb-2 font-bold">
                  04. ADAPT
                </div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                  Interactive
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Stops to check your understanding and answers your specific questions instantly.
                </p>
              </div>
            </div>

          </div>
        </div>
      </section>
      <section className="py-24 overflow-hidden dark:bg-background-dark relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="mb-12">
            <h2 className="text-3xl md:text-5xl font-bold font-display text-gray-900 dark:text-white mb-4">
              More Than Content Generation
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              The difference between a tool that writes and a tutor that teaches.
            </p>
          </div>

          <BentoGrid className="max-w-4xl mx-auto mb-16">
            <BentoGridItem
              title="Curriculum-Level Reasoning"
              description="Most AI generates disconnected paragraphs. GYANOVA understands the pedagogical arc."
              header={
                <div className="flex flex-1 w-full h-full min-h-[6rem] rounded-xl bg-surface-dark border border-white/10 relative overflow-hidden group/visual">
                  <div className="absolute inset-x-0 bottom-0 top-1/2 bg-gradient-to-t from-surface-dark to-transparent z-10" />
                  <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
                  <div className="absolute top-4 left-4 right-4 flex flex-col gap-2 z-20">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-primary" />
                      <div className="h-1 w-16 bg-primary/20 rounded-full" />
                    </div>
                    <div className="flex flex-col gap-2 ml-4 border-l border-white/10 pl-4 py-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-secondary" />
                        <div className="h-1 w-12 bg-secondary/20 rounded-full" />
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-gray-600" />
                        <div className="h-1 w-10 bg-gray-600/20 rounded-full" />
                      </div>
                    </div>
                  </div>
                </div>
              }
              className="md:col-span-2"
              icon={<span className="material-symbols-outlined text-neutral-500">psychology</span>}
            />
            <BentoGridItem
              title="Synced Teaching Narration"
              description="Structured explanations, not just text-to-speech. The tutor pauses for emphasis."
              header={
                <div className="flex flex-1 w-full h-full min-h-[6rem] rounded-xl bg-surface-dark border border-white/10 relative overflow-hidden flex items-center justify-center">
                  <div className="flex gap-1 items-end h-8">
                    {[40, 70, 100, 30, 80, 50, 90, 60, 40, 70].map((height, i) => (
                      <div key={i} className={`w-1 bg-pink-500 rounded-full animate-pulse`} style={{ height: `${height}%`, animationDelay: `${i * 0.1}s` }} />
                    ))}
                  </div>
                  <div className="absolute bottom-2 right-2 flex items-center gap-1 bg-black/40 px-2 py-0.5 rounded text-[10px] text-white/50 font-mono">
                    <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" /> REC
                  </div>
                </div>
              }
              className="md:col-span-1"
              icon={<span className="material-symbols-outlined text-neutral-500">record_voice_over</span>}
            />
            <BentoGridItem
              title="Concept-Aware Visuals"
              description="Visuals generated to explain specific relationships and flows."
              header={
                <div className="flex flex-1 w-full h-full min-h-[6rem] rounded-xl bg-surface-dark border border-white/10 relative overflow-hidden flex items-center justify-center">
                  <div className="relative flex flex-col items-center gap-2 scale-75">
                    <div className="w-16 h-8 border border-secondary/50 bg-secondary/10 rounded flex items-center justify-center text-[8px] text-secondary">Start</div>
                    <div className="h-4 w-0.5 bg-gray-700" />
                    <div className="w-16 h-8 border border-white/10 bg-white/5 rounded flex items-center justify-center text-[8px] text-gray-400 rotate-45">Decision</div>
                  </div>
                  <div className="absolute top-2 left-2 text-[10px] text-white/30 font-mono">FIG. 1.2</div>
                </div>
              }
              className="md:col-span-1"
              icon={<span className="material-symbols-outlined text-neutral-500">account_tree</span>}
            />
            <BentoGridItem
              title="Progress-Aware Tutoring"
              description="The AI tutor tracks what you know and adapts. It doesn't move on until you understand."
              header={
                <div className="flex flex-1 w-full h-full min-h-[6rem] rounded-xl bg-surface-dark border border-white/10 relative overflow-hidden p-4 font-mono text-[10px]">
                  <div className="text-gray-500 mb-2">// Tutor Log</div>
                  <div className="text-green-400">$ analyzing_response...</div>
                  <div className="text-yellow-400 ml-2">warn: student_hesitation_detected</div>
                  <div className="text-blue-400 ml-2">action: trigger_simplification_routine</div>
                  <div className="text-gray-500 mt-2">-- adjusting difficulty --</div>
                </div>
              }
              className="md:col-span-2"
              icon={<span className="material-symbols-outlined text-neutral-500">touch_app</span>}
            />
          </BentoGrid>

          <div className="grid md:grid-cols-2 bg-surface-dark border border-white/10 rounded-xl overflow-hidden text-sm">
            <div className="p-8 border-b md:border-b-0 md:border-r border-white/10">
              <h4 className="text-gray-400 font-bold mb-6 tracking-wide uppercase">Generic AI Tools</h4>
              <ul className="space-y-4 text-gray-500">
                <li className="flex gap-3"><span className="material-symbols-outlined text-red-900">close</span> Disconnected explanations</li>
                <li className="flex gap-3"><span className="material-symbols-outlined text-red-900">close</span> No clear learning path</li>
                <li className="flex gap-3"><span className="material-symbols-outlined text-red-900">close</span> Static text or weird images</li>
              </ul>
            </div>
            <div className="p-8 bg-white/5">
              <h4 className="text-primary font-bold mb-6 tracking-wide uppercase">GYANOVA</h4>
              <ul className="space-y-4 text-white">
                <li className="flex gap-3"><span className="material-symbols-outlined text-green-500">check</span> Logical curriculum progression</li>
                <li className="flex gap-3"><span className="material-symbols-outlined text-green-500">check</span> Concept-aware explanatory visuals</li>
                <li className="flex gap-3"><span className="material-symbols-outlined text-green-500">check</span> Interactive tutor behavior</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-indigo-900/10 border-y border-white/5 relative overflow-hidden">
        <div className="absolute inset-0 grid-bg opacity-20 pointer-events-none"></div>
        <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
          <div className="inline-block p-12 bg-surface-dark border border-white/10 rounded-2xl shadow-2xl max-w-2xl w-full text-left">
            <div className="flex gap-4 mb-6">
              <div className="w-10 h-10 rounded-full bg-gray-700 flex-shrink-0"></div>
              <div className="bg-gray-800 p-4 rounded-r-xl rounded-bl-xl text-gray-300 text-sm">
                Wait, I don&apos;t understand why the error propagates backwards?
              </div>
            </div>
            <div className="flex gap-4 flex-row-reverse">
              <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center flex-shrink-0 text-white font-bold">G</div>
              <div className="bg-primary/20 border border-primary/30 p-4 rounded-l-xl rounded-br-xl text-white text-sm">
                <TextGenerateEffect
                  words="Think of it like blaming the specific ingredients for a bad cake. We taste the final cake (Output), find it's too salty (Error), and then go back to the recipe to see exactly how much salt we added."
                  className="text-sm font-normal text-white"
                />
                <br />
                <span className="text-primary-300">Would you like to try a simulation of this?</span>
              </div>
            </div>
          </div>
          <div className="mt-12">
            <h2 className="text-3xl font-display font-bold text-white mb-2">Ask. Explore. Understand.</h2>
            <p className="text-gray-400">Real-time clarification whenever you get stuck.</p>
          </div>
        </div>
      </section>
      <section className="py-24 bg-[#050608] border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold font-display text-white mb-4">
              Visual Intelligence Gallery
            </h2>
            <p className="text-gray-400">
              These visuals are generated to teach, not decorate.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            <CardContainer className="inter-var">
              <CardBody className="bg-gray-50 relative group/card  dark:hover:shadow-2xl dark:hover:shadow-emerald-500/[0.1] dark:bg-black dark:border-white/[0.2] border-black/[0.1] w-auto sm:w-[30rem] h-auto rounded-xl p-6 border  ">
                <CardItem translateZ="50" className="text-xl font-bold text-neutral-600 dark:text-white">
                  Evolutionary Timeline
                </CardItem>
                <CardItem as="p" translateZ="60" className="text-neutral-500 text-sm max-w-sm mt-2 dark:text-neutral-300">
                  Auto-generated for historical or process topics.
                </CardItem>
                <CardItem translateZ="100" className="w-full mt-4">
                  <div className="aspect-[4/3] bg-black/50 p-6 flex items-center justify-center rounded-xl">
                    <div className="flex flex-col items-center gap-4 w-full px-4">
                      <div className="w-full h-0.5 bg-gray-700 relative">
                        <div className="absolute left-[20%] top-[-4px] w-2 h-2 rounded-full bg-primary"></div>
                        <div className="absolute left-[50%] top-[-4px] w-2 h-2 rounded-full bg-gray-500"></div>
                        <div className="absolute left-[80%] top-[-4px] w-2 h-2 rounded-full bg-gray-500"></div>
                      </div>
                      <div className="grid grid-cols-3 w-full text-center gap-2">
                        <div className="text-[10px] text-primary">2010</div>
                        <div className="text-[10px] text-gray-500">2015</div>
                        <div className="text-[10px] text-gray-500">2020</div>
                      </div>
                    </div>
                  </div>
                </CardItem>
              </CardBody>
            </CardContainer>
            <CardContainer className="inter-var">
              <CardBody className="bg-gray-50 relative group/card  dark:hover:shadow-2xl dark:hover:shadow-emerald-500/[0.1] dark:bg-black dark:border-white/[0.2] border-black/[0.1] w-auto sm:w-[30rem] h-auto rounded-xl p-6 border  ">
                <CardItem translateZ="50" className="text-xl font-bold text-neutral-600 dark:text-white">
                  System Architecture Flowchart
                </CardItem>
                <CardItem as="p" translateZ="60" className="text-neutral-500 text-sm max-w-sm mt-2 dark:text-neutral-300">
                  Visualizes logic flows and technical systems.
                </CardItem>
                <CardItem translateZ="100" className="w-full mt-4">
                  <div className="aspect-[4/3] bg-black/50 p-6 flex items-center justify-center rounded-xl">
                    <div className="flex flex-col items-center gap-2">
                      <div className="w-20 h-8 border border-secondary text-secondary text-[10px] flex items-center justify-center rounded">Start</div>
                      <div className="h-4 w-0.5 bg-gray-700"></div>
                      <div className="w-20 h-8 border border-white/20 text-gray-400 text-[10px] flex items-center justify-center rounded rotate-45 transform bg-surface-dark z-10">Decision</div>
                    </div>
                  </div>
                </CardItem>
              </CardBody>
            </CardContainer>
            <CardContainer className="inter-var">
              <CardBody className="bg-gray-50 relative group/card  dark:hover:shadow-2xl dark:hover:shadow-emerald-500/[0.1] dark:bg-black dark:border-white/[0.2] border-black/[0.1] w-auto sm:w-[30rem] h-auto rounded-xl p-6 border  ">
                <CardItem translateZ="50" className="text-xl font-bold text-neutral-600 dark:text-white">
                  Concept Comparison
                </CardItem>
                <CardItem as="p" translateZ="60" className="text-neutral-500 text-sm max-w-sm mt-2 dark:text-neutral-300">
                  Automatically contrasts multiple entities or ideas.
                </CardItem>
                <CardItem translateZ="100" className="w-full mt-4">
                  <div className="aspect-[4/3] bg-black/50 p-6 flex items-center justify-center rounded-xl">
                    <div className="w-full h-full border border-white/10 rounded flex flex-col text-[10px] text-gray-400">
                      <div className="flex border-b border-white/10 bg-white/5"><div className="flex-1 p-2 border-r border-white/10">Concept</div><div className="flex-1 p-2">Pros</div></div>
                      <div className="flex border-b border-white/10"><div className="flex-1 p-2 border-r border-white/10 text-white">React</div><div className="flex-1 p-2">Ecosystem</div></div>
                      <div className="flex"><div className="flex-1 p-2 border-r border-white/10 text-white">Vue</div><div className="flex-1 p-2">Simplicity</div></div>
                    </div>
                  </div>
                </CardItem>
              </CardBody>
            </CardContainer>
          </div>
        </div>
      </section>
      <section className="py-20 bg-white dark:bg-background-dark border-t border-gray-100 dark:border-white/5">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl md:text-5xl font-bold font-display text-gray-900 dark:text-white mb-6">
            Ready to learn?
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-10">
            Join forward-thinking students and educators experiencing the future of learning with GYANOVA.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link href="/lesson/new">
              <Button
                borderRadius="1.75rem"
                containerClassName="hover:scale-105 transition-transform duration-200"
                className="bg-white dark:bg-background-dark text-gray-900 dark:text-white font-semibold border-neutral-200 dark:border-slate-800"
              >
                Start Learning
              </Button>
            </Link>
          </div>
          <p className="mt-6 text-sm text-gray-500 dark:text-gray-500">
            No credit card required. 14-day free trial.
          </p>
        </div>
      </section>
      <footer className="bg-gray-50 dark:bg-[#050608] border-t border-gray-200 dark:border-white/5 pt-16 pb-8">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8 mb-12">
            <div className="col-span-2 lg:col-span-2">
              <a href="#" className="flex items-center space-x-2 mb-6">
                <div className="w-8 h-8 rounded bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white font-bold font-display text-lg">
                  G
                </div>
                <span className="self-center text-xl font-bold whitespace-nowrap font-display tracking-tight dark:text-white">
                  GYANOVA
                </span>
              </a>
              <p className="text-gray-500 text-sm mb-6 max-w-xs">
                Empowering the next generation of knowledge creators with
                AI-driven tools that respect your workflow.
              </p>
              <div className="flex space-x-4">
                <a
                  href="#"
                  className="text-gray-400 hover:text-primary transition-colors"
                >
                  <span className="sr-only">Twitter</span>
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"></path>
                  </svg>
                </a>
                <a
                  href="#"
                  className="text-gray-400 hover:text-primary transition-colors"
                >
                  <span className="sr-only">GitHub</span>
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path
                      clipRule="evenodd"
                      d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                      fillRule="evenodd"
                    ></path>
                  </svg>
                </a>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Product
              </h3>
              <ul className="space-y-3">
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    Integrations
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    Pricing
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    Changelog
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Resources
              </h3>
              <ul className="space-y-3">
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    Documentation
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    API Reference
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    Community
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    Help Center
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-wider mb-4">
                Company
              </h3>
              <ul className="space-y-3">
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    About
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    Blog
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    Careers
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-500 hover:text-primary transition-colors text-sm"
                  >
                    Legal
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-200 dark:border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400 text-sm">
              © 2024 GYANOVA Inc. All rights reserved.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <a href="#" className="text-gray-400 hover:text-white text-sm">
                Privacy Policy
              </a>
              <a href="#" className="text-gray-400 hover:text-white text-sm">
                Terms of Service
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
