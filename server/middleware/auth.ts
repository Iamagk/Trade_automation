import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

if (!process.env.JWT_SECRET) {
    // We can't throw here if .env isn't loaded yet? 
    // It's loaded in index.ts which imports this? No, it imports routes which import this.
    // Env loading happens at runtime start.
    // Ideally duplicate dotenv config or assume it's loaded.
}

export interface AuthRequest extends Request {
    user?: {
        username: string;
    };
}

export const authenticateToken = (
    req: AuthRequest,
    res: Response,
    next: NextFunction
) => {
    const SECRET_KEY = process.env.JWT_SECRET;
    if (!SECRET_KEY) {
        console.error("JWT_SECRET missing");
        return res.status(500).json({ detail: "Server misconfiguration" });
    }

    const token = req.cookies.token; // HttpOnly cookie
    if (!token) {
        return res.status(401).json({ detail: 'No token provided' });
    }

    try {
        const decoded = jwt.verify(token, SECRET_KEY) as { sub: string };
        req.user = { username: decoded.sub };
        next();
    } catch (err) {
        return res.status(403).json({ detail: 'Invalid or expired token' });
    }
};
