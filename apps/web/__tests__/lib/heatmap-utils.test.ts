import { describe, it, expect } from "vitest";
import { hotspotRadius, scoreColor, confidenceLevel } from "@/lib/heatmap-utils";

describe("hotspotRadius", () => {
  it("returns minimum radius for supporter_count = 0", () => {
    expect(hotspotRadius(0)).toBe(8);
  });

  it("returns minimum radius for negative input", () => {
    expect(hotspotRadius(-5)).toBe(8);
  });

  it("returns a larger radius for positive supporter counts", () => {
    expect(hotspotRadius(100)).toBeGreaterThan(8);
  });

  it("grows with supporter count (monotone)", () => {
    expect(hotspotRadius(100)).toBeGreaterThan(hotspotRadius(25));
    expect(hotspotRadius(25)).toBeGreaterThan(hotspotRadius(1));
  });
});

describe("scoreColor", () => {
  it("returns a valid rgb string at score 0", () => {
    expect(scoreColor(0)).toMatch(/^rgb\(\d+,\d+,\d+\)$/);
  });

  it("returns a valid rgb string at score 100", () => {
    expect(scoreColor(100)).toMatch(/^rgb\(\d+,\d+,\d+\)$/);
  });

  it("returns a different color at score 0 vs score 100", () => {
    expect(scoreColor(0)).not.toBe(scoreColor(100));
  });

  it("returns a different color at score 0 vs score 50", () => {
    expect(scoreColor(0)).not.toBe(scoreColor(50));
  });

  it("clamps scores below 0", () => {
    expect(scoreColor(-10)).toBe(scoreColor(0));
  });

  it("clamps scores above 100", () => {
    expect(scoreColor(110)).toBe(scoreColor(100));
  });
});

describe("confidenceLevel", () => {
  it("returns High for confidence >= 0.7", () => {
    expect(confidenceLevel(0.7)).toBe("High");
    expect(confidenceLevel(1.0)).toBe("High");
    expect(confidenceLevel(0.85)).toBe("High");
  });

  it("returns Medium for confidence in [0.4, 0.7)", () => {
    expect(confidenceLevel(0.4)).toBe("Medium");
    expect(confidenceLevel(0.69)).toBe("Medium");
    expect(confidenceLevel(0.55)).toBe("Medium");
  });

  it("returns Low for confidence < 0.4", () => {
    expect(confidenceLevel(0.0)).toBe("Low");
    expect(confidenceLevel(0.39)).toBe("Low");
    expect(confidenceLevel(0.2)).toBe("Low");
  });

  it("handles boundary values correctly", () => {
    expect(confidenceLevel(0.39)).toBe("Low");
    expect(confidenceLevel(0.40)).toBe("Medium");
    expect(confidenceLevel(0.69)).toBe("Medium");
    expect(confidenceLevel(0.70)).toBe("High");
  });
});
