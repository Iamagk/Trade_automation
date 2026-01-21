import { Pool } from 'pg';
import dotenv from 'dotenv';
import path from 'path';

// Load env vars from root .env if it exists
const envPath = path.join(__dirname, '../.env');
dotenv.config({ path: envPath });

const connectionString = process.env.DATABASE_URL;
const isProduction = process.env.NODE_ENV === 'production' || !!connectionString;

const poolConfig: any = connectionString
    ? { connectionString }
    : {
        user: process.env.POSTGRES_USER,
        host: process.env.POSTGRES_HOST,
        database: process.env.POSTGRES_DB,
        password: process.env.POSTGRES_PASSWORD,
        port: parseInt(process.env.POSTGRES_PORT || '5432'),
    };

// Add SSL for production/Render connections
if (isProduction && connectionString && !connectionString.includes('localhost')) {
    poolConfig.ssl = {
        rejectUnauthorized: false
    };
}

// Final check if we have enough info
if (!connectionString && !process.env.POSTGRES_HOST) {
    throw new Error('Missing database configuration. Provide DATABASE_URL or POSTGRES_HOST variables.');
}

const pool = new Pool(poolConfig);

pool.on('error', (err) => {
    console.error('Unexpected error on idle client', err);
    process.exit(-1);
});

export const query = (text: string, params?: any[]) => pool.query(text, params);
export default pool;
