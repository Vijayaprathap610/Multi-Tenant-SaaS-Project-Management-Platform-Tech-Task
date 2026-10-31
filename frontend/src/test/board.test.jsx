import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Outlet, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/client";
import { computeMoveToIndex } from "../kanban/logic";
import BoardPage from "../pages/project/BoardPage";

// The drag interaction itself is covered by Playwright (e2e/kanban.spec.js). Here the board
// component is replaced by a stub that performs the same calls a real drop performs, so we can
// verify what BoardPage does with them: optimistic update, persistence, rollback and messaging.
vi.mock("../kanban/KanbanBoard", () => ({
  default: ({ columns, setColumns, onMove }) => (
    <div>
      {columns.map((c) => (
        <section key={c.id} data-testid={`col-${c.id}`}>{c.issues.map((i) => <div key={i.id}>{i.key}</div>)}</section>
      ))}
      <button onClick={() => { const m = computeMoveToIndex(columns, "i1", "c2", 0); setColumns(m.newColumns); onMove({ issueId: "i1", ...m }, columns); }}>
        drop-i1-on-c2
      </button>
    </div>
  ),
}));

const KANBAN = {
  id: "b1", name: "Main", truncated: false,
  columns: [
    { id: "c1", name: "To Do", status_id: "s1", category: "todo", issues: [{ id: "i1", key: "PRJ-1", title: "One", status_id: "s1", priority: "low" }] },
    { id: "c2", name: "Done", status_id: "s2", category: "done", issues: [] },
  ],
};

function setup() {
  vi.spyOn(api, "get").mockImplementation((url) => {
    if (url.endsWith("/boards/")) return Promise.resolve({ data: { results: [{ id: "b1" }] } });
    if (url.includes("/kanban/")) return Promise.resolve({ data: KANBAN });
    return Promise.resolve({ data: {} });
  });
  const ctx = { base: "/workspaces/w/projects/p", members: [], statuses: [] };
  render(
    <MemoryRouter initialEntries={["/board"]}>
      <Routes><Route element={<Outlet context={ctx} />}><Route path="/board" element={<BoardPage />} /></Route></Routes>
    </MemoryRouter>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("BoardPage moves", () => {
  it("persists a move through the API with the target status and position", async () => {
    vi.spyOn(api, "post").mockResolvedValue({ data: {} });
    setup();
    await userEvent.click(await screen.findByText("drop-i1-on-c2"));
    expect(within(screen.getByTestId("col-c2")).getByText("PRJ-1")).toBeInTheDocument(); // optimistic
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/workspaces/w/projects/p/issues/i1/move/", { status: "s2", before_issue_id: null }));
  });

  it("restores the previous state and explains the rejection when the backend refuses", async () => {
    vi.spyOn(api, "post").mockRejectedValue({ response: { status: 400, data: { status: ["Transition from 'To Do' to 'Done' is not allowed."] } } });
    setup();
    await userEvent.click(await screen.findByText("drop-i1-on-c2"));
    expect(await screen.findByRole("alert")).toHaveTextContent(/move rejected/i);
    expect(screen.getByRole("alert")).toHaveTextContent(/not allowed/i);
    expect(within(screen.getByTestId("col-c1")).getByText("PRJ-1")).toBeInTheDocument();
    expect(within(screen.getByTestId("col-c2")).queryByText("PRJ-1")).not.toBeInTheDocument();
  });

  it("restores the previous state and shows a network error when the request fails", async () => {
    vi.spyOn(api, "post").mockRejectedValue({ message: "Network Error" });
    setup();
    await userEvent.click(await screen.findByText("drop-i1-on-c2"));
    expect(await screen.findByRole("alert")).toHaveTextContent(/network error/i);
    expect(within(screen.getByTestId("col-c1")).getByText("PRJ-1")).toBeInTheDocument();
  });
});
