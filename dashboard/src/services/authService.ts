import ControllerService from './controllerService';

class AuthService extends ControllerService {
    public async login(data: { username: string; password: string }): Promise<any> {
        return this.post<any>('/token', data);
    }

    public async logout(): Promise<void> {
        await this.post('/logout');
    }

    public async whoami(): Promise<{ username: string }> {
        return this.get<{ username: string }>('/whoami');
    }
}

export const authService = new AuthService();
