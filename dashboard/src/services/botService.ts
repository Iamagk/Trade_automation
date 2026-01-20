import ControllerService from './controllerService';
import { BotStatus } from './types';

class BotService extends ControllerService {
    public async getStatus(): Promise<BotStatus> {
        // return this.get<BotStatus>('/bot/status');
        // Stub for migration
        return { is_running: false, mode: null, pid: null };
    }

    public async getLogs(): Promise<{ logs: string[] }> {
        // return this.get<{ logs: string[] }>('/bot/logs');
        return { logs: ["Migration in progress... Bot logic paused."] };
    }

    public async startBot(mode: string): Promise<{ status: string; mode: string }> {
        // return this.post<{ status: string; mode: string }>('/bot/start', { mode });
        throw new Error("Bot control not yet migrated to Node.js backend.");
    }

    public async stopBot(): Promise<{ status: string }> {
        // return this.post<{ status: string }>('/bot/stop', {});
        throw new Error("Bot control not yet migrated.");
    }

    public async sendInput(input: string): Promise<{ status: string }> {
        // return this.post<{ status: string }>('/bot/input', { input });
        throw new Error("Bot control not yet migrated.");
    }
}

export const botService = new BotService();
