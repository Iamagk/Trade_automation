import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PrismaService } from '../prisma/prisma.service';
import axios from 'axios';

@Injectable()
export class TradingService {
    private readonly logger = new Logger(TradingService.name);
    private engineUrl: string;

    constructor(
        private configService: ConfigService,
        private prisma: PrismaService,
    ) {
        this.engineUrl = this.configService.get<string>('PY_ENGINE_URL') || 'http://localhost:8000';
    }

    async getSystemState() {
        try {
            const response = await axios.get(`${this.engineUrl}/api/state`);
            const data = response.data;

            this.logger.debug(`Raw data from Python: ${JSON.stringify(data)}`);

            // The button should only be "Stop" if the websocket is actually connected.
            // If the websocket is disconnected, the user must be able to click "Start".
            const transformed = {
                running: data.running || false,
                starting: (data.is_started && !data.running) || false,
                engine_state: data.engine_state || 'UNKNOWN',
                pnl: data.risk?.daily_pnl || 0,
                strategy: data.tpb_strategy?.trend || (data.orb_levels?.established ? 'ORB Established' : 'TPB Trend'),
                positions: data.position?.position ? [data.position.position] : [],
                risk: data.risk || {},
                tpb: data.tpb_strategy || {},
                chart: data.chart_data || []
            };

            this.logger.debug(`Transformed data for frontend: ${JSON.stringify(transformed)}`);
            return transformed;
        } catch (e) {
            this.logger.error(`Error fetching system state: ${e.message}`);
            throw e;
        }
    }

    async executeCommand(command: string, params: any = {}) {
        try {
            const response = await axios.post(`${this.engineUrl}/api/command`, {
                command,
                params,
            });
            return response.data;
        } catch (e) {
            this.logger.error(`Error executing command ${command}: ${e.message}`);
            throw e;
        }
    }

    async toggleSimulation(enabled: boolean) {
        try {
            const response = await axios.post(`${this.engineUrl}/api/simulation/toggle?enabled=${enabled}`);
            return response.data;
        } catch (e) {
            this.logger.error(`Error toggling simulation: ${e.message}`);
            throw e;
        }
    }

    async manualTrade(signal: 'BUY_CE' | 'BUY_PE') {
        try {
            const response = await axios.post(`${this.engineUrl}/api/trade/manual?signal_type=${signal}`);
            return response.data;
        } catch (e) {
            this.logger.error(`Error triggering manual trade ${signal}: ${e.message}`);
            throw e;
        }
    }

    async getTradeHistory() {
        return this.prisma.trade.findMany({
            orderBy: { date: 'desc' },
            take: 50,
        });
    }
}
