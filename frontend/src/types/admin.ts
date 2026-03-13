export interface TenantRead {
  id: string;
  name: string;
  is_active: boolean;
}

export interface TenantCreate {
  id: string;
  name: string;
}

export interface UserRead {
  id: string;
  username: string;
  email: string | null;
  tenant_id: string;
  is_active: boolean;
  auth_provider: string;
}

export interface UserCreate {
  username: string;
  email?: string;
  password?: string;
  tenant_id?: string;
}

export interface RoleRead {
  id: string;
  name: string;
  tenant_id: string;
  permissions: string[];
  description: string | null;
}

export interface RoleCreate {
  name: string;
  tenant_id?: string;
  permissions: string[];
  description?: string;
}
