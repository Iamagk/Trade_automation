import express from 'express';
import pool from '../db';
import { authenticateToken } from '../middleware/auth';

const router = express.Router();

router.get('/', authenticateToken, async (req, res) => {
    try {
        // Simple select, frontend handles sorting usually, but we can sort here
        // The Python code had skip/limit but frontend didn't use pagination heavily yet.
        // We'll just return all for now or limit 100 default.
        const result = await pool.query(
            'SELECT * FROM trades ORDER BY timestamp DESC LIMIT 100'
        );
        res.json(result.rows);
    } catch (err: any) {
        console.error('Trades error:', err);
        res.status(500).json({ detail: 'Internal server error' });
    }
});

export default router;
