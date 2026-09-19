"use client";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

export function TutorMarkdown({ content }: { content: string }) {
  return (
    <div dir="auto" className="tutor-markdown min-w-0 break-words">
      <Markdown
        skipHtml
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[
          [rehypeKatex, { trust: false, strict: "warn", maxExpand: 1000 }],
        ]}
        components={{
          img: () => null,
          a: ({ href, children }) =>
            /^https?:\/\//i.test(href || "") ? (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="underline text-teal-800"
              >
                {children}
              </a>
            ) : (
              <span>{children}</span>
            ),
          pre: ({ children }) => (
            <pre
              dir="ltr"
              className="overflow-x-auto rounded-lg bg-slate-100 p-3 text-sm"
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
    </div>
  );
}
