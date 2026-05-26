import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ConfidenceBadge } from "@/components/fan/confidence-badge";

describe("ConfidenceBadge", () => {
  it("renders High for confidence >= 0.7", () => {
    render(<ConfidenceBadge confidence={0.7} />);
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it("renders High for confidence = 1.0", () => {
    render(<ConfidenceBadge confidence={1.0} />);
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it("renders Medium for confidence = 0.4", () => {
    render(<ConfidenceBadge confidence={0.4} />);
    expect(screen.getByText("Medium")).toBeInTheDocument();
  });

  it("renders Medium for confidence = 0.69", () => {
    render(<ConfidenceBadge confidence={0.69} />);
    expect(screen.getByText("Medium")).toBeInTheDocument();
  });

  it("renders Low for confidence < 0.4", () => {
    render(<ConfidenceBadge confidence={0.39} />);
    expect(screen.getByText("Low")).toBeInTheDocument();
  });

  it("renders Low for confidence = 0.0", () => {
    render(<ConfidenceBadge confidence={0.0} />);
    expect(screen.getByText("Low")).toBeInTheDocument();
  });

  it("applies green styling for High", () => {
    const { container } = render(<ConfidenceBadge confidence={0.8} />);
    expect(container.firstChild).toHaveClass("bg-green-100");
  });

  it("applies amber styling for Medium", () => {
    const { container } = render(<ConfidenceBadge confidence={0.5} />);
    expect(container.firstChild).toHaveClass("bg-amber-100");
  });

  it("applies red styling for Low", () => {
    const { container } = render(<ConfidenceBadge confidence={0.1} />);
    expect(container.firstChild).toHaveClass("bg-red-100");
  });
});
