import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/client";
import { PasswordInput } from "../components/common";
import { ProtectedRoute } from "../components/layouts";
import { AuthProvider } from "../context/AuthContext";
import { WorkspaceProvider } from "../context/WorkspaceContext";
import { Login, Register } from "../pages/auth";

const ME = { id: 1, email: "a@x.test", first_name: "", memberships: [{ workspace_id: "w1", workspace_name: "Acme", role: "owner" }] };

function mockApi({ meOk = false, post } = {}) {
  vi.spyOn(api, "get").mockImplementation((url) => {
    if (url === "/auth/me/") return meOk ? Promise.resolve({ data: ME }) : Promise.reject({ response: { status: 403, data: {} } });
    return Promise.resolve({ data: {} });
  });
  vi.spyOn(api, "post").mockImplementation(post || (() => Promise.resolve({ data: {} })));
}

function renderAt(path, routes) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider><WorkspaceProvider><Routes>{routes}</Routes></WorkspaceProvider></AuthProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => localStorage.clear());
afterEach(() => vi.restoreAllMocks());

describe("Login", () => {
  it("renders an accessible form with a logo-only header (no site navigation)", async () => {
    mockApi();
    renderAt("/login", <Route path="/login" element={<Login />} />);
    expect(await screen.findByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /tech task logo/i })).toBeInTheDocument();
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  });

  it("shows the server's generic message when credentials are wrong", async () => {
    mockApi({ post: () => Promise.reject({ response: { status: 400, data: { detail: "Invalid email or password." } } }) });
    renderAt("/login", <Route path="/login" element={<Login />} />);
    await userEvent.type(await screen.findByLabelText(/email/i), "a@x.test");
    await userEvent.type(screen.getByLabelText(/^password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /^log in$/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.");
  });

  it("signs in and goes to the app", async () => {
    mockApi({ post: () => Promise.resolve({ data: ME }) });
    renderAt("/login", <>
      <Route path="/login" element={<Login />} />
      <Route path="/app" element={<p>APP HOME</p>} />
    </>);
    await userEvent.type(await screen.findByLabelText(/email/i), "a@x.test");
    await userEvent.type(screen.getByLabelText(/^password/i), "pw");
    await userEvent.click(screen.getByRole("button", { name: /^log in$/i }));
    expect(await screen.findByText("APP HOME")).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith("/auth/login/", { email: "a@x.test", password: "pw" });
  });
});

describe("Register", () => {
  it("rejects mismatched passwords without calling the API", async () => {
    mockApi();
    renderAt("/register", <Route path="/register" element={<Register />} />);
    await userEvent.type(await screen.findByLabelText(/^email/i), "n@x.test");
    await userEvent.type(screen.getByLabelText(/^password$/i), "Str0ng-pass-1");
    await userEvent.type(screen.getByLabelText(/confirm password/i), "different");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));
    expect(await screen.findByText(/do not match/i)).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it("shows server validation errors", async () => {
    mockApi({ post: () => Promise.reject({ response: { status: 400, data: { password: ["This password is too common."] } } }) });
    renderAt("/register", <Route path="/register" element={<Register />} />);
    await userEvent.type(await screen.findByLabelText(/^email/i), "n@x.test");
    await userEvent.type(screen.getByLabelText(/^password$/i), "password123");
    await userEvent.type(screen.getByLabelText(/confirm password/i), "password123");
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));
    expect((await screen.findAllByText(/too common/i)).length).toBeGreaterThan(0);
  });
});

describe("ProtectedRoute (UI convenience only; the backend enforces access)", () => {
  const routes = (
    <>
      <Route path="/login" element={<p>LOGIN PAGE</p>} />
      <Route path="/app" element={<ProtectedRoute><p>SECRET</p></ProtectedRoute>} />
    </>
  );

  it("redirects anonymous visitors to the login page", async () => {
    mockApi({ meOk: false });
    renderAt("/app", routes);
    expect(await screen.findByText("LOGIN PAGE")).toBeInTheDocument();
    expect(screen.queryByText("SECRET")).not.toBeInTheDocument();
  });

  it("renders children for an authenticated user", async () => {
    mockApi({ meOk: true });
    renderAt("/app", routes);
    await waitFor(() => expect(screen.getByText("SECRET")).toBeInTheDocument());
  });
});

describe("PasswordInput", () => {
  it("toggles visibility with an accessible control", async () => {
    render(<PasswordInput id="p" label="Password" value="abc" onChange={() => {}} />);
    const field = screen.getByLabelText(/^password/i);
    expect(field).toHaveAttribute("type", "password");
    await userEvent.click(screen.getByRole("button", { name: /show password/i }));
    expect(field).toHaveAttribute("type", "text");
  });
});
