import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import fs from 'fs';

export type BotStatus = 'IDLE' | 'RUNNING' | 'ERROR';

interface BotState {
    status: BotStatus;
    logs: string[];
    pid: number | null;
    startTime: Date | null;
    mode: 'dry-run' | 'real' | null;
}

class BotManager {
    private static instance: BotManager;
    private state: BotState = {
        status: 'IDLE',
        logs: [],
        pid: null,
        startTime: null,
        mode: null
    };
    private process: ChildProcess | null = null;
    private readonly MAX_LOGS = 200;

    private constructor() { }

    public static getInstance(): BotManager {
        if (!BotManager.instance) {
            BotManager.instance = new BotManager();
        }
        return BotManager.instance;
    }

    private addLog(message: string) {
        const timestamp = new Date().toISOString();
        const logEntry = `[${timestamp}] ${message}`;
        this.state.logs.push(logEntry);
        if (this.state.logs.length > this.MAX_LOGS) {
            this.state.logs.shift();
        }
    }

    public start(mode: string) {
        if (this.state.status === 'RUNNING') {
            throw new Error('Bot is already running');
        }

        let projectRoot = path.resolve(__dirname, '../../');
        // If we are in 'server/dist/services', go up one more level
        if (__dirname.includes(path.join('server', 'dist')) || __dirname.includes('dist')) {
            projectRoot = path.resolve(__dirname, '../../../');
        }

        // Final sanity check: if 'src' doesn't exist here, we might be in the compiled 'dist' folder structure
        if (!fs.existsSync(path.join(projectRoot, 'src')) && fs.existsSync(path.resolve(projectRoot, '../src'))) {
            projectRoot = path.resolve(projectRoot, '../');
        }

        // Auto-detect virtual environment
        let pythonPath = process.env.PYTHON_PATH;
        if (!pythonPath) {
            const venvPath = path.join(projectRoot, '.venv');
            const binPath = process.platform === 'win32'
                ? path.join(venvPath, 'Scripts', 'python.exe')
                : path.join(venvPath, 'bin', 'python3');

            if (fs.existsSync(binPath)) {
                pythonPath = binPath;
            } else {
                pythonPath = 'python3';
            }
        }

        const args = [];
        let displayMode = mode;

        if (mode === 'login') {
            args.push('-m', 'src.main', '--login');
            displayMode = 'login';
        } else {
            // mode can be: run_now_dry, schedule_dry, run_now_real, schedule_real
            args.push('-m', 'src.main');

            if (mode.includes('run_now')) {
                args.push('--run-now');
            } else if (mode.includes('schedule')) {
                args.push('--schedule');
            }

            if (mode.includes('real')) {
                args.push('--real');
            } else {
                args.push('--dry-run');
            }
        }

        this.addLog(`Starting bot with command: ${pythonPath} ${args.join(' ')}`);
        this.process = spawn(pythonPath, args, {
            cwd: projectRoot,
            env: { ...process.env, PYTHONPATH: projectRoot }
        });

        this.state.status = 'RUNNING';
        this.state.pid = this.process.pid || null;
        this.state.startTime = new Date();
        this.state.mode = (displayMode as any);

        this.process.stdout?.on('data', (data) => {
            const output = data.toString().trim();
            if (output) this.addLog(output);
        });

        this.process.stderr?.on('data', (data) => {
            const output = data.toString().trim();
            if (output) this.addLog(`Error: ${output}`);
        });

        this.process.on('close', (code) => {
            this.addLog(`Bot process exited with code ${code}`);
            this.state.status = 'IDLE';
            this.state.pid = null;
            this.state.startTime = null;
            this.process = null;
        });

        this.process.on('error', (err) => {
            this.addLog(`Failed to start bot: ${err.message}`);
            this.state.status = 'ERROR';
            this.state.pid = null;
            this.process = null;
        });
    }

    public stop() {
        if (!this.process) {
            this.addLog('No bot process running to stop.');
            return;
        }

        this.addLog('Stopping bot process...');
        this.process.kill();
    }

    public sendInput(input: string) {
        if (!this.process || !this.process.stdin) {
            throw new Error('No bot process running or stdin is closed');
        }

        this.addLog(`Sending input: ${input}`);
        this.process.stdin.write(input + '\n');
    }

    public getStatus() {
        return {
            status: this.state.status,
            pid: this.state.pid,
            startTime: this.state.startTime,
            mode: this.state.mode,
            logCount: this.state.logs.length
        };
    }

    public getLogs() {
        return this.state.logs;
    }
}

export const botManager = BotManager.getInstance();
