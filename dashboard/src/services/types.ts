export interface BotStatus {
    is_running: boolean;
    mode: string | null;
    pid: number | null;
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
