import { Controller, Get, Post, Body, UseGuards, UnauthorizedException, Req } from '@nestjs/common';
import { TradingService } from './trading.service';
import type { Request } from 'express';

@Controller('trading')
export class TradingController {
    constructor(private tradingService: TradingService) { }

    @Get('state')
    async getState() {
        return this.tradingService.getSystemState();
    }

    @Post('command')
    async sendCommand(@Body() body: any) {
        const { command, params } = body;
        return this.tradingService.executeCommand(command, params);
    }

    @Post('simulation')
    async toggleSimulation(@Body() body: { enabled: boolean }) {
        return this.tradingService.toggleSimulation(body.enabled);
    }

    @Get('history')
    async getHistory() {
        return this.tradingService.getTradeHistory();
    }

    @Post('manual-trade')
    async manualTrade(@Body() body: { signal: 'BUY_CE' | 'BUY_PE' }) {
        return this.tradingService.manualTrade(body.signal);
    }
}
