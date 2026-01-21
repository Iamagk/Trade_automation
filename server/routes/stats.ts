import express from 'express';
import pool from '../db';
import { authenticateToken } from '../middleware/auth';

const router = express.Router();

router.get('/', authenticateToken, async (req, res) => {
    try {
        // 1. Calculate stats from trades
        const tradesResult = await pool.query('SELECT * FROM trades');
        const trades: any[] = tradesResult.rows;

        const holdingsDict: Record<string, { qty: number; cost: number }> = {};

        for (const trade of trades) {
            const symbol = trade.symbol;
            if (!holdingsDict[symbol]) {
                holdingsDict[symbol] = { qty: 0, cost: 0.0 };
            }

            const action = trade.action.toUpperCase();
            if (['BUY', 'AVERAGE'].includes(action)) {
                holdingsDict[symbol].qty += trade.quantity;
                holdingsDict[symbol].cost += trade.total_cost;
            } else if (action === 'SELL') {
                const oldQty = holdingsDict[symbol].qty;
                if (oldQty > 0) {
                    const avgPrice = holdingsDict[symbol].cost / oldQty;
                    holdingsDict[symbol].qty -= trade.quantity;
                    holdingsDict[symbol].cost -= (trade.quantity * avgPrice);
                }
            }
        }

        const activeSymbols = Object.keys(holdingsDict).filter(sym => holdingsDict[sym].qty > 0);
        let totalCost = 0;
        let totalValue = 0;

        if (activeSymbols.length > 0) {
            try {
                const { execSync } = require('child_process');
                const path = require('path');
                let projectRoot = path.resolve(__dirname, '../../');

                // If we are in 'dist' (production), go up one more level to reach project root
                if (__dirname.includes('dist')) {
                    projectRoot = path.resolve(__dirname, '../../../');
                }

                // Use the same project root detection logic as BotManager
                // For Docker/Production, we need a reliable path to the python script
                const fetchScript = path.join(projectRoot, 'src/tools/fetch_prices.py');
                const symbolsArg = activeSymbols.join(' ');

                // Detect python command (python3 or python)
                let pythonCmd = 'python3';
                try {
                    execSync('python3 --version');
                } catch {
                    pythonCmd = 'python';
                }

                const output = execSync(`${pythonCmd} ${fetchScript} ${symbolsArg}`).toString();
                const prices = JSON.parse(output);

                for (const symbol of activeSymbols) {
                    const stats = holdingsDict[symbol];
                    totalCost += stats.cost;
                    const ltp = prices[symbol] || 0;
                    if (ltp > 0) {
                        totalValue += (stats.qty * ltp);
                    } else {
                        // Fallback to cost if price fetch failed
                        totalValue += stats.cost;
                    }
                }
            } catch (err) {
                console.error('Error fetching live prices for stats:', err);
                // Fallback to cost if all else fails
                for (const symbol of activeSymbols) {
                    totalCost += holdingsDict[symbol].cost;
                }
                totalValue = totalCost;
            }
        }

        // 2. Get latest screening
        // Find latest timestamp first
        const latestRunResult = await pool.query(
            `SELECT date, time FROM screening_logs 
             ORDER BY timestamp DESC LIMIT 1`
        );

        let lastScreening: any[] = [];
        if (latestRunResult.rows.length > 0) {
            const { date, time } = latestRunResult.rows[0];
            const screeningResult = await pool.query(
                `SELECT * FROM screening_logs 
                 WHERE date = $1 AND time = $2 
                 ORDER BY rank ASC`,
                [date, time]
            );
            lastScreening = screeningResult.rows;
        }

        res.json({
            total_trades: trades.length,
            total_cost: totalCost,
            total_value: totalValue, // NEW: Market Value
            last_screening: lastScreening
        });

    } catch (err: any) {
        console.error('Stats error:', err);
        res.status(500).json({ detail: 'Internal server error' });
    }
});

export default router;
