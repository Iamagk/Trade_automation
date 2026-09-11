'use client';

import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

interface ChartDataPoint {
    time: string;
    price: number;
    vwap?: number;
}

interface MarketChartProps {
    data: ChartDataPoint[];
}

export default function MarketChart({ data }: MarketChartProps) {
    if (!data || data.length === 0) {
        return (
            <div className="h-64 flex items-center justify-center text-gray-500 italic">
                Waiting for market data...
            </div>
        );
    }

    const chartData = {
        labels: data.map(d => d.time),
        datasets: [
            {
                label: 'Price',
                data: data.map(d => d.price),
                borderColor: '#3b82f6', // blue-500
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true,
                pointRadius: 0,
                pointHitRadius: 10,
                borderWidth: 2,
            },
            {
                label: 'VWAP',
                data: data.map(d => d.vwap || null),
                borderColor: '#f59e0b', // amber-500
                borderDash: [5, 5],
                tension: 0.4,
                fill: false,
                pointRadius: 0,
                pointHitRadius: 10,
                borderWidth: 2,
            }
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: 'index' as const,
            intersect: false,
        },
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
                padding: 12,
                boxPadding: 6,
            },
        },
        scales: {
            x: {
                grid: {
                    display: false,
                    color: 'rgba(255, 255, 255, 0.05)',
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.5)',
                    maxTicksLimit: 8,
                },
            },
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.05)',
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.5)',
                },
                beginAtZero: false,
            },
        },
    };

    return (
        <div className="h-[300px] w-full">
            <Line data={chartData} options={options} />
        </div>
    );
}
