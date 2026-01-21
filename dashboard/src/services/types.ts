export interface BotStatus {
    status: 'IDLE' | 'RUNNING' | 'ERROR';
    pid: number | null;
    startTime: string | null;
    mode: 'dry-run' | 'real' | 'login' | null;
    logCount: number;
    isAuthorized: boolean;
}

export interface Trade {
    id: number;
    date: string;
    time: string;
    symbol: string;
    action: string;
    quantity: number;
    price: number;
    total_cost: number;
}

export interface ScreeningLog {
    id: number;
    date: string;
    time: string;
    symbol: string;
    rank: number;
    current_price: number;
    dma_25: number;
    percent_below_dma: string;
}

export interface Stats {
    total_trades: number;
    total_cost: number;
    last_screening: ScreeningLog[];
}
