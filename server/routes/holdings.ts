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

        const botHoldings: any[] = [];
        for (const symbol in holdingsDict) {
            if (holdingsDict[symbol].qty > 0) {
                const avgPrice = holdingsDict[symbol].cost / holdingsDict[symbol].qty;
                botHoldings.push({
                    symbol: symbol,
                    quantity: holdingsDict[symbol].qty,
                    average_price: avgPrice,
                    current_price: avgPrice // Fallback as we don't have live API yet
                });
            }
        }

        res.json(botHoldings);

    } catch (err: any) {
        console.error('Holdings error:', err);
        res.status(500).json({ detail: 'Internal server error' });
    }
});

export default router;
