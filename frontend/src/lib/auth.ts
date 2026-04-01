export const AUTH_STORAGE_KEY = "pm-auth-token";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export type LoginResult = {
  token: string;
  username: string;
};

export const login = async (
  username: string,
  password: string
): Promise<LoginResult> => {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error("Invalid credentials");
  }

  return response.json();
};

export const verifyToken = async (token: string): Promise<string> => {
  const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Unauthorized");
  }

  const data = (await response.json()) as { username: string };
  return data.username;
};
