# from __future__ import annotations
from dataclasses import dataclass, fields
from bs4 import BeautifulSoup
# from bs4.filter import SoupStrainer
from bs4.element import Tag, ResultSet
from typing import ClassVar, Any, Generator, Mapping
# from enum import StrEnum
import re
import json
# from importlib.abc import Traversable
from pkg.src.scraper_config_handler import TargetConfig
import esprima
from esprima.visitor import Visitor
from pkg.src.serp_scraper import SerpResult

"""
This module implements a strategy for the Strategy protocol
defined in pkg.src.strategy_protocol

In pkg.src.serp_scraper, there are two ways we can handle the
problem of URL injection via js scripts: statically, by scraping
the page's scripts and extracting the data we need, or dynamically,
by rendering the html in a headless browser and skipping the need
for script surgery. The Strategy protocol accomodates both options
and leaves the choice to the caller.

Here, we implement the static approach.

prepare() leaves the html unaltered and unrendered. It
initializes a BeautifulSoup object and returns it with no
modifications. It also returns a mapping of image ID values
to URLs, which is created by scraping, filtering, and parsing
the <script/ tags in the soup.

finalize() takes the SerpResult object produced by the
call to SerpScraper.scrape() and edits the list of SerpItems
via the map.
"""

_RE_FN_PATTERN = re.compile(
    r"_setImagesSrc\s*"
    r"\(\s*(\b(?:ii|r|s)\b)\s*,\s*"
    r"(?!\1)(\b(?:ii|r|s)\b)\s*,\s*"
    r"(?!\1|\2)(\b(?:ii|r|s)\b)\s*\)"
)

class StaticStrategy:

    def __init__(self):
        self.edits_map: dict[str, str]|None = None

    def prepare(self, html: bytes) -> BeautifulSoup:
        # set self.edits_map before returning soup!
        soup = BeautifulSoup(html, "html.parser")
        self.edits_map = self._build_edits_map(soup)
        return soup

    def finalize(self, sr: SerpResult) -> SerpResult:
        assert self.edits_map is not None
        for item in sr.items:
            item.image = self.edits_map.get(item.img_id, item.image)
        return sr

    def _inject_valid_urls(self, partial: SerpResult, mapping: dict[str, str]) -> None:
        for tile in partial.items:
            tile.image = mapping[tile.img_id]

    def _quickcheck(self, text) -> bool:
        return bool(_RE_FN_PATTERN.search(text))

    def _build_edits_map(self, soup: BeautifulSoup) -> dict[str, str]:
        all_scripts = [s.get_text() for s in soup.find_all("script") if self._quickcheck(s.get_text())]
        _emap = {}
        for script in all_scripts:
            _emap.update(self._extract_script_vars(str(script)))
        return _emap

    def _extract_script_vars(self, text: str) -> dict[str, str]:
        ast = esprima.parseScript(text)
        v = SrcInjectorVisitor()
        v.visit(ast)  # kicks off recursion
        return {i: v.s_val for i in v.ids if v.s_val}


class SrcInjectorVisitor(Visitor):
    def __init__(self):
        self.s_val: str | None = None
        self.ids: list[str] = []

    def visit_VariableDeclarator(self, node):
        # Handle declarator: e.g., "var s = '...';" or "var ii = ['a','b'];"
        name = getattr(getattr(node, "id", None), "name", None)
        init  = getattr(node, "init", None)
        tinit = getattr(init, "type", None)

        if name == "s" and tinit == "Literal" and isinstance(init.value, str):
            self.s_val = init.value

        elif name == "ii" and tinit == "ArrayExpression":
            for el in getattr(init, "elements", []) or []:
                if getattr(el, "type", None) == "Literal" and isinstance(el.value, str):
                    self.ids.append(el.value)

        # Important: continue traversal into children (id/init) if needed
        self.generic_visit(node)

