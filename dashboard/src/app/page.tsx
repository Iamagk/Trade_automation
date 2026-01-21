"use strict";
"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  LineChart,
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  ShoppingBag,
  Clock,
  LogOut,
  RefreshCcw,
  Square,
  Settings,
  ShieldCheck,
  Zap
} from "lucide-react";

import { statsService } from "@/services/statsService";
import { botService } from "@/services/botService";
import { authService } from "@/services/authService";
import { BotStatus } from "@/services/types";

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [botStatus, setBotStatus] = useState<BotStatus>({ status: 'IDLE', mode: null, pid: null, startTime: null, logCount: 0 });
  const [botLogs, setBotLogs] = useState<string[]>([]);
  const [requestToken, setRequestToken] = useState("");
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        await authService.whoami();
        setLoading(false);
      } catch (err) {
        // Interceptor will redirect, but just in case:
        router.push('/login');
      }
    };
    checkAuth();
  }, [router]);

  const fetchStats = async () => {
    try {
      const data = await statsService.getStats();
      setStats(data);
    } catch (err: any) {
      console.error("Failed to fetch stats", err);
      // Auth errors handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  const fetchBotStatus = async () => {
    try {
      const status = await botService.getStatus();
      setBotStatus(status);
    } catch (err) {
      console.error("Failed to fetch bot status", err);
    }
  };

  const fetchBotLogs = async () => {
    try {
      const data = await botService.getLogs();
      setBotLogs(data.logs);

      if (logContainerRef.current) {
        logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
      }
    } catch (err) {
      console.error("Failed to fetch bot logs", err);
    }
  };

  const handleBotAction = async (action: string, mode?: string) => {
    try {
      if (action === "start" && mode) {
        await botService.startBot(mode);
      } else {
        await botService.stopBot();
      }
      fetchBotStatus();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message || "Action failed");
    }
  };

  const handleSendInput = async () => {
    if (!requestToken) return;

    try {
      await botService.sendInput(requestToken);
      setRequestToken("");
      alert("Token sent to bot");
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message || "Failed to send token");
    }
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
      router.push("/login");
    } catch (e) {
      console.error("Logout failed", e);
      router.push("/login"); // Force redirect
    }
  };

  useEffect(() => {
    // Initial check
    fetchStats();
    fetchBotStatus();

    const statusInterval = setInterval(fetchBotStatus, 3000);

    // Poll logs if running
    let logsInterval: any;
    if (botStatus.status === 'RUNNING') {
      fetchBotLogs();
      logsInterval = setInterval(fetchBotLogs, 2000);
    } else {
      fetchBotLogs();
    }

    return () => {
      clearInterval(statusInterval);
      if (logsInterval) clearInterval(logsInterval);
    };
  }, [botStatus.status]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white font-sans p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Trading Dashboard</h1>
            <p className="text-gray-400">Welcome back, Client</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={fetchStats}
              className="flex items-center gap-2 px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg hover:bg-gray-800 transition-all text-sm"
            >
              <RefreshCcw className="w-4 h-4" /> Refresh
            </button>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 bg-red-900/20 border border-red-500/30 text-red-400 rounded-lg hover:bg-red-900/30 transition-all text-sm"
            >
              <LogOut className="w-4 h-4" /> Logout
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <Link href="/trades" className="p-6 bg-gray-900 rounded-2xl border border-gray-800 shadow-lg group hover:border-blue-500/50 transition-all cursor-pointer overflow-hidden relative">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400">
                <ShoppingBag className="w-6 h-6" />
              </div>
              <div className="text-xs text-blue-400 opacity-0 group-hover:opacity-100 transition-all transform translate-x-4 group-hover:translate-x-0 font-medium">
                View History →
              </div>
            </div>
            <div className="text-sm text-gray-400 mb-1">Total Trades</div>
            <div className="text-3xl font-bold">{stats?.total_trades || 0}</div>
            <div className="absolute bottom-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-all transform scale-150 group-hover:scale-100">
              <ShoppingBag className="w-16 h-16" />
            </div>
          </Link>

          <Link href="/investments" className="p-6 bg-gray-900 rounded-2xl border border-gray-800 shadow-lg group hover:border-emerald-500/50 transition-all cursor-pointer overflow-hidden relative">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
                <DollarSign className="w-6 h-6" />
              </div>
              <div className="text-xs text-emerald-400 opacity-0 group-hover:opacity-100 transition-all transform translate-x-4 group-hover:translate-x-0 font-medium">
                View Portfolio →
              </div>
            </div>
            <div className="text-sm text-gray-400 mb-1">Total Investment</div>
            <div className="text-3xl font-bold">₹{stats?.total_cost?.toLocaleString() || "0.00"}</div>
            <div className="absolute bottom-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-all transform scale-150 group-hover:scale-100">
              <DollarSign className="w-16 h-16" />
            </div>
          </Link>

          <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800 shadow-lg group hover:border-purple-500/50 transition-all">
            <div className="flex justify-between items-start mb-4">
              <div className={`p-3 rounded-xl ${botStatus.status === 'RUNNING' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-500/10 text-gray-400'}`}>
                <Activity className={`w-6 h-6 ${botStatus.status === 'RUNNING' ? 'animate-pulse' : ''}`} />
              </div>
            </div>
            <div className="text-sm text-gray-400 mb-1">Active Status</div>
            <div className={`text-3xl font-bold ${botStatus.status === 'RUNNING' ? 'text-emerald-400' : 'text-gray-500'}`}>
              {botStatus.status === 'RUNNING' ? "Active" : "Idle"}
            </div>
          </div>
        </div>

        {/* Recent Screening Logs & Terminal */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3 space-y-6">
            <div className="bg-gray-900 rounded-2xl border border-gray-800 shadow-xl overflow-hidden">
              <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <LineChart className="w-5 h-5 text-blue-400" /> Recent Screening Candidates
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-gray-950 text-gray-400 text-xs uppercase">
                    <tr>
                      <th className="px-6 py-4">Symbol</th>
                      <th className="px-6 py-4">Price</th>
                      <th className="px-6 py-4">25 DMA</th>
                      <th className="px-6 py-4">Below DMA</th>
                      <th className="px-6 py-4">Rank</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {stats?.last_screening?.map((log: any) => (
                      <tr key={log.id} className="hover:bg-gray-800/50 transition-all">
                        <td className="px-6 py-4 font-semibold">{log.symbol}</td>
                        <td className="px-6 py-4 text-gray-300">₹{log.current_price.toFixed(2)}</td>
                        <td className="px-6 py-4 text-gray-400">₹{log.dma_25.toFixed(2)}</td>
                        <td className="px-6 py-4">
                          <span className="text-red-400 bg-red-400/10 px-2 py-1 rounded-md text-xs font-medium">
                            {log.percent_below_dma}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-500">#{log.rank}</td>
                      </tr>
                    ))}
                    {(!stats?.last_screening || stats.last_screening.length === 0) && (
                      <tr>
                        <td colSpan={5} className="px-6 py-10 text-center text-gray-500">
                          No screening data available yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Live Terminal */}
            <div className="bg-gray-950 rounded-2xl border border-gray-800 shadow-xl overflow-hidden">
              <div className="p-4 border-b border-gray-800 flex justify-between items-center bg-gray-900">
                <h2 className="text-sm font-bold flex items-center gap-2 text-gray-400 uppercase tracking-widest">
                  <span className={`w-2 h-2 rounded-full ${botStatus.status === 'RUNNING' ? 'bg-emerald-500 animate-pulse' : 'bg-gray-600'}`}></span>
                  Live Bot Output
                </h2>
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500/20"></div>
                  <div className="w-3 h-3 rounded-full bg-amber-500/20"></div>
                  <div className="w-3 h-3 rounded-full bg-emerald-500/20"></div>
                </div>
              </div>
              <div
                ref={logContainerRef}
                className="p-6 h-64 overflow-y-auto font-mono text-xs space-y-1.5 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent bg-black/40"
              >
                {botLogs.length > 0 ? (
                  botLogs.map((log, i) => (
                    <div key={i} className="flex gap-3 animate-in fade-in slide-in-from-left-2 duration-300">
                      <span className="text-gray-600 select-none">[{i + 1}]</span>
                      <span className="text-gray-300 break-all">{log}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-gray-600 italic">
                    {botStatus.status === 'RUNNING' ? "Capturing output..." : "Start the bot to see logs here."}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Quick Stats Sidebar */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 shadow-xl">
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-emerald-400" /> Strategy Insights
              </h2>
              <div className="space-y-4">
                <div className="p-4 bg-gray-950 rounded-xl border border-gray-800">
                  <div className="flex items-center gap-3 text-sm text-gray-400 mb-2">
                    <Clock className="w-4 h-4" /> Last Run
                  </div>
                  <div className="font-semibold">{stats?.last_screening?.[0]?.time || "Never"} - {stats?.last_screening?.[0]?.date || "N/A"}</div>
                </div>
                <div className="p-4 bg-gray-950 rounded-xl border border-gray-800">
                  <div className="flex items-center gap-3 text-sm text-gray-400 mb-2">
                    <TrendingDown className="w-4 h-4 text-red-400" /> Top Drop Today
                  </div>
                  <div className="font-semibold text-red-400">
                    {stats?.last_screening?.[0]?.symbol || "None"} ({stats?.last_screening?.[0]?.percent_below_dma || "0%"})
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 shadow-xl">
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <Settings className="w-5 h-5 text-blue-400" /> Bot Controls
              </h2>
              <div className="grid grid-cols-1 gap-3">
                {botStatus.status === 'RUNNING' ? (
                  <div className="space-y-4">
                    <button
                      onClick={() => handleBotAction("stop")}
                      className="flex items-center justify-center gap-2 w-full py-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl hover:bg-red-500/20 transition-all font-semibold"
                    >
                      <Square className="w-4 h-4" /> Stop Bot ({botStatus.mode})
                    </button>

                    {botStatus.mode === "login" && (
                      <div className="p-4 bg-gray-950 rounded-xl border border-gray-800 animate-in fade-in slide-in-from-top-2 duration-500">
                        <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                          Enter Request Token
                        </label>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={requestToken}
                            onChange={(e) => setRequestToken(e.target.value)}
                            placeholder="Paste token here..."
                            className="bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm w-full focus:outline-none focus:border-purple-500 transition-all"
                          />
                          <button
                            onClick={handleSendInput}
                            className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all"
                          >
                            Submit
                          </button>
                        </div>
                        <p className="text-[10px] text-gray-500 mt-2">
                          Copy the token from the redirected URL after logging in.
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => handleBotAction("start", "login")}
                      className="flex items-center justify-center gap-2 w-full py-3 bg-purple-500/10 border border-purple-500/30 text-purple-400 rounded-xl hover:bg-purple-500/20 transition-all text-sm font-bold"
                    >
                      <ShieldCheck className="w-4 h-4" /> Authorize Zerodha
                    </button>
                    <div className="h-px bg-gray-800 my-2"></div>
                    <button
                      onClick={() => handleBotAction("start", "run_now_dry")}
                      className="flex items-center justify-center gap-2 w-full py-3 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-xl hover:bg-blue-500/20 transition-all text-sm"
                    >
                      <Zap className="w-4 h-4" /> Immediate run (Dry Run)
                    </button>
                    <button
                      onClick={() => handleBotAction("start", "schedule_dry")}
                      className="flex items-center justify-center gap-2 w-full py-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 rounded-xl hover:bg-emerald-500/20 transition-all text-sm"
                    >
                      <Clock className="w-4 h-4" /> Daily Scheduler (Dry Run)
                    </button>
                    <div className="h-px bg-gray-800 my-2"></div>
                    <button
                      onClick={() => handleBotAction("start", "run_now_real")}
                      className="flex items-center justify-center gap-2 w-full py-3 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-xl hover:bg-amber-500/20 transition-all text-sm"
                    >
                      <ShieldCheck className="w-4 h-4" /> Immediate run (REAL)
                    </button>
                    <button
                      onClick={() => handleBotAction("start", "schedule_real")}
                      className="flex items-center justify-center gap-2 w-full py-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl hover:bg-rose-500/20 transition-all text-sm"
                    >
                      <ShieldCheck className="w-4 h-4" /> Daily Scheduler (REAL)
                    </button>
                  </>
                )}
              </div>
            </div>

            <div className={`bg-gradient-to-br transition-all duration-500 ${botStatus.status === 'RUNNING' ? 'from-emerald-600 to-blue-600' : 'from-gray-700 to-gray-800'} rounded-2xl p-6 shadow-xl relative overflow-hidden`}>
              <div className="relative z-10 text-white">
                <h3 className="text-lg font-bold mb-2">System Status</h3>
                <p className="text-sm text-blue-100 mb-4 opacity-90">
                  {botStatus.status === 'RUNNING'
                    ? `The bot is currently running in ${botStatus.mode} mode.`
                    : "The bot is currently idle. Start a run from the controls above."}
                </p>
                <div className={`flex items-center gap-2 text-xs font-mono uppercase tracking-widest bg-black/20 w-fit px-3 py-1 rounded-full border border-white/10`}>
                  <span className={`w-2 h-2 rounded-full ${botStatus.status === 'RUNNING' ? 'bg-emerald-400 animate-pulse' : 'bg-gray-400'}`}></span>
                  {botStatus.status === 'RUNNING' ? "Active" : "Idle"}
                </div>
              </div>
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <Activity className="w-24 h-24" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
