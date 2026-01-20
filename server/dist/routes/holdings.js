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
        const botHoldings = [];
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
    }
    catch (err) {
        console.error('Holdings error:', err);
        res.status(500).json({ detail: 'Internal server error' });
    }
});
exports.default = router;
