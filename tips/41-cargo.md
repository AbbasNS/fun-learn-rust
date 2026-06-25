🦀 Tip of the day 41: Cargo, Crates, and Packages

Most languages need three or four tools to build a project: a compiler, a build system, a package manager, a test runner. Rust ships one tool that does all of them. It is called Cargo, and it is the closest the ecosystem comes to a single answer for "how do I build, run, test, document, and publish my code."

Three terms that get confused all the time:

- A *crate* is a unit of compilation. The compiler takes one crate as input and produces a single binary or library as output. Each crate is either a binary (entry point in `main()`) or a library (no entry point, code that other crates pull in).
- A *package* is what `Cargo.toml` describes. A package contains *one* library crate (at most) and *any number* of binary crates. Both kinds can coexist in the same package.
- A *workspace* is a top-level `Cargo.toml` that groups multiple packages so they share a `Cargo.lock` and a single `target/` directory. Useful for projects split into several internal crates.

A typical package layout:

```
mypkg/
├── Cargo.toml          // package metadata and dependencies
├── Cargo.lock          // exact resolved versions, like a lockfile
├── src/
│   ├── lib.rs          // optional library crate
│   ├── main.rs         // optional binary crate (named "mypkg")
│   └── bin/
│       └── tool.rs     // additional binary, run with `cargo run --bin tool`
├── tests/              // integration tests
├── examples/           // example programs
└── benches/            // benchmarks
```

Cargo discovers all of this from convention. You do not configure it.

The commands you will use most (before agents):

- `cargo new <name>` creates a new package, with a starter `Cargo.toml` and `src/main.rs`. Add `--lib` to start with `src/lib.rs` instead.
- `cargo build` compiles in debug mode (fast to build, slow at runtime, with overflow checks and other safety belts). Add `--release` for an optimized build.
- `cargo run` builds and runs the binary crate. Forward arguments after `--`: `cargo run -- arg1 arg2`.
- `cargo check` typechecks without producing an executable. Many times faster than `cargo build` because it skips code generation.
- `cargo test` compiles and runs every test in the package: unit tests, integration tests, and doc tests.
- `cargo doc --open` generates HTML documentation from doc comments and opens it in your browser. `docs.rs` automatically builds and hosts these for every crate published to crates.io.
- `cargo update` updates `Cargo.lock` to the newest versions allowed by `Cargo.toml`.

Cargo parallelizes builds by default: independent crates in the dependency graph compile at the same time, and within a single crate `rustc` splits code generation across threads. Linking, the final step that stitches the compiled pieces into one binary, mostly runs single-threaded and is often the bottleneck on incremental rebuilds, where you recompile one crate but still relink everything. The full pipeline, and how to make linking faster, is covered later when we look at what `cargo build` actually does.

Two more tools usually live next to Cargo and feel built-in: `cargo fmt` (the formatter, `rustfmt`) and `cargo clippy` (the linter). They are technically separate components, but they ship with most toolchain installations.

Workspaces let you keep several related packages in one repository without each one fetching dependencies separately. A workspace `Cargo.toml` looks like:

```toml
[workspace]
members = ["core", "cli", "server"]
```

Each member has its own `Cargo.toml` and `src/`, but they share a single resolved dependency graph and a single `target/` directory. This is how large projects (the Rust compiler itself, frameworks like axum or bevy) are organized.

Comparison:

- Java: Maven and Gradle handle builds and dependencies, but they are external to the language and configured in XML, Groovy, or Kotlin. Test runners are separate.
- Python: historically `pip` for packages, `setuptools` or `poetry` for builds, `pytest` for tests, all loosely coupled. `uv` (2024 onward) is closing the gap fast: one Rust-built tool, explicitly modeled on Cargo, that handles packaging, virtual environments, and even Python versions.
- Node.js: `npm` (or `yarn`, `pnpm`) handles packages, scripts, and runs through `package.json`. `bun` (itself rewritten from Zig to Rust in 2026, much of it AI-generated) goes further, folding runtime, package manager, bundler, and test runner into one binary, the closest in spirit to Cargo.
- Go: `go` itself is the build system, formatter, and tester, and a package manager since 1.11 (modules); the build, format, and test tooling predates that. Same one-tool philosophy as Cargo, slightly less feature-rich.
- C and C++: pick one (or several!) from each column and pray they get along. A compiler: gcc, clang, msvc, or whatever your embedded vendor shipped. A build system: make, cmake, meson, bazel, or the shell script someone wrote in 2005. A package manager: vcpkg, conan, or the time-honored tradition of copying headers into your repo and never speaking of it again. There is no blessed default, so every project invents its own combination, and getting two of them to agree on where a header file lives is still treated as a personality test. Even now, with an AI on every shoulder, the workflow has not changed: have it generate a `CMakeLists.txt` you do not fully understand, have it explain the linker error that follows, and quietly vibe code your build system and package manager into existence one prompt at a time. Choose your fighter.
- Rust: Cargo handles building, dependencies, tests, docs, benches, and publishing in one tool with one config file.

The takeaway: a *crate* is what the compiler builds, a *package* is what `Cargo.toml` describes, and a *workspace* groups packages. Cargo is the one tool that drives all of it, and most days you only need `cargo build`, `cargo run`, `cargo test`, and `cargo check`.

🔇 Cargo builds, tests, documents, and publishes, all from one tool. The link times are what give you time to read tips like this one.
