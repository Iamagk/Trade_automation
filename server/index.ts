import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import cookieParser from 'cookie-parser';
import bcrypt from 'bcryptjs';
import pool from './db';

// Routes
import authRoutes from './routes/auth';
import statsRoutes from './routes/stats';
import tradesRoutes from './routes/trades';
import holdingsRoutes from './routes/holdings';
import botRoutes from './routes/bot';

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../.env') });

if (!process.env.PORT) {
    console.warn("PORT not set, defaulting to 8000 for safety but check env!");
}

const app = express();
const port = process.env.PORT || 8000;

// CORS configuration for credentials
const allowedOrigins = [
    'https://trade-automation-one.vercel.app',
    'http://localhost:3000',
    process.env.FRONTEND_URL
].filter(Boolean) as string[];

app.use(cors({
    origin: allowedOrigins,
    credentials: true,
}));

// Middleware
app.use(cookieParser());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Keep-alive interval
setInterval(() => { }, 1000 * 60 * 60);

// Routes
app.use('/', authRoutes);
app.use('/stats', statsRoutes);
app.use('/trades', tradesRoutes);
app.use('/holdings', holdingsRoutes);
app.use('/bot', botRoutes);

// Error handlers
process.on('uncaughtException', (err) => {
    console.error('Uncaught Exception:', err);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

async function seedAdmin() {
    const username = 'allenngk';
    const password = 'Kkmballenn@2004';

    try {
        const result = await pool.query('SELECT * FROM users WHERE username = $1', [username]);
        if (result.rows.length === 0) {
            console.log('Seeding default admin user...');
            const hashedPassword = await bcrypt.hash(password, 10);
            await pool.query(
                'INSERT INTO users (username, hashed_password) VALUES ($1, $2)',
                [username, hashedPassword]
            );
            console.log('Admin user seeded successfully.');
        }
    } catch (err) {
        console.error('Error seeding admin user:', err);
    }
}

const startServer = async () => {
    await seedAdmin();
    app.listen(port, () => {
        console.log(`Server is running at http://localhost:${port}`);
    });
};

startServer();
