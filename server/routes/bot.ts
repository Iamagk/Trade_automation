import { Router } from 'express';
import { botManager } from '../services/botManager';
import { authenticateToken } from '../middleware/auth';

const router = Router();

// Get current bot status
router.get('/status', authenticateToken, (req, res) => {
    res.json(botManager.getStatus());
});

// Get recent logs
router.get('/logs', authenticateToken, (req, res) => {
    res.json({ logs: botManager.getLogs() });
});

// Start the bot
router.post('/start', authenticateToken, (req, res) => {
    const { mode } = req.body;

    // Valid modes: login, run_now_dry, schedule_dry, run_now_real, schedule_real
    if (!mode || typeof mode !== 'string') {
        return res.status(400).json({ error: 'Invalid mode.' });
    }

    try {
        botManager.start(mode);
        res.json({ message: `Bot started in ${mode} mode`, status: botManager.getStatus() });
    } catch (error: any) {
        res.status(400).json({ error: error.message });
    }
});

// Stop the bot
router.post('/stop', authenticateToken, (req, res) => {
    botManager.stop();
    res.json({ message: 'Bot stop signal sent', status: botManager.getStatus() });
});

// Send input to the bot
router.post('/input', authenticateToken, (req, res) => {
    const { input } = req.body;
    if (typeof input !== 'string') {
        return res.status(400).json({ error: 'Input must be a string' });
    }

    try {
        botManager.sendInput(input);
        res.json({ message: 'Input sent successfully' });
    } catch (error: any) {
        res.status(400).json({ error: error.message });
    }
});

export default router;
