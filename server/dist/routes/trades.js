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
        // Simple select, frontend handles sorting usually, but we can sort here
        // The Python code had skip/limit but frontend didn't use pagination heavily yet.
        // We'll just return all for now or limit 100 default.
        const result = await db_1.default.query('SELECT * FROM trades ORDER BY timestamp DESC LIMIT 100');
        res.json(result.rows);
    }
    catch (err) {
        console.error('Trades error:', err);
        res.status(500).json({ detail: 'Internal server error' });
    }
});
exports.default = router;
