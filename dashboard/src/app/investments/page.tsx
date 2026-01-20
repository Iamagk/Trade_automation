"use strict";
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import {
    ArrowLeft,
    TrendingUp,
    TrendingDown,
    DollarSign,
    Clock,
    LogOut,
    RefreshCcw,
    Search,
    Filter,
    Briefcase
} from "lucide-react";
import Link from "next/link";

export default function Investments() {
    const [holdings, setHoldings] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState("");
    const router = useRouter();

    const fetchHoldings = async () => {
        const token = localStorage.getItem("token");
        if (!token) {
            router.push("/login");
            return;
        }

        try {
            const response = await axios.get("http://localhost:8000/holdings", {
                headers: { Authorization: `Bearer ${token}` }
            });
            setHoldings(response.data);
        } catch (err: any) {
            console.error("Failed to fetch holdings", err);
            if (err.response?.status === 401) {
                localStorage.removeItem("token");
                router.push("/login");
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHoldings();
    }, []);

    const handleLogout = () => {
        localStorage.removeItem("token");
        router.push("/login");
    };

    const filteredHoldings = holdings.filter(holding =>
        holding.symbol.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const totalPortfolioValue = holdings.reduce((acc, h) => acc + (h.current_price * h.quantity), 0);
    const totalInvestedValue = holdings.reduce((acc, h) => acc + (h.average_price * h.quantity), 0);
    const totalPnL = totalPortfolioValue - totalInvestedValue;

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
                            <h1 className="text-3xl font-bold mb-1 text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-blue-400">
                                Investments
                            </h1>
                            <p className="text-gray-400">Current portfolio and holdings performance</p>
                        </div>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={fetchHoldings}
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

                {/* Portfolio Summary */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800 shadow-lg">
                        <div className="text-sm text-gray-400 mb-1">Current Value</div>
                        <div className="text-2xl font-bold">₹{totalPortfolioValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                    </div>
                    <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800 shadow-lg">
                        <div className="text-sm text-gray-400 mb-1">Total Invested</div>
                        <div className="text-2xl font-bold">₹{totalInvestedValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                    </div>
                    <div className="p-6 bg-gray-900 rounded-2xl border border-gray-800 shadow-lg">
                        <div className="text-sm text-gray-400 mb-1">Total P&L</div>
                        <div className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {totalPnL >= 0 ? '+' : ''}₹{totalPnL.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </div>
                        <div className={`text-sm font-semibold mt-1 ${totalPnL >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {totalPnL >= 0 ? '+' : ''}{totalInvestedValue > 0 ? ((totalPnL / totalInvestedValue) * 100).toFixed(2) : '0.00'}%
                        </div>
                    </div>
                </div>

                {/* Filters and Search */}
                <div className="mb-8 flex flex-col md:flex-row gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 w-5 h-5" />
                        <input
                            type="text"
                            placeholder="Search by symbol..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-gray-900 border border-gray-800 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                        />
                    </div>
                </div>

                {/* Holdings Table */}
                <div className="bg-gray-900 rounded-2xl border border-gray-800 shadow-xl overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-gray-950 text-gray-400 text-xs uppercase">
                                <tr>
                                    <th className="px-6 py-4">Symbol</th>
                                    <th className="px-6 py-4">Quantity</th>
                                    <th className="px-6 py-4">Avg. Price</th>
                                    <th className="px-6 py-4">LTP</th>
                                    <th className="px-6 py-4">Current Value</th>
                                    <th className="px-6 py-4">P&L</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800">
                                {filteredHoldings.map((holding: any, idx: number) => {
                                    const pnl = (holding.current_price - holding.average_price) * holding.quantity;
                                    const isPositive = pnl >= 0;
                                    return (
                                        <tr key={idx} className="hover:bg-gray-800/50 transition-all group">
                                            <td className="px-6 py-4">
                                                <span className="px-2.5 py-1 bg-emerald-500/10 text-emerald-400 rounded-lg text-xs font-bold border border-emerald-500/20">
                                                    {holding.symbol}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-gray-300 font-mono text-sm">
                                                {holding.quantity}
                                            </td>
                                            <td className="px-6 py-4 text-gray-300 font-mono text-sm">
                                                ₹{holding.average_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                            </td>
                                            <td className="px-6 py-4 text-gray-300 font-mono text-sm">
                                                ₹{holding.current_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="text-gray-200 font-bold text-sm">
                                                    ₹{(holding.current_price * holding.quantity).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-2">
                                                    {isPositive ? (
                                                        <TrendingUp className="w-4 h-4 text-emerald-400" />
                                                    ) : (
                                                        <TrendingDown className="w-4 h-4 text-rose-400" />
                                                    )}
                                                    <div className="flex flex-col">
                                                        <span className={`text-sm font-semibold ${isPositive ? "text-emerald-400" : "text-rose-400"}`}>
                                                            {isPositive ? '+' : ''}₹{pnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                                        </span>
                                                        <span className={`text-xs font-medium ${isPositive ? "text-emerald-400/70" : "text-rose-400/70"}`}>
                                                            {isPositive ? '+' : ''}{((pnl / (holding.average_price * holding.quantity)) * 100).toFixed(2)}%
                                                        </span>
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                                {filteredHoldings.length === 0 && (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-20 text-center">
                                            <div className="flex flex-col items-center justify-center text-gray-500">
                                                <Briefcase className="w-12 h-12 mb-4 opacity-20" />
                                                <p className="text-lg font-medium">No holdings found</p>
                                                <p className="text-sm">Authorize Zerodha or check your Zerodha dashboard.</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
