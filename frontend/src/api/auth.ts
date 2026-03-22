import apiClient from "./client";
import type { AuthSession, LoginRequest, SetupStatus, SetupInitResponse, HealthStatus } from "./types";

export async function login(data: LoginRequest): Promise<AuthSession> {
  const res = await apiClient.post<AuthSession>("/auth/login", data);
  return res.data;
}

export async function revokeToken(token: string): Promise<void> {
  await apiClient.post("/auth/revoke", { token });
}

export async function getSetupStatus(): Promise<SetupStatus> {
  const res = await apiClient.get<SetupStatus>("/setup/status");
  return res.data;
}

export async function setupInit(password: string): Promise<SetupInitResponse> {
  const res = await apiClient.post<SetupInitResponse>("/setup/init", { password });
  return res.data;
}

export async function getHealth(): Promise<HealthStatus> {
  const res = await apiClient.get<HealthStatus>("/health");
  return res.data;
}
