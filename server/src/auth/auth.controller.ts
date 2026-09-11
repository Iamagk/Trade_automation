import { Controller, Post, Body, Res, Get, Req, UnauthorizedException } from '@nestjs/common';
import { AuthService } from './auth.service';
import type { Response, Request } from 'express';
import { ConfigService } from '@nestjs/config';

@Controller()
export class AuthController {
    constructor(
        private authService: AuthService,
        private configService: ConfigService,
    ) { }

    @Post('token')
    async login(@Body() body: any, @Res() res: Response) {
        const { username, password } = body;
        const user = await this.authService.validateUser(username, password);
        if (!user) {
            throw new UnauthorizedException('Incorrect username or password');
        }

        const token = this.authService.generateToken(user);
        const expireMinutes = parseInt(this.configService.get<string>('ACCESS_TOKEN_EXPIRE_MINUTES') || '60');

        res.cookie('token', token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax',
            maxAge: expireMinutes * 60 * 1000,
        });

        return res.json({
            status: 'success',
            username: user.username,
        });
    }

    @Post('logout')
    logout(@Res() res: Response) {
        res.clearCookie('token');
        return res.json({ status: 'success' });
    }

    @Get('whoami')
    async whoami(@Req() req: Request) {
        const token = req.cookies['token'];
        if (!token) {
            throw new UnauthorizedException('No token provided');
        }

        try {
            const secret = this.configService.get<string>('JWT_SECRET')!;
            const decoded = require('jsonwebtoken').verify(token, secret) as { sub: string };
            const user = await this.authService.findByUsername(decoded.sub);
            if (!user) {
                throw new UnauthorizedException('Invalid user');
            }
            return user;
        } catch (e) {
            throw new UnauthorizedException('Invalid or expired token');
        }
    }
}
