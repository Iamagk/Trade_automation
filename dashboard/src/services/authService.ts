import ControllerService from './controllerService';

class AuthService extends ControllerService {
    public async login(data: { username: string; password: string }): Promise<any> {
        const response = await this.post<any>('/token', data);
        if (response.token && typeof window !== 'undefined') {
            localStorage.setItem('auth_token', response.token);
        }
        return response;
    }

    public async logout(): Promise<void> {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
        }
        await this.post('/logout');
    }

    public async whoami(): Promise<{ username: string }> {
        return this.get<{ username: string }>('/whoami');
    }

    public isAuthenticated(): boolean {
        if (typeof window !== 'undefined') {
            return !!localStorage.getItem('auth_token');
        }
        return false;
    }
}

export const authService = new AuthService();
