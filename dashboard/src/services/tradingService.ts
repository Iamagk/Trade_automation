import ControllerService from './controllerService';

class TradingService extends ControllerService {
    public async getState(): Promise<any> {
        return this.get<any>('/trading/state');
    }

    public async sendCommand(command: string, params: any = {}): Promise<any> {
        return this.post<any>('/trading/command', { command, params });
    }

    public async toggleSimulation(enabled: boolean): Promise<any> {
        return this.post<any>('/trading/simulation', { enabled });
    }

    public async getHistory(): Promise<any[]> {
        return this.get<any[]>('/trading/history');
    }

    public async triggerManualTrade(signal: 'BUY_CE' | 'BUY_PE'): Promise<any> {
        return this.post<any>('/trading/manual-trade', { signal });
    }
}

export const tradingService = new TradingService();
