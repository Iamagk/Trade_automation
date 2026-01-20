import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ControllerService {
    protected api: AxiosInstance;

    constructor() {
        this.api = axios.create({
            baseURL: NEXT_PUBLIC_API_URL,
            withCredentials: true,  // Enable cookies
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Global response interceptor for auth errors
        this.api.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status === 401) {
                    if (typeof window !== 'undefined' &&
                        !window.location.pathname.includes('/login')) {
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

    protected async post<T, D = any>(
        url: string,
        data?: D,
        config?: AxiosRequestConfig
    ): Promise<T> {
        const response: AxiosResponse<T> = await this.api.post(url, data, config);
        return response.data;
    }

    protected async put<T, D = any>(
        url: string,
        data?: D,
        config?: AxiosRequestConfig
    ): Promise<T> {
        const response: AxiosResponse<T> = await this.api.put(url, data, config);
        return response.data;
    }

    protected async patch<T, D = any>(
        url: string,
        data?: D,
        config?: AxiosRequestConfig
    ): Promise<T> {
        const response: AxiosResponse<T> = await this.api.patch(url, data, config);
        return response.data;
    }

    protected async delete<T>(
        url: string,
        config?: AxiosRequestConfig
    ): Promise<T> {
        const response: AxiosResponse<T> = await this.api.delete(url, config);
        return response.data;
    }
}

export default ControllerService;
