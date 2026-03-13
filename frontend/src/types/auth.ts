export interface LoginRequest {
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface TokenData {
  sub: string;
  scopes: string[];
  tenant_id: string;
  roles: string[];
  permissions: string[];
  exp: number;
}
