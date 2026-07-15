🦀 Tip of the day 48 follow-up

Follow-up questions from the discussion on [Tip 48: Build Scripts, When Cargo.toml Cannot Do Enough](48-build-scripts.md).

## Is there an accepted way to mix C&C++ builds with Rust? Does `build.rs` run CMake, does CMake run Cargo, or does some third tool run both?

It isn't a mess once you ask one question: which build system produces the final artifact you ship? Whoever owns the final linked output is "on top," and the other one is invoked as a component builder. All three of those options are real. They just correspond to three different answers to that question.

### Case A: Cargo on top (your `build.rs` drives the C&C++ build)

You run `cargo build` and it produces the final binary; the C&C++ is a dependency. This is the common case, and it is what the `-sys` crates in the tip are doing. Two idiomatic, official (`rust-lang` org) build-dependencies:

- [`cc`](https://docs.rs/cc/latest/cc/) for a handful of C&C++ (or assembly) files you own. You list the files, it compiles them into a static archive and emits the link directives for you.

```rust
// build.rs
fn main() {
    cc::Build::new().file("src/foo.c").compile("foo"); // linking handled automatically
}
```

- [`cmake`](https://docs.rs/cmake/latest/cmake/) when the dependency already ships a `CMakeLists.txt`. Your `build.rs` shells out to the system `cmake`, gets back an install path, and you emit the link directives yourself.

```rust
// build.rs
let dst = cmake::Config::new("libfoo").build();
println!("cargo::rustc-link-search=native={}", dst.display());
println!("cargo::rustc-link-lib=static=foo");
```

So "have `build.rs` run CMake" is not a hack, it is the sanctioned path. Rule of thumb: `cc` for source files you control, `cmake` for an upstream project that already has a CMake build.

### Case B: CMake on top (CMake pulls in Cargo)

Here the project is fundamentally a C&C++ CMake project and Rust is one library inside it. You do not want `build.rs` calling `cmake`, that is backwards. You want the tool built for this direction: [Corrosion](https://github.com/corrosion-rs/corrosion) (formerly `cmake-cargo`, actively maintained). Its documented [`corrosion_import_crate`](https://corrosion-rs.github.io/corrosion/usage.html) runs `cargo metadata`, turns each crate into a CMake target, and lets your C++ targets link them normally.

```cmake
corrosion_import_crate(MANIFEST_PATH rust/Cargo.toml)
target_link_libraries(my_cpp_app PRIVATE my_rust_crate)
```

The Rust crate declares `crate-type = ["staticlib"]` or `["cdylib"]`. CMake's own native `enable_language(Rust)` is still just a [draft merge request](https://gitlab.kitware.com/cmake/cmake/-/merge_requests/11109) as of late 2025, so do not reach for that yet; Corrosion is the practical answer.

### Case C: A third tool orchestrates both

In large polyglot monorepos, neither Cargo nor CMake is on top. A meta build system owns everything and calls `rustc` directly, using Cargo only as a source of dependency metadata that gets translated ahead of time:

- [Bazel](https://bazel.build/) with [`rules_rust`](https://github.com/bazelbuild/rules_rust). Its [`crate_universe`](https://bazelbuild.github.io/rules_rust/crate_universe_bzlmod.html) feature reads your `Cargo.toml` and generates Bazel targets. Popular, used at scale, with first-class C&C++ interop via `rules_cc`.
- [Buck2](https://buck2.build/) (Meta) with its [Rust rules](https://buck2.build/docs/prelude/rules/rust/rust_library/). A separate tool, [Reindeer](https://github.com/facebookincubator/reindeer), buckifies your Cargo graph ahead of time. Its manual is blunt about it: "At build time, Cargo is not involved at all."
- [Meson](https://mesonbuild.com/Rust.html). Has native Rust support, calls `rustc` directly, and since 1.9 can even mix Rust and C sources in a single target.

The common thread in Case C: Cargo stops being the orchestrator and becomes a dependency-manifest reader.

### One clarification worth making

None of the above is the same thing as language interop. Orchestration (who builds and links what) is separate from the FFI boundary (how C++ and Rust actually call each other). For the boundary you use [`bindgen`](https://github.com/rust-lang/rust-bindgen) (C headers to Rust), [`cbindgen`](https://github.com/mozilla/cbindgen) (Rust to C headers), or [`cxx`](https://cxx.rs/) (safe C++ to Rust bridge). Real projects commonly pair one orchestrator (say Corrosion) with one interop tool (say `cxx`). They are complementary, not competing.

So it is not a mess. Orchestration comes down to one question, who produces the final artifact; wiring the two languages together is a separate concern, handled by the interop tools above.

## Can a `build.rs` require external libraries, indicated in a "sub-`build.rs`"?

Two halves, and the short answer is "yes, but not through a nested script."

Can a `build.rs` require external libraries? Yes. A build script is compiled as its own small program and has its own dependency list, declared under [`[build-dependencies]`](https://doc.rust-lang.org/cargo/reference/build-scripts.html#build-dependencies) in `Cargo.toml`. That is exactly how it pulls in `cc`, `cmake`, `bindgen`, and so on. These are walled off from your normal `[dependencies]`; the build script cannot even see those, since they are not built yet when it runs.

```toml
[build-dependencies]
cc = "1"
cmake = "0.1"
```

Is there a "sub-`build.rs`"? No, not as a literal feature. A package has exactly one build script. The [`build` key](https://doc.rust-lang.org/cargo/reference/manifest.html#the-build-field) in `[package]` takes a single file path (or `false` to disable it), never a list. You cannot nest build scripts inside one package.

But the inception is real. It just lives in the dependency graph, not inside a single crate. A crate you list in `[build-dependencies]` is an ordinary crate, so it can have its own `build.rs`, and its own `[build-dependencies]`, which can have theirs, all the way down. Cargo compiles and runs each one in topological order: a dependency's build script finishes before the dependent that needs it. So you do get build scripts triggering build scripts, through the graph rather than through nesting.

There is even a sanctioned channel for one build script to hand data to another, which is the principled version of a "sub-`build.rs`" telling its parent what it needs. A crate with `links = "foo"` can emit `cargo::metadata=KEY=VALUE`, and Cargo exposes it to the immediate dependent's build script as an environment variable [`DEP_FOO_KEY`](https://doc.rust-lang.org/cargo/reference/build-scripts.html#the-links-manifest-key). Note it only reaches direct dependents, not transitively.

The takeaway for both questions: it is turtles all the way down, but each turtle is a separate package with exactly one `build.rs`, and Cargo runs them bottom-up.
