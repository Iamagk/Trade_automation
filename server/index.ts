import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import cookieParser from 'cookie-parser';

// Routes
import authRoutes from './routes/auth';
import statsRoutes from './routes/stats';
import tradesRoutes from './routes/trades';
import holdingsRoutes from './routes/holdings';
// import botRoutes from './routes/bot'; 

// Load environment variables
dotenv.config({ path: path.join(__dirname, '../.env') });

if (!process.env.PORT) {
    console.warn("PORT not set, defaulting to 8000 for safety but check env!");
}

const app = express();
const port = process.env.PORT || 8000;

// CORS configuration for credentials
app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
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
// app.use('/bot', botRoutes);

// Error handlers
process.on('uncaughtException', (err) => {
    console.error('Uncaught Exception:', err);
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});
