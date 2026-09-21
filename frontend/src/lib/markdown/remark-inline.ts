import type { PhrasingContent, Root, RootContent } from "mdast";
import type { Plugin } from "unified";

// Criterion names live inside headings/strong elements. Flatten block content
// before rendering so pasted Markdown can never produce invalid nested blocks.
const remarkInline: Plugin<[], Root> = () => (tree) => {
  function flatten(node: RootContent): PhrasingContent[] {
    if (node.type === "math" || node.type === "inlineMath") {
      return [
        {
          type: "inlineMath",
          value: node.value,
          data: {
            hName: "code",
            hProperties: { className: ["math-inline"] },
            hChildren: [{ type: "text", value: node.value }],
          },
        },
      ];
    }
    if (node.type === "code")
      return [{ type: "inlineCode", value: node.value }];
    if (node.type === "definition" || node.type === "thematicBreak") return [];
    if (
      node.type === "emphasis" ||
      node.type === "strong" ||
      node.type === "delete" ||
      node.type === "link" ||
      node.type === "linkReference"
    ) {
      return [{ ...node, children: node.children.flatMap(flatten) }];
    }
    if (
      [
        "paragraph",
        "heading",
        "blockquote",
        "list",
        "listItem",
        "table",
        "tableRow",
        "tableCell",
      ].includes(node.type) &&
      "children" in node
    ) {
      return node.children.flatMap((child, index) => [
        ...(index && node.type !== "paragraph" && node.type !== "heading"
          ? [{ type: "text" as const, value: " " }]
          : []),
        ...flatten(child),
      ]);
    }
    return [node as PhrasingContent];
  }
  const definitions = tree.children.filter(
    (node) => node.type === "definition",
  );
  const children = tree.children.flatMap((node, index) => [
    ...(index ? [{ type: "text" as const, value: " " }] : []),
    ...flatten(node),
  ]);
  tree.children = [...definitions, { type: "paragraph", children }];
};

export default remarkInline;
