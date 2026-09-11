import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import * as bcrypt from 'bcrypt';
import * as jwt from 'jsonwebtoken';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class AuthService {
    constructor(
        private prisma: PrismaService,
        private configService: ConfigService,
    ) { }

    async validateUser(username: string, pass: string): Promise<any> {
        const user = await this.prisma.user.findUnique({
            where: { username },
        });
        if (user && (await bcrypt.compare(pass, user.hashedPassword))) {
            const { hashedPassword, ...result } = user;
            return result;
        }
        return null;
    }

    generateToken(user: any): string {
        const payload = { sub: user.username };
        const secret = this.configService.get<string>('JWT_SECRET')!;
        const expiresIn = `${this.configService.get<string>('ACCESS_TOKEN_EXPIRE_MINUTES')}m`;
        return jwt.sign(payload, secret, { expiresIn: expiresIn as any });
    }

    async findByUsername(username: string) {
        return this.prisma.user.findUnique({
            where: { username },
            select: { username: true },
        });
    }
}
