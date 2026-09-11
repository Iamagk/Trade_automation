import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcrypt';
import * as dotenv from 'dotenv';
import * as path from 'path';

dotenv.config({ path: path.join(__dirname, '../.env') });

const prisma = new PrismaClient();

async function main() {
  const hashedPassword = await bcrypt.hash('trading_password', 10);
  const user = await prisma.user.upsert({
    where: { username: 'trading_user' },
    update: {},
    create: {
      username: 'trading_user',
      hashedPassword: hashedPassword,
    },
  });
  console.log('Seeded user:', user.username);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
