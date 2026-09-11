import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

class ControllerService {
    protected api: AxiosInstance;

    constructor() {
        this.api = axios.create({
            baseURL: NEXT_PUBLIC_API_URL,
            withCredentials: true,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        this.api.interceptors.response.use(
            (response) => {
                console.log(`[Dashboard API] Response from ${response.config.url}:`, response.data);
                return response;
            },
            (error) => {
                console.error(`[Dashboard API] Error from ${error.config?.url}:`, error.message);
                if (error.response?.status === 401) {
                    if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
                        window.location.href = '/login';
                    }
                }
                return Promise.reject(error);
            }
        );
    }

    protected async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
        const response: AxiosResponse<T> = await this.api.get(url, config);
        return response.data;
    }

    protected async post<T, D = any>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
        const response: AxiosResponse<T> = await this.api.post(url, data, config);
        return response.data;
    }
}

export default ControllerService;
