vi.mock("@/components/KanbanBoard", () => ({
  KanbanBoard: ({ onLogout }: { onLogout?: () => void }) => (
    <div>
      <h1>Kanban Studio</h1>
      <button type="button" onClick={() => onLogout?.()}>
        Log out
      </button>
    </div>
  ),
}));

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HomeScreen } from "@/components/HomeScreen";
import { AUTH_STORAGE_KEY } from "@/lib/auth";

const mockFetch = vi.fn();

const createStorage = () => {
  const store = new Map<string, string>();

  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => {
      store.clear();
    },
  };
};

describe("HomeScreen", () => {
  beforeEach(() => {
    mockFetch.mockReset();
    vi.stubGlobal("fetch", mockFetch);
    vi.stubGlobal("localStorage", createStorage());
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the login screen when there is no saved token", async () => {
    render(<HomeScreen />);

    expect(
      await screen.findByRole("heading", { name: /sign in to open your kanban workspace/i })
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Kanban Studio" })).not.toBeInTheDocument();
  });

  it("shows an error for an invalid login", async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "Invalid credentials" }),
    });

    render(<HomeScreen />);
    await screen.findByRole("heading", { name: /sign in to open your kanban workspace/i });

    await userEvent.type(screen.getByLabelText("Username"), "user");
    await userEvent.type(screen.getByLabelText("Password"), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid credentials.");
    expect(window.localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  });

  it("requires both username and password before submitting", async () => {
    render(<HomeScreen />);
    await screen.findByRole("heading", { name: /sign in to open your kanban workspace/i });

    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Enter both username and password."
    );
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("signs in and logs out", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ token: "pm-mvp-user-token", username: "user" }),
    });

    render(<HomeScreen />);
    await screen.findByRole("heading", { name: /sign in to open your kanban workspace/i });

    await userEvent.type(screen.getByLabelText("Username"), "user");
    await userEvent.type(screen.getByLabelText("Password"), "password");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("heading", { name: "Kanban Studio" })).toBeInTheDocument();
    expect(window.localStorage.getItem(AUTH_STORAGE_KEY)).toBe("pm-mvp-user-token");

    await userEvent.click(screen.getByRole("button", { name: /log out/i }));

    expect(
      await screen.findByRole("heading", { name: /sign in to open your kanban workspace/i })
    ).toBeInTheDocument();
    expect(window.localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull();
  });

  it("restores a saved session after reload", async () => {
    window.localStorage.setItem(AUTH_STORAGE_KEY, "pm-mvp-user-token");
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ username: "user" }),
    });

    render(<HomeScreen />);

    expect(
      await screen.findByRole("heading", { name: "Kanban Studio" })
    ).toBeInTheDocument();

    await waitFor(() =>
      expect(mockFetch).toHaveBeenCalledWith("/api/auth/me", {
        headers: {
          Authorization: "Bearer pm-mvp-user-token",
        },
      })
    );
  });
});
