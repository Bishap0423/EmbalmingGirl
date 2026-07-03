import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { App } from "./App";

test("renders the project title", () => {
  localStorage.clear();
  render(<App />);

  expect(screen.getByRole("heading", { name: "冰冷的她醒来之前" })).toBeInTheDocument();
  expect(screen.getByLabelText("你的名字")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "创建房间" })).toBeEnabled();
  expect(screen.getByRole("button", { name: "加入房间" })).toBeEnabled();
});
