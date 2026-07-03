import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { App } from "./App";

test("renders the project title", () => {
  render(<App />);

  expect(screen.getByRole("heading", { name: "冰冷的她醒来之前" })).toBeInTheDocument();
});
