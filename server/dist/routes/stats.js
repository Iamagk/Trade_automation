"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const db_1 = __importDefault(require("../db"));
const auth_1 = require("../middleware/auth");
const router = express_1.default.Router();
router.get('/', auth_1.authenticateToken, async (req, res) => {
    try {
        // 1. Calculate stats from trades
        const tradesResult = await db_1.default.query('SELECT * FROM trades');
        const trades = tradesResult.rows;
        const holdingsDict = {};
        for (const trade of trades) {
            const symbol = trade.symbol;
            if (!holdingsDict[symbol]) {
                holdingsDict[symbol] = { qty: 0, cost: 0.0 };
            }
            const action = trade.action.toUpperCase();
            if (['BUY', 'AVERAGE'].includes(action)) {
                holdingsDict[symbol].qty += trade.quantity;
                holdingsDict[symbol].cost += trade.total_cost;
            }
            else if (action === 'SELL') {
                const oldQty = holdingsDict[symbol].qty;
                if (oldQty > 0) {
                    const avgPrice = holdingsDict[symbol].cost / oldQty;
                    holdingsDict[symbol].qty -= trade.quantity;
                    holdingsDict[symbol].cost -= (trade.quantity * avgPrice);
                }
            }
        }
        let totalCost = 0;
        for (const key in holdingsDict) {
            if (holdingsDict[key].qty > 0) {
                totalCost += holdingsDict[key].cost;
            }
        }
        // 2. Get latest screening
        // Find latest timestamp first
        const latestRunResult = await db_1.default.query(`SELECT date, time FROM screening_logs 
             ORDER BY timestamp DESC LIMIT 1`);
        let lastScreening = [];
        if (latestRunResult.rows.length > 0) {
            const { date, time } = latestRunResult.rows[0];
            const screeningResult = await db_1.default.query(`SELECT * FROM screening_logs 
                 WHERE date = $1 AND time = $2 
                 ORDER BY rank ASC`, [date, time]);
            lastScreening = screeningResult.rows;
        }
        res.json({
            total_trades: trades.length,
            total_cost: totalCost,
            last_screening: lastScreening
        });
    }
    catch (err) {
        console.error('Stats error:', err);
        res.status(500).json({ detail: 'Internal server error' });
    }
});
exports.default = router;
