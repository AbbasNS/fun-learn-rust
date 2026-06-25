🦀 Tip of the day 40: Modules, How Rust Splits a Program Into Pieces

Tip [10](10-impl.md) introduced inline modules: `mod foo { ... }` to group related code in the same file. That works for small examples but not for projects with thousands of lines. The same `mod` keyword has a second form that pulls code in from another file.

Two ways to declare a module:

```rust
mod inline {
    pub fn hello() {}
}

mod external;   // looks for external.rs (or external/mod.rs) in the same directory
```

When you write `mod external;` with a semicolon instead of a body, the compiler loads the contents of `external.rs` (or `external/mod.rs`) and treats them as if they had been written inline. The two forms are equivalent in every other way.

The flip side: a `.rs` file that has no `mod` declaration points at is not part of your crate at all. The compiler never reads it. An orphaned file compiles to nothing and produces no error, which surprises people who expect every file in `src/` to matter.

So is every file a module? Effectively yes: a file becomes a module the instant some `mod` points at it, and the root file is the crate's top module. But the mapping runs one way only. A single module's items come from exactly one place, its inline `{ }` block or its one file; you cannot split one module across two files. A module can *contain* submodules that live in their own files, but it is never itself spread across them. (Go differs: one package spans many files. So do C# namespaces.)

The module tree starts at one root, one tree per *crate*. A crate is the library or binary the compiler builds as a single unit; the Cargo tip covers crates in full. That root is `src/lib.rs` for a library, `src/main.rs` for a binary. Every module is reached by descending from there. A typical layout for a small library:

```
src/
├── lib.rs          // module root
├── parser.rs       // mod parser; in lib.rs
├── runtime.rs      // mod runtime; in lib.rs
└── runtime/
    ├── value.rs    // mod value; in runtime.rs
    └── env.rs      // mod env;   in runtime.rs
```

Inside `lib.rs`, you write `mod parser;` and `mod runtime;`. Inside `runtime.rs`, you write `mod value;` and `mod env;`. The compiler walks the tree.

That `runtime.rs`-next-to-`runtime/` layout is the modern style. Before the 2018 edition, a module with submodules had to live in `runtime/mod.rs`, so a large project accumulated dozens of files all named `mod.rs`, indistinguishable in your editor's tabs. The 2018 edition let `runtime.rs` sit beside a `runtime/` directory instead. Both styles still compile, so you will meet `mod.rs` in older codebases.

Now visibility. Items declared inside a module are private by default. To expose one, put `pub` on it:

```rust
pub mod parser {   // a module is private by default; `pub` exposes its path
    pub fn parse(text: &str) -> Ast { /* ... */ }   // visible outside this module
    fn helper() { /* ... */ }                       // private to this module
    pub struct Ast { /* ... */ }                    // type is visible
    // but Ast's fields are still private unless individually marked pub
}
```

`pub` has finer-grained variants: `pub(crate)` exposes only within the current crate, `pub(super)` only to the parent module, `pub(in path)` to a specific subtree. Default is private. There is no `private` keyword; the absence of `pub` is private.

A related guard: a public signature cannot quietly hand out a more private type. If a `pub fn` returns a private (or `pub(crate)`) type, the compiler warns `type X is more private than the item`, since callers who can reach the function cannot name what it returns. Make the type at least as visible as the signature that exposes it, or make the signature no more visible than the type.

To use an item from another module, name its full path or import it with `use`:

```rust
use crate::parser::parse;
use crate::runtime::env::Env;

fn main() {
    let ast = parse("input");
    let env = Env::new();
}
```

Path roots:

- `crate::` starts at the current crate's module root.
- `super::` goes up one level (the parent module).
- `self::` is the current module. As a prefix it is almost always optional, since a bare name already resolves in the current module first; it only adds explicitness. The keyword earns its keep in the group form `use std::fmt::{self, Display}`, which imports the module `fmt` itself alongside `Display`.
- A bare name like `std` or a dependency name starts at that crate's root.

Do names have to be unique? Only within a single module, and only within the same namespace (Rust keeps types, values, and macros in separate ones, so a `mod thing` and a `fn thing` can sit side by side). The same name in two different modules is always fine, fully distinguished by its path: `parser::Node` and `runtime::Node` never collide, which is the entire point of a tree of scopes. That applies to module names themselves too: most files carry their own `mod tests`, and a crate's dozens of `tests` modules coexist happily because each sits under a different parent. The error you will actually hit is declaring two items of the same kind with the same name in one module: `the name X is defined multiple times`. Across crates there is no conflict either, since every path is rooted at a crate name, so `serde::Error` and `std::io::Error` coexist. Cargo can even link two different versions of the same crate, keeping each one distinct.

A useful pattern is *re-exporting* with `pub use`. It lets the inside of your crate be organized one way while presenting a different API to users:

```rust
// in lib.rs
mod internal {                  // the module itself stays private
    pub struct Thing;           // but Thing is pub within it
}

pub use internal::Thing;
// users write `mycrate::Thing`, not `mycrate::internal::Thing`
```

Notice what is and isn't required. The `internal` module can stay private; `pub use` lifts one chosen item out without exposing its neighbors. But the item itself must already be `pub`. `pub use` changes where a name lives, not how visible it is, so re-exporting a private or `pub(crate)` item *as* `pub` is a compile error. You cannot launder something into the public API just by re-exporting it.

This is how big standard library types can sit at convenient names while their definitions live deeper in the tree.

Why a tree at all? Modules are about names and visibility, nothing more, so the required file layout can look like busywork. It is not a separate rule. A file named after a module is just the default place the compiler looks for that module's body, and you could nest the entire tree inline in one file instead, the way the `mod inline { ... }` example above does. The layout is a convention that keeps large projects navigable, not something the compiler requires.

What the compiler does require is a *crate*. Modules are not compilation units; the crate is. The compiler reads a crate's whole module tree and compiles it as a single piece, then a linker joins each crate's output into the final binary. Compilation does not run module by module, so adding more modules does not change what gets built or make it faster on its own. The parallelism lives at two other levels: Cargo builds independent crates in parallel from the dependency graph, and within one crate the backend splits work into *codegen units* that LLVM compiles at the same time. What `cargo build` does end to end, including the linker, and how profiles tune codegen units, each get a tip of their own later.

Comparison:

- Java: package equals directory, and the file path mirrors the package path. Visibility uses `public`, `private`, `protected`, plus package-private (default).
- Python: a directory with `__init__.py` (or any `.py` file) is a module. Imports with `import` and `from`. No public/private at the language level; convention uses leading underscores.
- C++: `namespace` only groups and names; `public`/`private`/`protected` encapsulate class members; and file-level "public" rides on the header/source split, which exists for separate compilation, with `static`/anonymous namespaces tying visibility to linkage. So C++ braids visibility and the build model together. C++20 `module`s tidy this with explicit `export`, but a module is still both a compilation unit and a visibility boundary.
- Go: package equals directory (one package per directory). Names starting with uppercase are exported, lowercase are private.
- JavaScript / TypeScript: ES modules with `import`/`export`. Each file is a module; exports are explicit.
- Rust: modules form a tree rooted at `lib.rs` or `main.rs`, declared with `mod`, private by default, exposure graded with `pub`. Visibility lives entirely in that tree; how the code compiles is the crate's concern, a separate axis.

The takeaway: Rust modules are a tree of named scopes rooted at one file. `mod name;` pulls in a file, `pub` exposes an item, `use` brings a name into scope, and `pub use` re-exports it as part of your public API.

🔇 The file is right there. The compiler can see the file. It just wants to hear you say `mod`.
