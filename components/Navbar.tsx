"use client";

import Link from "next/link";
import { useSession, signIn, signOut } from "next-auth/react";
import Image from "next/image";

export function Navbar() {
    const { data: session } = useSession();

    return (
        <nav className="fixed w-full z-50 top-0 start-0 border-b border-gray-200 dark:border-white/5 bg-white/80 dark:bg-background-dark/80 backdrop-blur-md">
            <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between px-6 py-4">
                <Link href="/" className="flex items-center space-x-2 rtl:space-x-reverse">
                    <div className="w-8 h-8 rounded bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white font-bold font-display text-lg">
                        G
                    </div>
                    <span className="self-center text-xl font-bold whitespace-nowrap font-display tracking-tight dark:text-white">
                        GYANOVA
                    </span>
                </Link>
                <div className="flex md:order-2 space-x-3 md:space-x-4 rtl:space-x-reverse items-center">
                    {session ? (
                        <div className="flex items-center gap-4">
                            <div className="text-sm text-gray-300 hidden sm:block">
                                Hi, {session.user?.name?.split(' ')[0]}
                            </div>
                            {session.user?.image ? (
                                <Image
                                    src={session.user.image}
                                    alt="Profile"
                                    width={32}
                                    height={32}
                                    className="rounded-full border border-white/10"
                                />
                            ) : (
                                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                                    {session.user?.name?.[0] || "U"}
                                </div>
                            )}
                            <button
                                onClick={() => signOut()}
                                className="text-sm text-gray-400 hover:text-white transition-colors"
                            >
                                Sign Out
                            </button>
                            <Link
                                href="/lesson/new"
                                className="text-white bg-primary hover:bg-indigo-600 focus:ring-4 focus:outline-none focus:ring-indigo-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:focus:ring-indigo-800 transition-all shadow-[0_0_15px_rgba(99,102,241,0.5)] hover:shadow-[0_0_25px_rgba(99,102,241,0.6)]"
                            >
                                New Lesson
                            </Link>
                        </div>
                    ) : (
                        <button
                            onClick={() => signIn("credentials")}
                            className="text-white bg-primary hover:bg-indigo-600 focus:ring-4 focus:outline-none focus:ring-indigo-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:focus:ring-indigo-800 transition-all shadow-[0_0_15px_rgba(99,102,241,0.5)] hover:shadow-[0_0_25px_rgba(99,102,241,0.6)]"
                        >
                            Sign In (Demo Account)
                        </button>
                    )}

                    <button
                        data-collapse-toggle="navbar-sticky"
                        type="button"
                        className="inline-flex items-center p-2 w-10 h-10 justify-center text-sm text-gray-500 rounded-lg md:hidden hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200 dark:text-gray-400 dark:hover:bg-gray-700 dark:focus:ring-gray-600"
                        aria-controls="navbar-sticky"
                        aria-expanded="false"
                    >
                        <span className="sr-only">Open main menu</span>
                        <span className="material-symbols-outlined">menu</span>
                    </button>
                </div>
                <div
                    className="items-center justify-between hidden w-full md:flex md:w-auto md:order-1"
                    id="navbar-sticky"
                >
                    <ul className="flex flex-col p-4 md:p-0 mt-4 font-medium border border-gray-100 rounded-lg bg-gray-50 md:space-x-8 rtl:space-x-reverse md:flex-row md:mt-0 md:border-0 md:bg-white dark:bg-gray-800 md:dark:bg-transparent dark:border-gray-700">
                        <li>
                            <Link
                                href="/"
                                className="block py-2 px-3 text-white bg-primary rounded md:bg-transparent md:text-primary md:p-0 dark:text-white md:dark:text-primary"
                                aria-current="page"
                            >
                                Product
                            </Link>
                        </li>
                        <li>
                            <Link
                                href="#"
                                className="block py-2 px-3 text-gray-900 rounded hover:bg-gray-100 md:hover:bg-transparent md:hover:text-primary md:p-0 md:dark:hover:text-primary dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-white md:dark:hover:bg-transparent dark:border-gray-700"
                            >
                                Solutions
                            </Link>
                        </li>
                        <li>
                            <Link
                                href="#"
                                className="block py-2 px-3 text-gray-900 rounded hover:bg-gray-100 md:hover:bg-transparent md:hover:text-primary md:p-0 md:dark:hover:text-primary dark:text-gray-400 dark:hover:bg-gray-700 dark:hover:text-white md:dark:hover:bg-transparent dark:border-gray-700"
                            >
                                Pricing
                            </Link>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
    );
}
