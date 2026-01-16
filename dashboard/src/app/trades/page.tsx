"use strict";
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import {
    ArrowLeft,
    ArrowUpRight,
    ArrowDownRight,
    ShoppingBag,
    Clock,
    LogOut,
    RefreshCcw,
    Search,
    Filter
} from "lucide-react";
import Link from "next/link";

export default function TradeHistory() {
    const [trades, setTrades] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const router = useRouter();

    const fetchTrades = async () => {
        const token = localStorage.getItem("token");
        if (!token) {
            router.push("/login");
            return;
        }

        try {
            const response = await axios.get("http://localhost:8000/trades", {
                headers: { Authorization: `Bearer ${token}` }
            });
            // Sort trades by date and time descending (newest first)
            const sortedTrades = response.data.sort((a: any, b: any) => {
                const dateA = new Date(`${a.date}T${a.time}`);
                const dateB = new Date(`${b.date}T${b.time}`);
                return dateB.getTime() - dateA.getTime();
            });
            setTrades(sortedTrades);
        } catch (err: any) {
            console.error("Failed to fetch trades", err);
            if (err.response?.status === 401) {
                localStorage.removeItem("token");
                router.push("/login");
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTrades();
    }, []);

    const handleLogout = () => {
        localStorage.removeItem("token");
        router.push("/login");
    };

    const filteredTrades = trades.filter(trade =>
        trade.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
        trade.action.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-950 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-950 text-white p-6 md:p-10 font-sans">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
                    <div className="flex items-center gap-4">
                        <Link
                            href="/"
                            className="p-2 bg-gray-900 border border-gray-800 rounded-lg hover:bg-gray-800 transition-all text-gray-400 hover:text-white"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </Link>
                        <div>
                            <h1 className="text-3xl font-bold mb-1 text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
                                Trade History
                            </h1>
                            <p className="text-gray-400">Detailed record of all bot activities</p>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={fetchTrades}
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

                {/* Filters and Search */}
                <div className="mb-8 flex flex-col md:flex-row gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 w-5 h-5" />
                        <input
                            type="text"
                            placeholder="Search by symbol or action..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-gray-900 border border-gray-800 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                        />
                    </div>
                    <button className="flex items-center justify-center gap-2 px-6 py-2 bg-gray-900 border border-gray-800 rounded-xl hover:bg-gray-800 transition-all text-sm text-gray-400">
                        <Filter className="w-4 h-4" /> Filter
                    </button>
                </div>

                {/* Trade History Table */}
                <div className="bg-gray-900 rounded-2xl border border-gray-800 shadow-xl overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-gray-950 text-gray-400 text-xs uppercase">
                                <tr>
                                    <th className="px-6 py-4">Transaction</th>
                                    <th className="px-6 py-4">Symbol</th>
                                    <th className="px-6 py-4">Action</th>
                                    <th className="px-6 py-4">Quantity</th>
                                    <th className="px-6 py-4">Avg. Price</th>
                                    <th className="px-6 py-4">Total Cost</th>
                                    <th className="px-6 py-4 text-right">Details</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800">
                                {filteredTrades.map((trade: any) => (
                                    <tr key={trade.id} className="hover:bg-gray-800/50 transition-all group">
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col">
                                                <span className="font-medium text-sm text-gray-200">
                                                    {trade.date}
                                                </span>
                                                <div className="flex items-center gap-1.5 text-xs text-gray-500 mt-1">
                                                    <Clock className="w-3 h-3" /> {trade.time}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="px-2.5 py-1 bg-blue-500/10 text-blue-400 rounded-lg text-xs font-bold border border-blue-500/20">
                                                {trade.symbol}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                {trade.action.toUpperCase() === "BUY" ? (
                                                    <div className="p-1.5 bg-emerald-500/10 text-emerald-400 rounded-md">
                                                        <ArrowDownRight className="w-4 h-4" />
                                                    </div>
                                                ) : (
                                                    <div className="p-1.5 bg-rose-500/10 text-rose-400 rounded-md">
                                                        <ArrowUpRight className="w-4 h-4" />
                                                    </div>
                                                )}
                                                <span className={`text-sm font-semibold ${trade.action.toUpperCase() === "BUY" ? "text-emerald-400" : "text-rose-400"
                                                    }`}>
                                                    {trade.action}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-gray-300 font-mono text-sm">
                                            {trade.quantity}
                                        </td>
                                        <td className="px-6 py-4 text-gray-300 font-mono text-sm">
                                            ₹{trade.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="text-gray-200 font-bold text-sm">
                                                ₹{trade.total_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-all opacity-0 group-hover:opacity-100">
                                                View Receipt
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                                {filteredTrades.length === 0 && (
                                    <tr>
                                        <td colSpan={7} className="px-6 py-20 text-center">
                                            <div className="flex flex-col items-center justify-center text-gray-500">
                                                <ShoppingBag className="w-12 h-12 mb-4 opacity-20" />
                                                <p className="text-lg font-medium">No trade history found</p>
                                                <p className="text-sm">Try adjusting your search or rerun the bot.</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                    <div className="p-6 border-t border-gray-800 flex justify-between items-center text-sm text-gray-500">
                        <div>Showing {filteredTrades.length} transactions</div>
                        <div className="flex gap-2">
                            <button disabled className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg opacity-50 cursor-not-allowed">Previous</button>
                            <button disabled className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg opacity-50 cursor-not-allowed">Next</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
