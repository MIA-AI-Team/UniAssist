"use client";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import remarkLatex from "@/lib/markdown/remark-latex";
import remarkInline from "@/lib/markdown/remark-inline";
import "katex/dist/katex.min.css";

export function AcademicMarkdown({
  content,
  className = "",
  inline = false,
}: {
  content: string;
  className?: string;
  inline?: boolean;
}) {
  const Wrapper = inline ? "span" : "div";
  return (
    <Wrapper
      dir="auto"
      className={`academic-markdown min-w-0 break-words ${className}`}
    >
      <Markdown
        skipHtml
        remarkPlugins={[
          remarkGfm,
          remarkMath,
          remarkLatex,
          ...(inline ? [remarkInline] : []),
        ]}
        rehypePlugins={[
          [rehypeKatex, { trust: false, strict: "warn", maxExpand: 1000 }],
        ]}
        components={{
          ...(inline
            ? {
                p: ({ children }: { children?: React.ReactNode }) => (
                  <span>{children}</span>
                ),
              }
            : {}),
          img: () => null,
          a: ({ href, children }) =>
            /^https?:\/\//i.test(href || "") ? (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="underline text-action"
              >
                {children}
              </a>
            ) : (
              <span>{children}</span>
            ),
          pre: ({ children }) => (
            <pre
              dir="ltr"
              className="overflow-x-auto rounded-lg bg-surface-subtle p-3 text-sm"
            >
              {children}
            </pre>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto">
              <table>{children}</table>
            </div>
          ),
        }}
      >
        {content}
      </Markdown>
    </Wrapper>
  );
}
