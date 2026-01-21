import express from 'express';
import pool from '../db';
import { authenticateToken } from '../middleware/auth';

const router = express.Router();

router.get('/', authenticateToken, async (req, res) => {
    try {
        const tradesResult = await pool.query('SELECT * FROM trades');
        const trades: any[] = tradesResult.rows;

        const holdingsDict: Record<string, { qty: number; cost: number }> = {};

        for (const trade of trades) {
            const symbol = trade.symbol.trim();
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
        let prices: Record<string, number> = {};

        if (activeSymbols.length > 0) {
            try {
                const { execSync } = require('child_process');
                const path = require('path');
                let projectRoot = path.resolve(__dirname, '../../');

                if (__dirname.includes('dist')) {
                    projectRoot = path.resolve(__dirname, '../../../');
                }

                const fetchScript = path.join(projectRoot, 'src/tools/fetch_prices.py');
                const symbolsArg = activeSymbols.join(' ');

                let pythonCmd = 'python3';
                try {
                    execSync('python3 --version');
                } catch {
                    pythonCmd = 'python';
                }

                const output = execSync(`${pythonCmd} ${fetchScript} ${symbolsArg}`).toString();
                prices = JSON.parse(output);
            } catch (err) {
                console.error('Error fetching live prices for holdings:', err);
            }
        }

        const botHoldings: any[] = [];
        for (const symbol of activeSymbols) {
            const stats = holdingsDict[symbol];
            const avgPrice = stats.cost / stats.qty;
            botHoldings.push({
                symbol: symbol,
                quantity: stats.qty,
                average_price: avgPrice,
                current_price: prices[symbol] || avgPrice // Fallback only if fetch failed
            });
        }

        res.json(botHoldings);

    } catch (err: any) {
        console.error('Holdings error:', err);
        res.status(500).json({ detail: 'Internal server error' });
    }
});

export default router;
