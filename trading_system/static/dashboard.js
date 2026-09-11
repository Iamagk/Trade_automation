document.addEventListener('DOMContentLoaded', () => {
    let chart;
    const ctx = document.getElementById('mainChart').getContext('2d');

    // Initialize Chart
    function initChart() {
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Spot Price',
                        borderColor: '#58a6ff',
                        backgroundColor: 'transparent',
                        data: [],
                        borderWidth: 2,
                        tension: 0.1,
                        pointRadius: 0
                    },
                    {
                        label: 'VWAP',
                        borderColor: '#d29922',
                        backgroundColor: 'transparent',
                        data: [],
                        borderWidth: 1.5,
                        borderDash: [5, 5],
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { display: false },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#8b949e' }
                    }
                },
                plugins: {
                    legend: { display: true, labels: { color: '#c9d1d9' } }
                }
            }
        });
    }

    async function updateDashboard() {
        try {
            const response = await fetch('/api/state');
            const data = await response.json();

            // Update Status Cards
            document.getElementById('trend-val').innerText = data.tpb_strategy.trend;
            document.getElementById('trend-val').className = 'stat-value ' + data.tpb_strategy.trend.toLowerCase();

            const setupStatus = document.getElementById('setup-status');
            if (data.tpb_strategy.signal_fired) {
                setupStatus.innerText = 'TRADE EXECUTED';
                setupStatus.className = 'status-badge';
            } else if (data.tpb_strategy.pullback_occurred) {
                setupStatus.innerText = 'PULLBACK DETECTED';
                setupStatus.style.background = 'rgba(210, 153, 34, 0.2)';
            } else if (data.tpb_strategy.is_established) {
                setupStatus.innerText = 'TREND CONFIRMED';
            }

            // Update P&L
            const pnl = data.position.pnl || 0;
            const pnlVal = document.getElementById('pnl-val');
            pnlVal.innerText = `₹ ${pnl.toFixed(2)}`;
            pnlVal.className = 'stat-value ' + (pnl >= 0 ? 'pnl-positive' : 'pnl-negative');

            document.getElementById('daily-pnl').innerText = `₹ ${data.risk.daily_pnl.toFixed(2)}`;
            document.getElementById('trade-count').innerText = `${data.risk.trades_today} Trades Today`;

            // Active Position Panel
            const pos = data.position;
            if (pos.tradingsymbol) {
                document.getElementById('pos-symbol').innerText = pos.tradingsymbol;
                document.getElementById('pos-entry').innerText = pos.entry_price.toFixed(2);
                document.getElementById('pos-ltp').innerText = (pos.ltp || 0).toFixed(2);
                document.getElementById('pos-sl-tgt').innerText = `${pos.stop_loss.toFixed(2)} / ${pos.target.toFixed(2)}`;
                document.getElementById('pos-tsl').innerText = pos.trailing_sl.toFixed(2);
            } else {
                document.getElementById('pos-symbol').innerText = '-';
            }

            // Update Chart with historical data
            if (data.chart_data && data.chart_data.length > 0) {
                chart.data.labels = data.chart_data.map(d => d.time);
                chart.data.datasets[0].data = data.chart_data.map(d => d.price);
                chart.data.datasets[1].data = data.chart_data.map(d => d.vwap);
                chart.update('none');
            }

        } catch (error) {
            console.error('Failed to fetch state:', error);
            document.getElementById('engine-status').innerText = 'ENGINE: DISCONNECTED';
            document.getElementById('engine-status').style.background = 'rgba(248, 81, 73, 0.15)';
        }
    }


    // Global Action Wrappers
    window.manualTrade = async (type) => {
        if (!confirm(`Trigger manual ${type}?`)) return;
        await fetch(`/api/trade/manual?signal_type=${type}`, { method: 'POST' });
    };

    window.manualExit = async () => {
        if (!confirm('Force close all positions?')) return;
        await fetch('/api/trade/exit', { method: 'POST' });
    };

    window.activateKillSwitch = async () => {
        if (!confirm('EMERGENCY: Stop ALL trading and halt engine?')) return;
        await fetch('/api/kill', { method: 'POST' });
    };

    initChart();
    setInterval(updateDashboard, 3000);
    updateDashboard();
});
