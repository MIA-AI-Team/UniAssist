import type { Root } from "mdast";
import type { Extension as FromMarkdownExtension } from "mdast-util-from-markdown";
import type { Construct, Extension, State, Token } from "micromark-util-types";
import type { Plugin } from "unified";

declare module "micromark-util-types" {
  interface TokenTypeMap {
    academicMath: "academicMath";
    academicMathLiteral: "academicMathLiteral";
    academicMathData: "academicMathData";
    academicMathSequence: "academicMathSequence";
  }
}

// Parse before CommonMark's character escapes. Code and link destinations are
// handled by their own Markdown constructs and never pass through this parser.
const math: Construct = {
  name: "academicMath",
  tokenize(effects, ok, nok) {
    let closing: number;
    let sequence: Token;

    function start(code: number | null): State | undefined {
      effects.enter("academicMath");
      effects.enter("academicMathSequence");
      effects.consume(code);
      return open;
    }
    const body: State = (code) => {
      if (code === null) return nok(code);
      if (code === 92) {
        sequence = effects.enter("academicMathSequence");
        effects.consume(code);
        return afterSlash;
      }
      // Micromark needs explicit line-ending events when crossing the linked
      // text chunks of a paragraph, including list/blockquote continuations.
      const type =
        code === -5 || code === -4 || code === -3
          ? "lineEnding"
          : "academicMathData";
      effects.enter(type);
      effects.consume(code);
      effects.exit(type);
      return body;
    };
    const open: State = (code) => {
      if (code !== 40 && code !== 91) return nok(code);
      closing = code === 40 ? 41 : 93;
      effects.consume(code);
      effects.exit("academicMathSequence");
      return body;
    };
    const afterSlash: State = (code) => {
      if (code === null) return nok(code);
      if (code === -5 || code === -4 || code === -3) {
        sequence.type = "academicMathData";
        effects.exit("academicMathData");
        return body(code);
      }
      effects.consume(code);
      if (code === closing) {
        effects.exit("academicMathSequence");
        effects.exit("academicMath");
        return ok;
      }
      // Consume an escaped backslash as a pair (e.g. a matrix row break).
      sequence.type = "academicMathData";
      effects.exit("academicMathData");
      return body;
    };
    return start;
  },
};

// If an equation is incomplete, retain its delimiter instead of letting
// CommonMark remove its backslash. This also makes live editing readable.
const literal: Construct = {
  name: "academicMathLiteral",
  tokenize(effects, ok, nok) {
    return (code) => {
      effects.enter("academicMathLiteral");
      effects.consume(code);
      return (next) => {
        if (next !== 40 && next !== 41 && next !== 91 && next !== 93)
          return nok(next);
        effects.consume(next);
        effects.exit("academicMathLiteral");
        return ok;
      };
    };
  },
};

const fromMarkdown: FromMarkdownExtension = {
  enter: {
    academicMath(token: Token) {
      const source = this.sliceSerialize(token);
      this.enter(
        {
          type: "inlineMath",
          value: "",
          data: {
            hName: "code",
            hProperties: {
              className: [source[1] === "[" ? "math-display" : "math-inline"],
            },
            hChildren: [],
          },
        },
        token,
      );
      this.buffer();
    },
    academicMathLiteral(token: Token) {
      this.enter({ type: "text", value: this.sliceSerialize(token) }, token);
    },
  },
  exit: {
    academicMath(token: Token) {
      const value = this.resume();
      const node = this.stack[this.stack.length - 1];
      if (node.type === "inlineMath") {
        node.value = value;
        node.data!.hChildren = [{ type: "text", value }];
      }
      this.exit(token);
    },
    academicMathData(token: Token) {
      this.config.enter.data.call(this, token);
      this.config.exit.data.call(this, token);
    },
    academicMathLiteral(token: Token) {
      this.exit(token);
    },
  },
};

const remarkLatex: Plugin<[], Root> = function () {
  const data = this.data() as {
    micromarkExtensions?: Extension[];
    fromMarkdownExtensions?: FromMarkdownExtension[];
  };
  (data.micromarkExtensions ??= []).push({ text: { 92: [math, literal] } });
  (data.fromMarkdownExtensions ??= []).push(fromMarkdown);
};

export default remarkLatex;
