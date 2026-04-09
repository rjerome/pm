import { act, fireEvent, render, screen } from "@testing-library/react";
import { AIChatSidebar } from "@/components/AIChatSidebar";
import { initialData, type BoardData } from "@/lib/kanban";
import { sendAIChatMessage } from "@/lib/boardApi";

vi.mock("@/lib/boardApi", async () => {
  const actual = await vi.importActual<typeof import("@/lib/boardApi")>("@/lib/boardApi");
  return {
    ...actual,
    sendAIChatMessage: vi.fn(),
  };
});

const mockedSendAIChatMessage = vi.mocked(sendAIChatMessage);

const createBoardState = (): BoardData => JSON.parse(JSON.stringify(initialData));

describe("AIChatSidebar", () => {
  beforeEach(() => {
    mockedSendAIChatMessage.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("stops showing Sending when the AI request times out", async () => {
    vi.useFakeTimers();
    mockedSendAIChatMessage.mockImplementation(
      () =>
        new Promise<never>((_, reject) => {
          window.setTimeout(() => {
            reject(new Error("The AI assistant took too long to respond. Please try again."));
          }, 45_000);
        })
    );

    render(
      <AIChatSidebar
        token="pm-mvp-user-token"
        board={createBoardState()}
        onBoardUpdate={vi.fn()}
      />
    );

    fireEvent.change(screen.getByLabelText(/ask the ai assistant/i), {
      target: { value: "Rename backlog to Ideas." },
    });
    fireEvent.click(screen.getByRole("button", { name: /^send$/i }));

    expect(screen.getByRole("button", { name: /sending/i })).toBeDisabled();

    await act(async () => {
      vi.advanceTimersByTime(45_000);
      await Promise.resolve();
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "The AI assistant took too long to respond. Please try again."
    );
    expect(screen.queryByRole("button", { name: /sending/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^send$/i })).toBeDisabled();
  });
});
