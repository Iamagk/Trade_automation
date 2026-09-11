'use client';

import { useEffect, useState } from 'react';
import { tradingService } from '@/services/tradingService';
import {
    TrendingUp,
    Activity,
    BarChart3,
    Clock,
    Play,
    Square,
    RefreshCw,
    AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import MarketChart from '@/components/MarketChart';

export default function DashboardPage() {
    const [state, setState] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [refreshing, setRefreshing] = useState(false);

    const fetchData = async () => {
        setRefreshing(true);
        try {
            const [stateData, historyData] = await Promise.all([
                tradingService.getState(),
                tradingService.getHistory()
            ]);
            setState(stateData);
            setHistory(historyData);
            setError('');
        } catch (_err) {
            setError('Connection to engine lost. Retrying...');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleCommand = async (command: string) => {
        try {
            await tradingService.sendCommand(command);
            fetchData();
        } catch (_err) {
            alert('Failed to send command');
        }
    };

    const handleToggleSimulation = async (enabled: boolean) => {
        try {
            await tradingService.toggleSimulation(enabled);
            fetchData();
        } catch (_err) {
            alert('Failed to toggle simulation mode');
        }
    };


    if (loading) return null;

    const pnl = state?.pnl || 0;
    const isPnlPositive = pnl >= 0;

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-12">
            {/* Header Info */}
            <AnimatePresence>
                {error && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="bg-red-500/10 border border-red-500/20 text-red-500 px-4 py-2 rounded-xl text-sm flex items-center space-x-2"
                    >
                        <AlertCircle size={16} />
                        <span>{error}</span>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatusCard
                    title="Daily P&L"
                    value={`₹${pnl.toLocaleString()}`}
                    trend={isPnlPositive ? '+2.4%' : '-1.2%'}
                    isPositive={isPnlPositive}
                    icon={<TrendingUp size={20} />}
                />
                <StatusCard
                    title="Open Positions"
                    value={state?.positions?.length || 0}
                    trend="Live"
                    isPositive={true}
                    icon={<Activity size={20} />}
                />
                <StatusCard
                    title="Total Capital"
                    value="₹1,00,000"
                    trend="Locked"
                    isPositive={true}
                    icon={<BarChart3 size={20} />}
                />
                <StatusCard
                    title="Execution Type"
                    value={state?.strategy || 'TPB Trend'}
                    trend="Active"
                    isPositive={true}
                    icon={<Clock size={20} />}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Control Panel */}
                <div className="lg:col-span-2 space-y-8">
                    <div className="bg-[#141414] rounded-3xl p-8 border border-white/5 relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-8">
                            <RefreshCw className={`text-blue-500/40 ${refreshing ? 'animate-spin' : ''}`} size={24} />
                        </div>

                        <h3 className="text-xl font-bold mb-6 flex items-center space-x-2">
                            <Play className="text-blue-500" size={20} fill="currentColor" />
                            <span>Strategy Controls</span>
                        </h3>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <ControlButton
                                onClick={() => handleCommand('START')}
                                active={!state?.running && !state?.starting}
                                starting={state?.starting}
                                variant="primary"
                                label={state?.starting ? "Connecting..." : "Start Engine"}
                                subLabel="Initialize websocket & data stream"
                                icon={state?.starting ? <RefreshCw className="animate-spin" size={20} /> : <Play size={20} />}
                            />
                            <ControlButton
                                onClick={() => handleCommand('STOP')}
                                active={state?.running}
                                variant="danger"
                                label="Stop Engine"
                                subLabel="Halt all future trade executions"
                                icon={<Square size={20} />}
                            />
                        </div>

                        <div className="mt-8 pt-8 border-t border-white/5">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h4 className="font-bold text-gray-200">Dry Run Mode</h4>
                                    <p className="text-xs text-gray-500">Execute trades in simulation mode without real money</p>
                                </div>
                                <button
                                    onClick={() => handleToggleSimulation(!state?.risk?.is_simulation)}
                                    className={`
                    relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none
                    ${state?.risk?.is_simulation ? 'bg-blue-600' : 'bg-white/10'}
                  `}
                                >
                                    <span
                                        className={`
                      inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                      ${state?.risk?.is_simulation ? 'translate-x-6' : 'translate-x-1'}
                    `}
                                    />
                                </button>
                            </div>
                        </div>
                    </div>

                    <div className="bg-[#141414] rounded-3xl p-8 border border-white/5 relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-8 opacity-20">
                            <Activity size={40} className="text-blue-500" />
                        </div>
                        <h3 className="text-xl font-bold mb-6 flex items-center space-x-2">
                            <TrendingUp className="text-blue-500" size={20} />
                            <span>Bot Insights & Analysis</span>
                        </h3>

                        <div className="space-y-6">
                            <div className="bg-white/5 rounded-2xl p-6 border border-white/5">
                                <p className="text-xs text-gray-500 uppercase tracking-widest font-bold mb-2">Automated Reasoning</p>
                                <p className="text-lg font-medium text-gray-200 leading-relaxed">
                                    &quot;{state?.tpb?.reasoning || 'Analyzing market structure...'}&quot;
                                </p>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-white/2 rounded-xl p-4 border border-white/5">
                                    <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Target Price</p>
                                    <p className="text-xl font-mono font-bold text-green-500">
                                        {state?.tpb?.target ? `₹${state.tpb.target.toFixed(2)}` : '--'}
                                    </p>
                                </div>
                                <div className="bg-white/2 rounded-xl p-4 border border-white/5">
                                    <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Stop Loss</p>
                                    <p className="text-xl font-mono font-bold text-red-500">
                                        {state?.tpb?.stop_loss ? `₹${state.tpb.stop_loss.toFixed(2)}` : '--'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bg-[#141414] rounded-3xl border border-white/5 overflow-hidden">
                        <div className="p-8 pb-0 border-b border-white/5 bg-white/2">
                            <h3 className="text-xl font-bold mb-6">Market Action</h3>
                            {state?.chart && <MarketChart data={state.chart} />}
                        </div>
                        <div className="p-8 pb-0 border-b border-white/5 bg-white/2 mt-4">
                            <h3 className="text-xl font-bold mb-6 flex items-center space-x-2">
                                <span>Open Positions</span>
                            </h3>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="text-gray-500 text-xs uppercase tracking-wider">
                                    <tr>
                                        <th className="px-8 py-4 font-bold">Symbol</th>
                                        <th className="px-8 py-4 font-bold">Type</th>
                                        <th className="px-8 py-4 font-bold text-right">Entry</th>
                                        <th className="px-8 py-4 font-bold text-right">LTP</th>
                                        <th className="px-8 py-4 font-bold text-right">PnL</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {state?.positions?.map((pos: any, i: number) => (
                                        <motion.tr
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            key={i}
                                            className="hover:bg-white/2 transition-colors group"
                                        >
                                            <td className="px-8 py-6 font-medium text-blue-400">{pos.tradingsymbol}</td>
                                            <td className="px-8 py-6">
                                                <span className={`px-3 py-1 rounded-full text-[10px] font-bold uppercase ${pos.option_type === 'CE' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                                                    {pos.option_type}
                                                </span>
                                            </td>
                                            <td className="px-8 py-6 text-right font-mono text-gray-400">₹{pos.entry_price?.toFixed(2) || 0}</td>
                                            <td className="px-8 py-6 text-right font-mono">₹{pos.ltp?.toFixed(2) || 0}</td>
                                            <td className={`px-8 py-6 text-right font-bold font-mono ${pos.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                                {pos.pnl >= 0 ? '+' : ''}{pos.pnl?.toFixed(2) || 0}
                                            </td>
                                        </motion.tr>
                                    ))}
                                    {!state?.positions?.length && (
                                        <tr>
                                            <td colSpan={5} className="px-8 py-12 text-center text-gray-500 italic">No open positions</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                {/* Sidebar History */}
                <div className="space-y-8">
                    <div className="bg-[#141414] rounded-3xl border border-white/5 overflow-hidden p-8">
                        <h3 className="text-xl font-bold mb-6">Recent Activity</h3>
                        <div className="space-y-6">
                            {history.map((item, i) => (
                                <div key={i} className="flex items-start space-x-4">
                                    <div className={`mt-1 w-2 h-2 rounded-full shrink-0 ${item.exit_price ? 'bg-blue-500' : 'bg-green-500'}`}></div>
                                    <div className="flex-1">
                                        <p className="text-sm font-medium text-gray-200">
                                            {item.exit_price ? 'Trade Exited' : 'Entry Executed'}
                                        </p>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {item.tradingsymbol} {item.option_type} - ₹{item.exit_price || item.entry_price}
                                        </p>
                                        <p className="text-[10px] text-gray-600 mt-2">
                                            {new Date(item.date || item.entry_time).toLocaleTimeString()}
                                        </p>
                                    </div>
                                    {item.pnl !== undefined && (
                                        <div className={`text-sm font-bold ${item.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                            {item.pnl >= 0 ? '+' : ''}{item.pnl?.toFixed(2) || 0}
                                        </div>
                                    )}
                                </div>
                            ))}
                            {!history.length && <p className="text-gray-500 text-sm italic">No recent activity</p>}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function StatusCard({ title, value, trend, isPositive, icon }: any) {
    return (
        <div className="bg-[#141414] border border-white/5 p-6 rounded-3xl hover:border-white/10 transition-colors">
            <div className="flex items-center justify-between mb-4">
                <div className="p-3 bg-white/5 rounded-2xl text-gray-400 group-hover:text-blue-500 transition-colors">
                    {icon}
                </div>
                <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-1 rounded-lg ${isPositive ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                    {trend}
                </span>
            </div>
            <p className="text-sm text-gray-500 font-medium mb-1">{title}</p>
            <p className="text-2xl font-bold font-mono">{value}</p>
        </div>
    );
}

function ControlButton({ onClick, active, starting, variant, label, subLabel, icon }: any) {
    const isPrimary = variant === 'primary';
    const isActive = active;
    const isStarting = starting;

    return (
        <button
            onClick={isStarting && variant !== 'danger' ? undefined : onClick}
            className={`
        relative text-left p-6 rounded-2xl border transition-all duration-300 group
        ${isActive
                    ? (isPrimary ? 'bg-blue-600/10 border-blue-600' : 'bg-red-600/10 border-red-600')
                    : isStarting
                        ? 'bg-yellow-600/10 border-yellow-600/50 cursor-wait animate-pulse'
                        : 'bg-[#1a1a1a] border-white/5 opacity-50 grayscale hover:grayscale-0 hover:opacity-100 hover:border-white/20'
                }
      `}
        >
            <div className="flex items-center space-x-4">
                <div className={`p-3 rounded-xl ${isActive ? (isPrimary ? 'bg-blue-600 text-white' : 'bg-red-600 text-white') : isStarting ? 'bg-yellow-600 text-white' : 'bg-white/5 text-gray-500'}`}>
                    {icon}
                </div>
                <div>
                    <p className={`font-bold ${isActive ? 'text-white' : isStarting ? 'text-yellow-500' : 'text-gray-400'}`}>{label}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{subLabel}</p>
                </div>
            </div>
            {(isActive || isStarting) && (
                <div className="absolute top-4 right-4 flex space-x-1">
                    <span className={`w-1.5 h-1.5 rounded-full ${isPrimary ? 'bg-blue-500 animate-ping' : isStarting ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'}`}></span>
                    <span className={`w-1.5 h-1.5 rounded-full ${isPrimary ? 'bg-blue-500' : isStarting ? 'bg-yellow-500' : 'bg-red-500'}`}></span>
                </div>
            )}
        </button>
    );
}
