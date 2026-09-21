import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render } from "@testing-library/react";
import { AcademicMarkdown } from "../src/components/academic-markdown";

afterEach(cleanup);

describe("academic Markdown math", () => {
  it.each([
    ["dollar inline", "$x^2$", false],
    ["dollar block", "$$\n\\sum_{i=1}^{n} i\n$$", true],
    ["LaTeX inline", String.raw`Before \(\frac{1}{2}\) after`, false],
    ["LaTeX display", String.raw`Before \[\sqrt{x}\] after`, true],
    [
      "multiline matrix",
      "\\[\n\\begin{pmatrix}1 & 2 \\\\\n3 & 4\\end{pmatrix}\n\\]",
      true,
    ],
    ["math fence", "```math\nx^2\n```", true],
    ["Arabic inline", String.raw`احسب \(x^2 + y^2\) ثم اشرح`, false],
    ["list", String.raw`- Evaluate \(x^2\)`, false],
    ["blockquote", "> \\[\n> x^2\n> \\]", true],
    ["table", "| Value |\n| --- |\n| \\(x^2\\) |", false],
  ])("renders %s with accessible math", (_name, content, display) => {
    const { container } = render(
      <AcademicMarkdown content={content as string} />,
    );
    expect(container.querySelectorAll(".katex")).toHaveLength(1);
    expect(container.querySelector("math")).not.toBeNull();
    expect(container.querySelector(".katex-error")).toBeNull();
    expect(!!container.querySelector(".katex-display")).toBe(display);
  });

  it.each([
    String.raw`\(x^2`,
    String.raw`\[x^2`,
    String.raw`x^2\)`,
    String.raw`x^2\]`,
  ])("keeps incomplete delimiters readable: %s", (content) => {
    const { container } = render(<AcademicMarkdown content={content} />);
    expect(container.textContent).toBe(content);
    expect(container.querySelector(".katex")).toBeNull();
  });

  it("preserves code, escapes, destinations and ordinary Markdown", () => {
    const code = String.raw`\(x\) $y$ \[z\]`;
    const content = [
      "`" + code + "`",
      "```tex\n" + code + "\n```",
      "    " + code,
      String.raw`\\(literal\\) and \\[literal\\] and \$5`,
      String.raw`[link](https://example.com/\(value\))`,
      "**Strong** and *emphasis*",
    ].join("\n\n");
    const { container } = render(<AcademicMarkdown content={content} />);
    expect(container.querySelector(".katex")).toBeNull();
    expect(
      [...container.querySelectorAll("code")].map((node) =>
        node.textContent?.trim(),
      ),
    ).toEqual([code, code, code]);
    expect(container.textContent).toContain(
      String.raw`\(literal\) and \[literal\] and $5`,
    );
    expect(container.querySelector("a")).toHaveAttribute(
      "href",
      "https://example.com/(value)",
    );
    expect(container.querySelector("strong")).toHaveTextContent("Strong");
  });

  it("renders multiple syntaxes without consuming neighboring expressions", () => {
    const { container } = render(
      <AcademicMarkdown content={String.raw`$a$ \(b\) \[c\] \(d\)`} />,
    );
    expect(container.querySelectorAll(".katex")).toHaveLength(4);
    expect(container.querySelectorAll("annotation")).toHaveLength(4);
  });

  it("shows malformed math source and keeps surrounding prose", () => {
    const { container } = render(
      <AcademicMarkdown content={String.raw`Before \(\frac{\) after`} />,
    );
    expect(container.querySelector(".katex-error")).toHaveTextContent(
      String.raw`\frac{`,
    );
    expect(container.textContent).toContain("Before");
    expect(container.textContent).toContain("after");
  });

  it("blocks HTML, tracking images and untrusted math commands", () => {
    const { container } = render(
      <AcademicMarkdown
        content={String.raw`
<script>alert(1)</script>

![pixel](https://example.com/pixel)

[bad](javascript:alert%281%29)

\(\href{javascript:alert(1)}{click}\)

\(\includegraphics{https://example.com/pixel}\)

\(\htmlStyle{background:url(https://example.com/pixel)}{x}\)
`}
      />,
    );
    expect(container.querySelector("script, img, a")).toBeNull();
    expect(container.querySelector('[style*="background"]')).toBeNull();
  });

  it("flattens criterion names to valid inline markup", () => {
    const { container } = render(
      <strong>
        <AcademicMarkdown
          inline
          content={"# **Name** \\(x^2\\)\n\n$$\ny^2\n$$\n\n- item"}
        />
      </strong>,
    );
    expect(
      container.querySelector("div, p, pre, h1, ul, li, .katex-display"),
    ).toBeNull();
    expect(container.querySelectorAll(".katex")).toHaveLength(2);
    expect(container.textContent).toContain("Name");
  });

  it("keeps display syntax inline inside formatted criterion names", () => {
    const { container } = render(
      <AcademicMarkdown
        inline
        content={String.raw`**\[x^2\]** and *\[y^2\]*`}
      />,
    );
    expect(container.querySelectorAll(".katex")).toHaveLength(2);
    expect(container.querySelector(".katex-display")).toBeNull();
  });

  it("does not cross a code fence when a display opener is incomplete", () => {
    const { container } = render(
      <AcademicMarkdown content={"\\[\n\n```js\n\\]\n```"} />,
    );
    expect(container.querySelector(".katex")).toBeNull();
    expect(container.querySelector("pre")).toHaveTextContent(String.raw`\]`);
  });

  it("preserves newlines and row separators in the math source", () => {
    const source =
      String.raw`\begin{pmatrix}1 & 2 \\` +
      "\n" +
      String.raw`3 & 4\end{pmatrix}`;
    const { container } = render(
      <AcademicMarkdown content={"\\[" + source + "\\]"} />,
    );
    expect(container.querySelector("annotation")?.textContent).toBe(source);
  });
});
