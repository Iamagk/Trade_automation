import ControllerService from './controllerService';
import { Trade } from './types';

class TradeService extends ControllerService {
    public async getTrades(): Promise<Trade[]> {
        return this.get<Trade[]>('/trades');
    }
}

export const tradeService = new TradeService();
