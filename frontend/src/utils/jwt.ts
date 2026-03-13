import { jwtDecode } from 'jwt-decode';
import type { TokenData } from '@/types/auth';

export function decodeToken(token: string): TokenData {
  return jwtDecode<TokenData>(token);
}

export function isTokenExpired(token: string): boolean {
  try {
    const decoded = decodeToken(token);
    return decoded.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}