"""
Very good. Let us take the visitor apart slowly, then walk it against your concrete string, so that every moving part is seen, named, and understood.

# The shape of the problem

Your script is a tiny, self-invoking function. Inside it, three variables are declared. First, `s`, whose value is a long data-URI string. Second, `ii`, whose value is an array with one string element, the image id. Third, `r`, which is irrelevant. Finally, a call is made to `_setImagesSrc(ii, s, r)`. We want to read two things only. The value of `s`. Every string literal inside the `ii` array. Nothing else matters for our mapping.

# What Esprima gives you

When you call `esprima.parseScript(js_text)`, you receive an **ESTree**-shaped AST. The root is a `Program`. Its `body` holds one `ExpressionStatement`. That statement’s `expression` is a `CallExpression`. The callee of that call is a `FunctionExpression` which contains a `BlockStatement`. Inside that block’s `body` live the important nodes for us. Three `VariableDeclaration` nodes, each holding one or more `VariableDeclarator` children, then another `ExpressionStatement` for the `_setImagesSrc` call.

So the declarations you care about are always found as **descendants** under that `BlockStatement`. In practice, you can find them reliably by visiting all `VariableDeclarator` nodes anywhere in the tree. That is exactly what the visitor does.

# How the visitor pattern recurses

Esprima’s Python port ships a small base class, `esprima.visitor.Visitor`. It exposes two key methods. `visit`, which dispatches on node type to a method named `visit_<Type>`. And `generic_visit`, which walks a node’s **children** and calls `visit` on each. This gives you a simple rule. Implement `visit_VariableDeclarator` for the one node kind you care about. Do your extraction there. Then call `self.generic_visit(node)` to recurse further, in case the initializer has nested structure to explore.

That single line **is** the recursion. You do not write the loop. The base class does.

# The class, line by line

```python
class SrcInjectorVisitor(visitor.Visitor):
    def __init__(self):
        self.s_val: str | None = None
        self.ids: list[str] = []
```

Creation. We hold two accumulators. `s_val` will store the single data-URI string we see in a script. `ids` will store every string literal found inside the `ii` array. Both begin empty. We keep them as simple Python types so that downstream code is trivial.

```python
    def visit_VariableDeclarator(self, node):
        name = getattr(getattr(node, "id", None), "name", None)
        init  = getattr(node, "init", None)
        tinit = getattr(init, "type", None)
```

Dispatch. The framework has reached a `VariableDeclarator`. In ESTree, a declarator has two important children. `id`, an Identifier node with a `name` such as `"s"` or `"ii"`. And `init`, which is the initializer expression. We read both defensively. We never assume fields exist. Minified code is regular, yet our visitor should remain calm under oddities.

```python
        if name == "s" and tinit == "Literal" and isinstance(init.value, str):
            self.s_val = init.value
```

First branch. We have a declaration of the form `var s = <something>`. We accept it only if the initializer is a `Literal` and that literal’s value is a Python string. For your example, the test passes. We store the data-URI string in `s_val`. We do not attempt to decode it. We do not validate that it begins with `data:image/`. You may add such checks later if you wish.

```python
        elif name == "ii" and tinit == "ArrayExpression":
            for el in getattr(init, "elements", []) or []:
                if getattr(el, "type", None) == "Literal" and isinstance(el.value, str):
                    self.ids.append(el.value)
```

Second branch. We have a declaration of the form `var ii = <something>`. We accept it only if the initializer is an `ArrayExpression`. We then iterate its `elements`. Each element is a node. In your page, every element is a `Literal` with a string value. We gather each string into `ids`. We do not short-circuit after one. In some pages `ii` contains many ids, and we want them all.

```python
        self.generic_visit(node)
```

Recursion. We hand control back to the base class to walk children such as `id` and `init`. This ensures that if a future minifier nests expression forms under `init` which themselves contain declarators, we will still traverse them. If you prefer strict minimalism, you may omit this line. For today’s shape, omitting it changes nothing because we have already read all useful information from this node. Keeping it makes the visitor robust.

# The driver

```python
def extract_mapping(js_text: str) -> dict[str, str]:
    ast = esprima.parseScript(js_text)
    v = SrcInjectorVisitor()
    v.visit(ast)
    return {i: v.s_val for i in v.ids if v.s_val}
```

Three steps. Parse once into an AST. Create the visitor. Visit the root. The visitor will walk the entire tree, fill `s_val` and `ids`, and return. We then construct a mapping from each id to the single `s_val`. This mirrors what the page’s `_setImagesSrc(ii, s, r)` does. One image payload used for many ids. If `s_val` is missing, we return an empty mapping to avoid writing `None` into your map.

# A step-by-step trace on your string

We feed your example into `extract_mapping`.

1. `parseScript` returns a `Program`.
2. `visit(Program)` has no specific handler. The base class calls `generic_visit` on it. It visits each child in `Program.body`.
3. It reaches the `ExpressionStatement` that wraps the IIFE. Again, no handler. It descends into its `expression`, a `CallExpression`.
4. The callee of that call is a `FunctionExpression`. Still no handler. The visitor descends into its `body`, a `BlockStatement`.
5. The block’s `body` is a list of four items. The first is a `VariableDeclaration` with one `VariableDeclarator` for `s`.
6. Now the framework calls `visit_VariableDeclarator` on that child. Your method runs.

   * `name` becomes `"s"`.
   * `init.type` becomes `"Literal"`.
   * The first branch matches. `self.s_val` is set to the long data-URI string.
   * You then call `generic_visit`. The base class looks at `id` and `init`. They have no declarators beneath them. It returns.
7. The second item in the block is a `VariableDeclaration` with a `VariableDeclarator` for `ii`. Your method runs again.

   * `name` becomes `"ii"`.
   * `init.type` becomes `"ArrayExpression"`.
   * The second branch matches. You iterate `init.elements`. There is one `Literal` with the value `"tsuid_L_FkZ4qlAtyDwbkP49Pj0QU_77"`. You append that to `self.ids`.
   * You call `generic_visit`. The base class visits children again. Nothing further to do.
8. The third declaration for `r` arrives. Your method sees `name == "r"`. Neither branch matches. You still call `generic_visit`. Nothing useful happens.
9. The final `ExpressionStatement` contains the call to `_setImagesSrc`. You did not define a handler. The base class descends and returns.
10. The traversal completes. Control returns to `extract_mapping`. You produce a dict with one entry. The key is the id. The value is the data-URI.

Nothing else is touched. No other nodes are examined with custom logic. This is why the approach remains small and clear.

# Why each guard exists

* We check `node.id.name` rather than the callee text. We care that we are in a declarator for specific names.
* We check `init.type`. We reject anything that is not a `Literal` for `s` and not an `ArrayExpression` for `ii`. This protects you from odd pages and gives you a stable mental model.
* We check `isinstance(init.value, str)` and the same for each array element. Esprima converts JS string literals into Python strings. Being explicit saves you from awkward surprises if a non-string literal appears.
* We keep `generic_visit`. It is a safety belt. If later you encounter `var ii = makeIds('a','b')`, you will need a different tactic entirely, yet the recursive call keeps your visitor complete for the shapes it already understands.

# Common extensions you will eventually want

* **Multiple declarators in one declaration.** Minifiers sometimes compact `var s='…', ii=['…'], r=''`. Your handler already handles this because you implemented `visit_VariableDeclarator`, not `visit_VariableDeclaration`. The framework calls your method for each declarator separately. No change required.
* **Identifiers as initialisers.** If you meet `var ii = I; var I = ['a']`, your current code will not resolve `I`. The next step is a tiny environment. Maintain a dict of `name → Python value` whenever you see a literal or an array literal. When you visit the `_setImagesSrc` call, evaluate its arguments by looking up identifiers in the environment. That remains small and hermetic.
* **Robust script filtering.** Keep your light “does this script mention `_setImagesSrc`” test to avoid unnecessary traversal. Prefer a regex that matches the callee name with optional whitespace. This prevents false negatives from formatting changes.
* **Graceful merging.** When you visit many scripts, build a map per script and then merge them. Let later entries overwrite earlier ones. This mirrors browser behaviour, where the last executed assignment wins.

# Measure twice, cut once

The correctness of this approach rests on one observation. In the static page you are handling, `s` is a literal string and `ii` is an array literal of strings. That is the whole trick. Your visitor is narrow because the page is regular. If that assumption ever fails, move up one notch to the tiny evaluator I mentioned. Until then, keep this visitor small, readable, and well-tested on real samples.

If you wish, we can build a miniature test where we print the `type` chain as the visitor walks your exact string. Seeing “Program, ExpressionStatement, CallExpression, FunctionExpression, BlockStatement, VariableDeclaration, VariableDeclarator…” once in the console often cements the mental model.

"""