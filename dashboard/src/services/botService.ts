import ControllerService from './controllerService';
import { BotStatus } from './types';

class BotService extends ControllerService {
    public async getStatus(): Promise<BotStatus> {
        return this.get<BotStatus>('/bot/status');
    }

    public async getLogs(): Promise<{ logs: string[] }> {
        return this.get<{ logs: string[] }>('/bot/logs');
    }

    public async startBot(mode: string): Promise<{ status: string; mode: string }> {
        return this.post<{ status: string; mode: string }>('/bot/start', { mode });
    }

    public async stopBot(): Promise<{ status: string }> {
        return this.post<{ status: string }>('/bot/stop', {});
    }

    public async sendInput(input: string): Promise<{ status: string }> {
        return this.post<{ status: string }>('/bot/input', { input });
    }
}

export const botService = new BotService();
