'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/services/authService';
import { LayoutDashboard, History, Settings, LogOut, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [engineState, setEngineState] = useState({ running: false, starting: false });
    const router = useRouter();

    useEffect(() => {
        async function checkAuth() {
            try {
                const userData = await authService.whoami();
                setUser(userData);
            } catch (_e) {
                router.push('/login');
            } finally {
                setLoading(false);
            }
        }
        checkAuth();

        // Poll for engine status
        const pollEngine = async () => {
            try {
                const { tradingService } = await import('@/services/tradingService');
                const state = await tradingService.getState();
                setEngineState({ running: state.running, starting: state.starting });
            } catch (_e) { }
        };
        pollEngine();
        const interval = setInterval(pollEngine, 5000);
        return () => clearInterval(interval);
    }, [router]);

    const handleLogout = async () => {
        await authService.logout();
        router.push('/login');
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white flex">
            {/* Sidebar */}
            <aside className="w-64 border-r border-white/5 bg-[#0d0d0d] hidden md:flex flex-col">
                <div className="p-6">
                    <h2 className="text-xl font-bold bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
                        TRADING BOT V2
                    </h2>
                </div>

                <nav className="flex-1 px-4 space-y-2">
                    <Link
                        href="/dashboard"
                        className="flex items-center space-x-3 px-4 py-3 rounded-xl bg-blue-600/10 text-blue-500 font-medium transition-colors"
                    >
                        <LayoutDashboard size={20} />
                        <span>Dashboard</span>
                    </Link>
                    <Link
                        href="/dashboard/history"
                        className="flex items-center space-x-3 px-4 py-3 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
                    >
                        <History size={20} />
                        <span>History</span>
                    </Link>
                    <Link
                        href="/dashboard/settings"
                        className="flex items-center space-x-3 px-4 py-3 rounded-xl hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
                    >
                        <Settings size={20} />
                        <span>Settings</span>
                    </Link>
                </nav>

                <div className="p-4 border-t border-white/5">
                    <div className="bg-white/5 rounded-2xl p-4 mb-4">
                        <p className="text-xs text-gray-500 uppercase font-bold tracking-wider mb-2">Connected User</p>
                        <p className="font-medium text-gray-200">{user?.username}</p>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-xl text-red-500 hover:bg-red-500/10 transition-colors"
                    >
                        <LogOut size={18} />
                        <span>Sign Out</span>
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col h-screen overflow-hidden">
                <header className="h-16 border-b border-white/5 flex items-center px-8 justify-between bg-[#0d0d0d]">
                    <h1 className="text-lg font-medium text-gray-300">Market Overview</h1>
                    <div className="flex items-center space-x-4 text-sm">
                        <div className="flex items-center space-x-2">
                            <span className={`w-2 h-2 rounded-full ${engineState.running ? 'bg-green-500 animate-pulse' : engineState.starting ? 'bg-yellow-500 animate-bounce' : 'bg-red-500'}`}></span>
                            <span className="text-gray-400">
                                {engineState.running ? 'Engine Live' : engineState.starting ? 'Connecting...' : 'Engine Offline'}
                            </span>
                        </div>
                        <div className="h-4 w-px bg-white/10"></div>
                        <span className="text-gray-500">v2.1.0</span>
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto p-8 relative">
                    {children}
                </div>
            </main>
        </div>
    );
}
