🦀 Tip of the day 45: What `cargo build` Actually Does

You typed `cargo build`. Some seconds later, an executable appeared. What happened?

Cargo is an orchestrator. It figures out which crates need compiling, in what order, and shells out to `rustc` (the actual compiler) for each one. After every crate has produced its object files, Cargo invokes the system linker to stitch them into a final binary.

`rustc` itself is a multi-stage pipeline. Source text is lexed and parsed into an AST. Macros are expanded, names are resolved, the AST is lowered into the High-level IR (HIR), and type checking runs. HIR is lowered again into the Mid-level IR (MIR), a simpler control-flow graph where the borrow checker runs. (The error messages from tips [18](18-ownership.md)-[22](22-lifetimes.md) come from the borrow checker on MIR.) Finally, MIR is lowered into LLVM IR, and LLVM does its own optimizations and emits object code.

That output, one or more `.o` files, gets passed to a linker. On large projects linking can dominate clean-build time, so it is worth knowing. Each platform picks a default, and you can override it:

- Linux: historically GNU `ld`. Since Rust 1.90 (September 2025), the bundled `rust-lld` is the default on `x86_64-unknown-linux-gnu`, making some incremental rebuilds link up to 7x faster. Other Linux targets still default to GNU `ld`.
- macOS: Apple's linker (the classic `ld64` gained a faster replacement in Xcode 15).
- Windows: `link.exe`, the MSVC toolchain's linker, since the default Windows target links against the MSVC runtime.

`lld` is LLVM's linker, and it works on all three platforms under different driver names: `ld64.lld` on macOS, `lld-link` on Windows (a drop-in replacement for `link.exe`), and `rust-lld` (the bundled copy) on Linux. Outside `x86_64-unknown-linux-gnu` it stays opt-in. Faster does not make it the default: Rust switches one target at a time and started with Linux, where GNU `ld` is the slowest of the three, while Windows and macOS keep their native linkers (which, unlike lld, still do incremental linking) for now. `mold` is faster still, but Linux-only. Its macOS port `sold` is now archived: Apple's own linker became fast enough in Xcode 15, so even its author recommends using that instead. To switch linker, for example to `mold` on Linux, set it in `.cargo/config.toml`:

```toml
[target.x86_64-unknown-linux-gnu]
linker = "clang"
rustflags = ["-C", "link-arg=-fuse-ld=mold"]
```

Are there alternative compilers? Practically, no. `rustc` with LLVM is the only production toolchain. The notable alternatives:

- `rustc_codegen_cranelift`: a non-LLVM back-end aimed at faster debug builds (commonly 20-30% quicker). It ships with nightly through rustup and can be enabled per project, but it produces slower binaries and still lacks full debugger support.
- `rustc_codegen_gcc`: a GCC back-end for `rustc`. Experimental.
- `gccrs`: a separate Rust front-end inside GCC. It landed in GCC 15 (2025) but cannot yet compile the standard library, so it is not ready for serious work.
- `mrustc`: a minimal Rust compiler used for bootstrapping `rustc` itself. Not for users.

The reason `rustc` is essentially the only choice is that for most of Rust's life there was no formal specification. The reference implementation was the spec, which makes an independent front-end a multi-year project. That is finally changing: in 2025 the Rust Project adopted the Ferrocene Language Specification and began folding it into an official spec. But a written spec does not conjure competing compilers overnight, so for now "the Rust compiler" still means `rustc`.

Comparison:

- C, C++: many compilers (GCC, Clang, MSVC, ICC). A standardized language definition lets them coexist.
- Java: `javac` for the front-end; HotSpot, OpenJ9, GraalVM for the runtime. Multiple back-ends in production use.
- Go: `gc` (the standard) and `gccgo` (alternative). One dominant.
- Python: CPython, PyPy, MicroPython, Jython. Several production implementations.
- Rust: `rustc` with LLVM, period. Alternative back-ends and front-ends exist, but none are production-ready.

The takeaway: `cargo build` orchestrates `rustc` per crate, which runs through parse → HIR → type-check → MIR → borrow-check → LLVM → object files. The system linker then stitches the objects into an executable, and on x86_64 Linux that linker is now the fast `rust-lld` by default.

🔇 Rust shipped for a decade with one compiler and no spec. Turns out "the compiler is the specification" compiles just fine.
