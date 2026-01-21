import express from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import pool from '../db';
import { authenticateToken, AuthRequest } from '../middleware/auth';

const router = express.Router();

// Login endpoint
router.post('/token', async (req, res) => {
    console.log('Login attempt:', req.body.username);
    const { username, password } = req.body;

    if (!process.env.JWT_SECRET || !process.env.ACCESS_TOKEN_EXPIRE_MINUTES) {
        console.error("JWT Configuration missing");
        return res.status(500).json({ detail: "Server configuration error" });
    }

    const SECRET_KEY = process.env.JWT_SECRET;
    // Env var is usually minutes, e.g., "10080"
    const EXPIRE_MINUTES = parseInt(process.env.ACCESS_TOKEN_EXPIRE_MINUTES);

    try {
        const result = await pool.query(
            'SELECT * FROM users WHERE username = $1',
            [username]
        );
        const user = result.rows[0];

        if (!user) {
            return res.status(401).json({
                detail: 'Incorrect username or password'
            });
        }

        // Verify password
        const validPassword = await bcrypt.compare(password, user.hashed_password);
        if (!validPassword) {
            return res.status(401).json({
                detail: 'Incorrect username or password'
            });
        }

        const token = jwt.sign({ sub: user.username }, SECRET_KEY, {
            expiresIn: `${EXPIRE_MINUTES}m`,
        });

        res.cookie('token', token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax',
            maxAge: EXPIRE_MINUTES * 60 * 1000,
        });

        res.json({
            status: 'success',
            username: user.username,
            // We can return access_token for backward compatibility if needed, 
            // but style guide says HttpOnly cookies. 
            // The frontend "controllerService" might expect something?
            // "AuthService.ts" in style guide returns "response.data" from /token log.
            // But it doesn't use the token in response, it relies on cookie.
        });

    } catch (err: any) {
        console.error('Login error:', err.message);
        res.status(500).json({ detail: 'Internal server error' });
    }
});

// Logout endpoint
router.post('/logout', (req, res) => {
    res.clearCookie('token');
    res.json({ status: 'success' });
});

// Current user endpoint
router.get('/whoami', authenticateToken, (req: AuthRequest, res) => {
    res.json({
        username: req.user?.username,
    });
});

export default router;
