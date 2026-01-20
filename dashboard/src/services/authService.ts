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

    public isAuthenticated(): boolean {
        // With HttpOnly cookies, we primarily rely on backend validation 401s
        // But we can check if we have a successful 'whoami' cached or similar.
        // For now, return true and let 401 interceptor handle it.
        return true;
    }
}

export const authService = new AuthService();
