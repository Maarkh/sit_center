export interface LoginRequest {
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

// Identity returned by GET /auth/me. With httpOnly-cookie auth the SPA can't
// decode the JWT itself, so it relies on this for UI / route-guard decisions.
export interface UserInfo {
  username: string;
  scopes: string[];
  roles: string[];
  permissions: string[];
  tenant_id: string;
}

export interface TokenData {
  sub: string;
  scopes: string[];
  tenant_id: string;
  roles: string[];
  permissions: string[];
  exp: number;
}
