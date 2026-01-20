import ControllerService from './controllerService';
import { Stats } from './types';

class StatsService extends ControllerService {
    public async getStats(): Promise<Stats> {
        return this.get<Stats>('/stats');
    }
}

export const statsService = new StatsService();
