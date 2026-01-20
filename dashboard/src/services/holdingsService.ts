import ControllerService from './controllerService';

export interface Holding {
    symbol: string;
    quantity: number;
    average_price: number;
    current_price: number;
}

class HoldingsService extends ControllerService {
    public async getHoldings(): Promise<Holding[]> {
        return this.get<Holding[]>('/holdings');
    }
}

export const holdingsService = new HoldingsService();
