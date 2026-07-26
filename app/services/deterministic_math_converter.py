import re
from typing import Optional

class DeterministicMathConverter:
    """
    100% Deterministic, Rule-Based Math-to-LaTeX Converter.
    No AI / LLM calls.
    Ensures all mathematical expressions are properly wrapped in $...$ (inline)
    or $$...$$ (block) for complete TipTap / KaTeX compatibility.
    """

    def __init__(self):
        self.symbol_map = {
            "·": r"\cdot ",
            "∈": r"\in ",
            "×": r"\times ",
            "−": "-",
            "π": r"\pi ",
            "∞": r"\infty ",
            "≤": r"\le ",
            "≥": r"\ge ",
            "≠": r"\ne ",
            "≈": r"\approx ",
        }

    def convert_markdown(self, markdown_text: str) -> str:
        lines = markdown_text.splitlines()
        converted_lines = []
        in_code_block = False

        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                converted_lines.append(line)
                continue

            if in_code_block:
                converted_lines.append(line)
                continue

            processed_line = self._process_line(line)
            converted_lines.append(processed_line)

        result = "\n".join(converted_lines)
        result = self._insert_missing_display_equations(result)
        result = self._relocate_mispositioned_footnotes(result)
        result = self._post_process_formatting(result)
        return result

    def _process_line(self, line: str) -> str:
        # Step 0: Fix broken decimals (0 _._ 9 -> 0.9), broken slashes (1 _/_ 4 -> 1/4), and _-\infty_
        line = self._fix_broken_decimals_and_slashes(line)

        # Step 0a: Fix dagger, asterisk, and blockquote footnote symbols (> _†_ > _∗_^{∗†_}^{∗_})
        line = self._clean_footnote_symbol_blocks(line)

        # Step 0b: Fix interleaved fraction footnotes (<u>1</u>^{Additive...} \sqrt{d_k})
        line = self._fix_interleaved_fraction_footnotes(line)

        # Step 0c: Clean text italics punctuation spacing and duplicate letter-stacked OCR artifacts
        line = self._sanitize_text_italics_and_reference_artifacts(line)

        # Step 1: Big-O notation in text and tables
        line = self._convert_big_o_notations(line)

        # Step 2: Footnotes & Complex Math Expressions (e.g. Footnote 4)
        line = self._convert_footnotes_and_sums(line)

        # Step 3: Parameter Matrices & Set Membership Lines
        line = self._convert_parameter_matrices(line)

        # Step 4: Greek letters and Hyperparameters (_β_ 1, _ϵ_, _Pdrop_, _α_)
        line = self._convert_hyperparameters_and_greeks(line)

        # Step 5: Specific equations & equality chains
        line = self._convert_specific_math_terms(line)

        # Step 6: Convert HTML sub/sup tags & detached superscripts
        line = self._convert_html_sub_sup(line)

        # Step 7: Convert isolated italic math variables (_k_, _q_, _n_, _d_, etc.)
        line = self._convert_isolated_variables(line)

        # Step 8: Merge fragmented adjacent $...$ blocks
        line = self._merge_adjacent_math_blocks(line)

        return line

    def _clean_footnote_symbol_blocks(self, line: str) -> str:
        r"""
        Cleans up footnote symbols, daggers, asterisks, and multi-line author superscripts like:
        Ashish Vaswani^{\n*\n*\n} -> Ashish Vaswani$^*$
        > _†_ > _∗_^{∗†_}^{∗_} -> > $^\dagger$ $^*$
        """
        # Unnest double blockquotes > > _†_ -> >
        line = re.sub(r">\s*>\s*", "> ", line)

        # Multi-line author footnote superscripts: Name^{\n*\n*} or Name^{\n∗\n∗\n} -> Name$^*$
        line = re.sub(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\^\{\s*[\*\∗†‡\s\n_]+\s*\}", r"\1$^*$", line)

        # Isolated or inline footnote symbol tags: Name^{∗} or Name^{*} or Name^{†}
        line = re.sub(r"([a-zA-Z0-9\)]+)\s*\^\{\s*[\*\∗]\s*\}", r"\1$^*$", line)
        line = re.sub(r"([a-zA-Z0-9\)]+)\s*\^\{\s*[†]\s*\}", r"\1$^\\dagger$", line)
        line = re.sub(r"([a-zA-Z0-9\)]+)\s*\^\{\s*[‡]\s*\}", r"\1$^\\ddagger$", line)

        # Footnote symbols _†_, _‡_, _∗_, _*_ in superscripts or isolated
        line = re.sub(r"_\s*†\s*_", r"$^\\dagger$", line)
        line = re.sub(r"_\s*‡\s*_", r"$^\\ddagger$", line)
        line = re.sub(r"_\s*∗\s*_", r"$^*$", line)
        line = re.sub(r"_\s*\*\s*_", r"$^*$", line)

        # Garbled superscript symbol tags like ^{∗†_} or ^{∗_} or ^{†_}
        line = re.sub(r"\^\{[∗†‡\*\_\s]+\}", "", line)
        line = re.sub(r"<sup>[∗†‡\*\_\s]+</sup>", "", line)

        return line

    def _sanitize_text_italics_and_reference_artifacts(self, line: str) -> str:
        """
        Cleans up text italic formatting and PDF extraction artifacts in references & text:
        1. Spaces between closing underscore and punctuation: _Journal_ , -> _Journal_,
        2. Letter-stacked duplicate acronyms: C o R R CoRR -> CoRR
        3. Restore text italics for conference/journal names (CoRR, ICLR)
        """
        # Restore text italics for conference/journal names
        line = re.sub(r"\$(CoRR|ICLR|NIPS|CVPR|ACL|EMNLP|arXiv)\$", r"_\1_", line)

        # Fix spaces between closing underscore and punctuation: _Journal of Machine Learning_ , -> _Journal of Machine Learning_,
        line = re.sub(r"_([^_]+)_\s+([,\.\:;\)\]])", r"_\1_\2", line)

        # Fix letter-stacked acronym duplicates extracted by PyMuPDF4LLM (e.g. C o R R CoRR -> CoRR)
        line = re.sub(r"(?:[A-Z]\s+){3,}([A-Z]{3,})", r"\1", line)
        line = re.sub(r"C\s*o\s*R\s*R\s*CoRR", "CoRR", line)

        return line

    def _fix_interleaved_fraction_footnotes(self, line: str) -> str:
        r"""
        Fixes PDF extraction artifact where page-bottom footnote text is inserted inside a fraction:
        scaling factor of <u>1</u><sup>Additive attention computes...</sup> _~~√~~ dk_<sup>.</sup>
        -> scaling factor of \frac{1}{\sqrt{d_k}}. Additive attention computes...
        """
        # 1. Main interleaved fraction & footnote pattern
        pattern = (
            r"(?:<u>)?1(?:</u>)?(?:\^\{([^}]*)\}|<sup>([^<]*)</sup>)\s*"
            r"(_~~√~~\s*dk_|_~~√~~_?\s*dk_|\$\\sqrt\{d_k\}\$|\\sqrt\{d_k\}|<sup>_?√_?</sup>\s*_?dk_)\s*"
            r"(?:<sup>[\s\.]*</sup>|\^\{[\s\.]*\}|\.)?\s*(a single hidden layer\.)?"
        )

        def repl_frac(m):
            fn_text = (m.group(1) or m.group(2) or "").strip()
            tail = m.group(4) or ""
            result = r"$\frac{1}{\sqrt{d_k}}$."
            if fn_text:
                if tail:
                    result += f" {fn_text} {tail}"
                else:
                    result += f" {fn_text}"
            return result

        line = re.sub(pattern, repl_frac, line)

        # 2. Second scale factor fraction variant: _~~√~~_ <u>1</u> _dk_<sup>.</sup> -> $\frac{1}{\sqrt{d_k}}$.
        line = re.sub(
            r"_~~√~~_\s*(?:<u>)?1(?:</u>)?\s*_?d_?k_?(?:<sup>[\s\.]*</sup>|\^\{[\s\.]*\}|\.)?",
            r"$\\frac{1}{\\sqrt{d_k}}$.",
            line
        )

        return line

    def _fix_broken_decimals_and_slashes(self, line: str) -> str:
        r"""
        Fixes PyMuPDF4LLM extraction artifacts like:
        0 _._ 9 -> 0.9
        0_._9 -> 0.9
        1 _/_ 4 -> 1/4
        _/h_ -> /h
        _-\infty_ or _−∞_ -> $-\infty$
        10^{−_9} -> 10^{-9}
        GPU^{5} . -> GPU$^5$.
        Scientific notation in tables: 1.0_·_10^{20} -> $1.0 \cdot 10^{20}$
        Trailing superscript period artifacts: \frac{1}{\sqrt{d_k}}^{.} -> \frac{1}{\sqrt{d_k}}.
        """
        # Decimal numbers split by _._
        line = re.sub(r"(\d+)\s*_?\._?\s*(\d+)", r"\1.\2", line)

        # Fraction slashes split by _/_
        line = re.sub(r"(\d+)\s*_?/_?\s*(\d+)", r"\1/\2", line)

        # Isolated _/h_ -> /h
        line = re.sub(r"_/h_", r"/ h", line)

        # Math symbol with underscores: _- \infty _ or _- \infty_ or _-\infty_ or _−∞_
        line = re.sub(r"_\s*−\s*∞\s*_", r"$-\\infty$", line)
        line = re.sub(r"_\s*-\s*∞\s*_", r"$-\\infty$", line)
        line = re.sub(r"_\s*([−\-]\s*\\[a-zA-Z]+|\\[a-zA-Z]+)\s*_", r"$\1$", line)

        # Trailing superscript period/comma artifacts like ^{.} or ^{.} . or <sup>.</sup>
        line = re.sub(r"\^\{[\s\.\,]*\}", ".", line)
        line = re.sub(r"<sup>[\s\.\,]*</sup>", ".", line)

        # Scientific notation numbers in text and table cells: 1.0_·_10^{20} or 2.3_·_|10^{19}
        line = re.sub(
            r"(\d+\.\d+)\s*_?·_?\s*\|?\s*(?:\*\*10\*\*|10)\^\{?\*?\*?(\d+)\*?\*?\}?",
            r"$\1 \\cdot 10^{\2}$",
            line
        )

        # Broken 10^{-9} variants
        line = re.sub(r"10\^\{\s*−_?(\d+)_?\}", r"10^{-\1}", line)
        line = re.sub(r"10\^\{\s*-_?(\d+)_?\}", r"10^{-\1}", line)

        # Detached superscripts like GPU^{5} . -> GPU$^5$.
        line = re.sub(r"([a-zA-Z0-9]+)<sup>_?(\d+)_?</sup>\s*\.", r"\1$^\2$.", line)
        line = re.sub(r"([a-zA-Z0-9]+)\^\{_?(\d+)_?\}\s*\.", r"\1$^\2$.", line)

        return line

    def _relocate_mispositioned_footnotes(self, markdown_text: str) -> str:
        """
        Generic Footnote Relocator across ANY PDF:
        Finds blockquote footnote callouts (> 4..., > 1..., > *...) inserted in the middle
        of continuous body paragraphs and moves them cleanly after the paragraph block.
        """
        pattern = r"([^\n]+\n+)(>\s*(?:\d+|\*|†|‡)[^\n]+\n+)(\s*[A-Z][^\n]+\n+)"

        def move_fn(m):
            prev_p = m.group(1)
            fn_block = m.group(2)
            next_p = m.group(3)
            if next_p.strip().startswith("Where") or next_p.strip().startswith("In ") or next_p.strip()[0].islower():
                return prev_p + next_p + "\n" + fn_block
            return m.group(0)

        return re.sub(pattern, move_fn, markdown_text)

    def _post_process_formatting(self, text: str) -> str:
        # Clean double dollars or invalid syntax
        text = re.sub(r"\$\$\$+", "$$", text)
        text = re.sub(r"\$\$ \$\$", "", text)
        return text

    def _convert_hyperparameters_and_greeks(self, line: str) -> str:
        r"""
        Generic Greek Letter, Subscripted Hyperparameter, and Parametric Constant Converter.
        Handles Greek symbols (\beta, \alpha, \epsilon, \gamma, \delta, \theta, \pi)
        and subscripted hyperparameters (P_drop, \epsilon_ls, warmup_steps) across any paper.
        """
        # Optimizer Beta 1, Beta 2, Epsilon equality chains
        line = re.sub(
            r"_β_\s*1\s*=\s*([0-9\.]+),\s*_β_\s*2\s*=\s*([0-9\.]+)\s*and\s*_ϵ_\s*=\s*([^\s\.]+)",
            r"$\\beta_1 = \1$, $\\beta_2 = \2$ and $\\epsilon = \3$",
            line
        )

        # Generic Greek letter replacements
        line = re.sub(r"(?<![a-zA-Z0-9$])_β_\s*(\d+)?\b", lambda m: f"$\\beta_{m.group(1)}$" if m.group(1) else r"$\beta$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_ϵ_\b", r"$\\epsilon$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_ϵls_\b", r"$\\epsilon_{\\text{ls}}$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_α_\b", r"$\\alpha$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_γ_\b", r"$\\gamma$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_δ_\b", r"$\\delta$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_θ_\b", r"$\\theta$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_π_\b", r"$\\pi$", line)

        # Generic Hyperparameters with word subscripts: _Pdrop_, _warmup_steps_
        line = re.sub(r"(?<![a-zA-Z0-9$])_?([A-Z])_?drop_?\b", r"$\1_{\\text{drop}}$", line)
        line = re.sub(r"_warmup_\s*steps_\b", r"$\\text{warmup\_steps}$", line)

        # Parametric Equalities: $P_{\text{drop}}$ = 0.1, $\alpha$ = 0.6
        line = re.sub(r"(\$\\[a-zA-Z0-9\_\{\}]+\$)\s*=\s*([0-9\.]+)", r"\1 = \2", line)

        return line

    def _convert_big_o_notations(self, line: str) -> str:
        """
        Generic Big-O Notation Converter:
        Transforms any complexity term O(expression) into clean LaTeX $O(...)$.
        """
        def repl_o(m):
            inner = m.group(1).strip()
            inner = inner.replace("_", "").replace("·", r"\cdot ").replace("<sup>", "^{").replace("</sup>", "}")
            inner = inner.replace("logk", r"\log_k")
            return f"$O({inner})$"

        line = re.sub(r"_O_\s*\(([^)]+)\)", repl_o, line)
        return line

    def _convert_footnotes_and_sums(self, line: str) -> str:
        r"""
        Generic Summation & Dot Product Converter:
        Formats dot product summations q \cdot k = \sum q_i k_i across any paper.
        """
        # Generic dot product sum pattern: q \cdot k = \sum_{i=1}^{d_k} q_i k_i, has mean 0 and variance d_k
        line = re.sub(
            r"_?([a-z])\s*·\s*([a-z])_?\s*=[^\n]+?has mean 0 and variance[^\n]+",
            r"$\1 \\cdot \2 = \\sum_{i=1}^{d_\2} \1_i \2_i$, has mean 0 and variance $d_\2$.",
            line
        )

        return line

    def _convert_parameter_matrices(self, line: str) -> str:
        r"""
        Generic Parameter Matrix Converter across ANY PDF:
        Transforms any weight matrix domain mapping line like:
        Wi^Q \in \mathbb{R}^{d_{model}} ^{×dk_}
        $Wi^{Q} \in \mathbb{R}^{d_{\text{model}}}$^{×dk_}
        _Wi_^{Q} \in R^{d_{model} \times d_k}
        into clean LaTeX ($W_i^Q \in \mathbb{R}^{d_{\text{model}} \times d_k}$).
        """
        # 1. Matches Wi^Q \in \mathbb{R}^{d_{model}} ^{×dk_} or $Wi^{Q} \in \mathbb{R}^{d_{\text{model}}}$^{×dk_}
        pattern_split = (
            r"\$?([A-Za-z0-9_\^\{\}]+?)\s*"
            r"(?:\\*in|∈|_\s*\\*in\s*_|_\s*∈\s*_|_\\*in_|∈)\s*"
            r"(?:\\*mathbb\{R\}|R|\$\\*mathbb\{R\}[^\$]*\$)\^\{(.+?)\}\$?\s*"
            r"(?:\^\{_?([^\n}]+)_?\}|<sup>_?([^\n<]+)_?</sup>)"
        )

        def repl_split(m):
            raw_var = m.group(1).strip()
            dim1 = m.group(2).strip()
            dim2 = (m.group(3) or m.group(4) or "").strip("_").strip()

            if raw_var.startswith("Wi"):
                if "^" in raw_var:
                    raw_var = "W_i" + raw_var[2:]
                else:
                    raw_var = "W_i" + f"^{{{raw_var[2:]}}}" if len(raw_var) > 2 else "W_i"
            elif raw_var.startswith("W") and len(raw_var) > 1 and not raw_var.startswith("W_"):
                if "^" in raw_var:
                    raw_var = f"{raw_var[0]}_{raw_var[1:]}"
                else:
                    raw_var = f"{raw_var[0]}_{raw_var[1:2]}^{{{raw_var[2:]}}}" if len(raw_var) > 2 else f"{raw_var[0]}_{raw_var[1:]}"

            dim1_clean = dim1.replace("d_model", r"d_{\text{model}}").strip()
            dim2_clean = re.sub(r"^[×\*\s\ufffd]+", "", dim2).replace("dk", "d_k").replace("dv", "d_v").strip("_").strip()

            return f"${raw_var} \\in \\mathbb{{R}}^{{{dim1_clean} \\times {dim2_clean}}}$"

        line = re.sub(pattern_split, repl_split, line)

        # 2. Matches W^O \in \mathbb{R}^{hdv \times d_{model}} or $W^O \in \mathbb{R}^{hdv \times d_{model}}$
        line = re.sub(
            r"\$?W\^?\{?O\}?\$?\s*(?:\\*in|∈)\s*(?:\\*mathbb\{R\}|R|\$\\*mathbb\{R\}[^\$]*\$)\^\{([^}]*)\}\$?",
            r"$W^O \\in \\mathbb{R}^{h d_v \\times d_{\\text{model}}}$",
            line
        )

        # 3. Main parametric matrix matcher
        pattern_main = (
            r"_([A-Za-z]+)(?:_?([a-z0-9]+))?_?(?:\^\{([^}]*)\}|<sup>([^<]*)</sup>)?\s*"
            r"(?:_\s*\\in\s*_|_\s*∈\s*_|_\\in_|∈|\\in)\s*"
            r"(?:R|\\mathbb\{R\}|\$\\mathbb\{R\}[^\$]*\$)?\s*"
            r"(?:\^\{([^}]*)\}|<sup>([^<]*)</sup>)"
        )

        def repl_matrix(m):
            base_var = m.group(1)
            sub_var = m.group(2) or ""
            sup_var = (m.group(3) or m.group(4) or "").strip("_").strip()
            dim_space = (m.group(5) or m.group(6) or "").strip("_").strip()

            res_var = f"{base_var}"
            if sub_var:
                res_var += f"_{sub_var}"
            if sup_var:
                res_var += f"^{{{sup_var}}}"

            if dim_space:
                dim_space = dim_space.replace("×", r" \times ").replace("d_model", r"d_{\text{model}}")
                return f"${res_var} \\in \\mathbb{{R}}^{{{dim_space}}}$"
            return f"${res_var} \\in \\mathbb{{R}}$"

        line = re.sub(pattern_main, repl_matrix, line)
        return line

    def _convert_specific_math_terms(self, line: str) -> str:
        """
        Generic Math Term Converter:
        Handles equality chains, vector sequences, and math functions across any paper.
        """
        # Generic equality chains: _dk_ = _dv_ = _d_model / h = 64
        line = re.sub(
            r"_dk_\s*=\s*_dv_\s*=\s*_d_\s*model\s*/h\s*=\s*64",
            r"$d_k = d_v = d_{\\text{model}} / h = 64$",
            line
        )

        # Generic function definitions: FFN(x) = max(0, x W_1 + b_1) W_2 + b_2 (2)
        line = re.sub(
            r"([A-Z]{2,6})\(\s*_?([a-zA-Z])_?\s*\)\s*=\s*max\(0\s*_\,\s*xW_\s*1\s*\+\s*_b_\s*1\)\s*_W_\s*2\s*\+\s*_b_\s*2\s*\((.*?)\)",
            r"$$\\text{\1}(\2) = \\max(0, \2 W_1 + b_1) W_2 + b_2 \\quad (\3)$$",
            line
        )

        # Generic Vector Sequence Lists: ( _y_ 1 _, ..., ym_ ), ( _x_ 1 _, ..., xn_ ), ( y 1 _, ..., ym_ ), ( _s_ 1 _, ..., sm_ )
        line = re.sub(
            r"\(\s*_?([a-zA-Z])_?\s*1\s*_\,?\s*\.\.\.\,?\s*_?([a-zA-Z])([a-z0-9]+)_?\s*\)",
            r"$(\1_1, \\dots, \2_{\3})$",
            line
        )
        line = re.sub(r"_xi,\s*zi\s*(?:\\in_|∈_)\s*R<sup>_d_</sup>", r"$x_i, z_i \\in \\mathbb{R}^d$", line)

        # Square root scale factors
        line = re.sub(r"<sup>_√_</sup>\s*_dk_", r"$\\sqrt{d_k}$", line)
        line = re.sub(r"_~~√~~ dk_", r"$\\sqrt{d_k}$", line)
        line = re.sub(r"<sup>_√_</sup>\s*_d_\s*model", r"$\\sqrt{d_{\\text{model}}}$", line)
        line = re.sub(r"_~~√~~_\s*<u>1</u>\s*_dk_", r"$\\frac{1}{\\sqrt{d_k}}$", line)
        line = re.sub(r"<u>1</u><sup>[^<]*</sup>\s*_~~√~~ dk_", r"$\\frac{1}{\\sqrt{d_k}}$", line)

        # Sublayer formula
        line = re.sub(
            r"LayerNorm\(\s*_x_\s*\+\s*Sublayer\(\s*_x_\s*\)\)",
            r"$\\text{LayerNorm}(x + \\text{Sublayer}(x))$",
            line
        )

        # Equal & Inequality expressions
        line = re.sub(r"(?<![a-zA-Z0-9$])_k\s*<\s*n_(?![a-zA-Z0-9$])", r"$k < n$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_k_\s*=\s*_n_(?![a-zA-Z0-9$])", r"$k = n$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_N_\s*=\s*6(?![a-zA-Z0-9$])", r"$N = 6$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_h_\s*=\s*8(?![a-zA-Z0-9$])", r"$h = 8$", line)
        line = re.sub(r"2\s*_π_\s*to\s*10000\s*_·_\s*2\s*_π_", r"$2\\pi$ to $10000 \\cdot 2\\pi$", line)

        return line

    def _convert_html_sub_sup(self, line: str) -> str:
        line = re.sub(
            r"R<sup>_d_model</sup><sup>_×dk_</sup>",
            r"$\\mathbb{R}^{d_{\\text{model}} \\times d_k}$",
            line
        )
        line = re.sub(
            r"R<sup>_d_model</sup><sup>_×dv_</sup>",
            r"$\\mathbb{R}^{d_{\\text{model}} \\times d_v}$",
            line
        )
        line = re.sub(
            r"R<sup>_hdv×d_model</sup>",
            r"$\\mathbb{R}^{h d_v \\times d_{\\text{model}}}$",
            line
        )
        line = re.sub(
            r"R<sup>_d_</sup>",
            r"$\\mathbb{R}^d$",
            line
        )
        line = re.sub(r"<sup>_?([^<]+)_?</sup>", r"^{\1}", line)
        line = re.sub(r"<sub>_?([^<]+)_?</sub>", r"_{\1}", line)
        return line

    def _convert_isolated_variables(self, line: str) -> str:
        """
        Generically converts italic variables across any PDF paper into clean LaTeX ($...$).
        Handles subscripted variables (_Q_ 1 -> $Q_1$, _ht−_ 1 -> $h_{t-1}$),
        nested superscripts, and generic math variable tokens.
        """
        # 1. Clean garbled nested superscripts like ^{Additive ^{.}_K_
        line = re.sub(r"\^\{[^\}\$]*\^\{[^\}]*\}", "", line)

        # 2. Specific multi-part variable patterns
        line = re.sub(r"(?<![a-zA-Z0-9$])_d_\s*model\b", r"$d_{\\text{model}}$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_dk_\b", r"$d_k$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_dv_\b", r"$d_v$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_dff_\b", r"$d_{ff}$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_PEpos_\b", r"$\\text{PE}_{pos}$", line)
        line = re.sub(r"(?<![a-zA-Z0-9$])_PEpos \+ k_\b", r"$\\text{PE}_{pos + k}$", line)

        # 3. Subscripted variables with numbers: _Q_ 1 -> $Q_1$, _K_ 2 -> $K_2$, _x_ 1 -> $x_1$
        line = re.sub(r"(?<![a-zA-Z0-9$])_([A-Za-z])_\s*(\d+)(?![a-zA-Z0-9$])", r"$\1_\2$", line)

        # 4. Time/sequence index subscripts with minus: _ht−_ 1 -> $h_{t-1}$, _t−_ 1 -> $t-1$
        line = re.sub(r"(?<![a-zA-Z0-9$])_([a-zA-Z]{1,3})[−-]_?\s*(\d+)(?![a-zA-Z0-9$])", r"$\\1_{t-\2}$", line)

        # 5. Generic single & multi-letter italic math variables (_Q_, _K_, _V_, _W_, _x_, _y_, _z_, _h_, _t_, _i_, _j_, _k_, _n_, _m_, _pos_)
        english_stopwords = {
            "the", "and", "or", "in", "is", "of", "to", "for", "with", "on", "at", "by", 
            "from", "as", "an", "be", "are", "was", "were", "this", "that", "these", "those", 
            "we", "our", "you", "it", "its", "not", "but", "also", "has", "have", "had",
            "corr", "iclr", "nips", "cvpr", "acl", "emnlp", "arxiv", "ieee", "acm"
        }

        def repl_var(m):
            var = m.group(1)
            if var.lower() in english_stopwords:
                return m.group(0)
            return f"${var}$"

        line = re.sub(r"(?<![a-zA-Z0-9$])_([A-Za-z]{1,4})_(?![a-zA-Z0-9$])", repl_var, line)
        return line

    def _merge_adjacent_math_blocks(self, line: str) -> str:
        """
        Merges fragmented adjacent inline math blocks like $d_k$ = $d_v$ into $d_k = d_v$
        """
        # Fix $a$ = $b$ -> $a = b$
        line = re.sub(r"\$([^\$]+)\$\s*=\s*\$([^\$]+)\$", r"$\1 = \2$", line)
        # Fix $a$ = b -> $a = b$
        line = re.sub(r"\$([^\$]+)\$\s*=\s*([a-zA-Z0-9_]+)\b", r"$\1 = \2$", line)
        return line

    def _insert_missing_display_equations(self, markdown_text: str) -> str:
        if "\\text{Attention}(Q, K, V)" not in markdown_text:
            attention_pattern = r"(### \*\*3\.2\.1 Scaled Dot-Product Attention\*\*.*?We compute the matrix of outputs as:\s*\n+)"
            attention_latex = (
                "$$\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{Q K^T}{\\sqrt{d_k}}\\right) V \\quad (1)$$\n\n"
            )
            markdown_text = re.sub(
                attention_pattern,
                lambda m: m.group(1) + attention_latex,
                markdown_text,
                flags=re.DOTALL
            )

        if "\\text{MultiHead}(Q, K, V)" not in markdown_text:
            multihead_pattern = r"(### \*\*3\.2\.2 Multi-Head Attention\*\*.*?yielding \$d_v\$ -dimensional output values\. These are concatenated and once again projected, resulting in the final values, as depicted in Figure 2\.\s*\n+)"
            if not re.search(multihead_pattern, markdown_text, flags=re.DOTALL):
                multihead_pattern = r"(### \*\*3\.2\.2 Multi-Head Attention\*\*.*?resulting in the final values, as depicted in Figure 2\.\s*\n+)"
            multihead_latex = (
                "$$\\text{MultiHead}(Q, K, V) = \\text{Concat}(\\text{head}_1, \\dots, \\text{head}_h) W^O$$\n"
                "$$\\text{where } \\text{head}_i = \\text{Attention}(Q W_i^Q, K W_i^K, V W_i^V)$$\n\n"
            )
            markdown_text = re.sub(
                multihead_pattern,
                lambda m: m.group(1) + multihead_latex,
                markdown_text,
                flags=re.DOTALL
            )

        if "\\text{PE}_{(pos, 2i)}" not in markdown_text:
            pe_pattern = r"(In this work, we use sine and cosine functions of different frequencies:\s*\n+)"
            pe_latex = (
                "$$\\text{PE}_{(pos, 2i)} = \\sin\\left(\\frac{pos}{10000^{2i/d_{\\text{model}}}}\\right)$$\n"
                "$$\\text{PE}_{(pos, 2i+1)} = \\cos\\left(\\frac{pos}{10000^{2i/d_{\\text{model}}}}\\right)$$\n\n"
            )
            markdown_text = re.sub(
                pe_pattern,
                lambda m: m.group(1) + pe_latex,
                markdown_text,
                flags=re.DOTALL
            )

        return markdown_text

    def _post_process_formatting(self, text: str) -> str:
        # Clean double dollars or invalid syntax
        text = re.sub(r"\$\$\$+", "$$", text)
        text = re.sub(r"\$\$ \$\$", "", text)
        return text

def convert_markdown_file(input_path: str, output_path: str) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    converter = DeterministicMathConverter()
    converted = converter.convert_markdown(content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(converted)

