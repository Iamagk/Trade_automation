"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.authenticateToken = void 0;
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
if (!process.env.JWT_SECRET) {
    // We can't throw here if .env isn't loaded yet? 
    // It's loaded in index.ts which imports this? No, it imports routes which import this.
    // Env loading happens at runtime start.
    // Ideally duplicate dotenv config or assume it's loaded.
}
const authenticateToken = (req, res, next) => {
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
        const decoded = jsonwebtoken_1.default.verify(token, SECRET_KEY);
        req.user = { username: decoded.sub };
        next();
    }
    catch (err) {
        return res.status(403).json({ detail: 'Invalid or expired token' });
    }
};
exports.authenticateToken = authenticateToken;
