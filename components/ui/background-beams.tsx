"use client";
import React from "react";
import { cn } from "@/lib/utils";

export const BackgroundBeams = ({ className }: { className?: string }) => {
    const canvasRef = React.useRef<HTMLCanvasElement>(null);

    React.useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        let animationFrameId: number;

        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        window.addEventListener("resize", resizeCanvas);
        resizeCanvas();

        const paths: {
            x: number;
            y: number;
            radius: number;
            angle: number;
            speed: number;
            color: string;
        }[] = [];

        // Create more paths for a denser effect
        for (let i = 0; i < 40; i++) {
            paths.push({
                x: Math.random() * window.innerWidth,
                y: Math.random() * window.innerHeight,
                radius: Math.random() * 2 + 1,
                angle: Math.random() * Math.PI * 2,
                speed: Math.random() * 0.5 + 0.1,
                color: `rgba(${Math.floor(Math.random() * 100 + 100)}, ${Math.floor(Math.random() * 100 + 100)}, 255, ${Math.random() * 0.5 + 0.1})`,
            });
        }

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            paths.forEach((path) => {
                path.x += Math.cos(path.angle) * path.speed;
                path.y += Math.sin(path.angle) * path.speed;
                path.angle += Math.random() * 0.02 - 0.01; // Slightly change direction

                // Wrap around screen
                if (path.x > canvas.width) path.x = 0;
                if (path.x < 0) path.x = canvas.width;
                if (path.y > canvas.height) path.y = 0;
                if (path.y < 0) path.y = canvas.height;

                ctx.beginPath();
                ctx.arc(path.x, path.y, path.radius, 0, Math.PI * 2);
                ctx.fillStyle = path.color;
                ctx.fill();

                // Draw trailing effect (beams)
                const length = Math.random() * 100 + 50;
                ctx.beginPath();
                ctx.moveTo(path.x, path.y);
                ctx.lineTo(path.x - Math.cos(path.angle) * length, path.y - Math.sin(path.angle) * length);
                const gradient = ctx.createLinearGradient(path.x, path.y, path.x - Math.cos(path.angle) * length, path.y - Math.sin(path.angle) * length);
                gradient.addColorStop(0, path.color.replace(/[\d.]+\)$/g, '0.3)'));
                gradient.addColorStop(1, 'transparent');
                ctx.strokeStyle = gradient;
                ctx.lineWidth = path.radius / 2;
                ctx.stroke();

            });

            animationFrameId = requestAnimationFrame(animate);
        };

        animate();

        return () => {
            window.removeEventListener("resize", resizeCanvas);
            cancelAnimationFrame(animationFrameId);
        };
    }, []);

    return (
        <div
            className={cn(
                "absolute inset-0 z-0 h-full w-full pointer-events-none opacity-40 mix-blend-screen",
                className
            )}
        >
            <canvas ref={canvasRef} className="absolute inset-0 h-full w-full"></canvas>
        </div>
    );
};
