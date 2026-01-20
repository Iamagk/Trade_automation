"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const cors_1 = __importDefault(require("cors"));
const dotenv_1 = __importDefault(require("dotenv"));
const path_1 = __importDefault(require("path"));
const cookie_parser_1 = __importDefault(require("cookie-parser"));
// Routes
const auth_1 = __importDefault(require("./routes/auth"));
const stats_1 = __importDefault(require("./routes/stats"));
const trades_1 = __importDefault(require("./routes/trades"));
const holdings_1 = __importDefault(require("./routes/holdings"));
// import botRoutes from './routes/bot'; 
// Load environment variables
dotenv_1.default.config({ path: path_1.default.join(__dirname, '../.env') });
if (!process.env.PORT) {
    console.warn("PORT not set, defaulting to 8000 for safety but check env!");
}
const app = (0, express_1.default)();
const port = process.env.PORT || 8000;
// CORS configuration for credentials
app.use((0, cors_1.default)({
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    credentials: true,
}));
// Middleware
app.use((0, cookie_parser_1.default)());
app.use(express_1.default.json());
app.use(express_1.default.urlencoded({ extended: true }));
// Keep-alive interval
setInterval(() => { }, 1000 * 60 * 60);
// Routes
app.use('/', auth_1.default);
app.use('/stats', stats_1.default);
app.use('/trades', trades_1.default);
app.use('/holdings', holdings_1.default);
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
