import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import cookieParser from 'cookie-parser';
import { Logger } from '@nestjs/common';
import * as dotenv from 'dotenv';
import * as path from 'path';

async function bootstrap() {
  dotenv.config({ path: path.join(__dirname, '../.env') });

  const port = process.env.PORT || 8001;
  const logger = new Logger('Bootstrap');

  const app = await NestFactory.create(AppModule);

  app.use(cookieParser());

  app.enableCors({
    origin: ['http://localhost:3000'],
    credentials: true,
  });

  await app.listen(port);
  logger.log(`Server is running at http://localhost:${port}`);
}
bootstrap();
