import { randomInt } from 'node:crypto';

const CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
const CODE_LENGTH = 7;

export const CODE_PATTERN = /^[A-Za-z0-9]{7}$/;

export function generateCode(): string {
  let code = '';
  for (let i = 0; i < CODE_LENGTH; i += 1) {
    code += CHARSET[randomInt(CHARSET.length)];
  }
  return code;
}
