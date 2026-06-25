🦀 Tip of the day 42 follow-up

Follow-up questions from the discussion on [Tip 42: Dependencies, Cargo.toml, and the Crates Ecosystem](42-dependencies.md).

## Are all dependencies handled as source code, or can you depend on closed-source, precompiled libraries?

By default, everything is source. Cargo downloads each dependency's source and compiles it into your build. Depending on a crate is closer to rebuilding a library from source and statically linking it than to linking a prebuilt `.lib` or `.so`.

The reason is that Rust deliberately has no stable ABI. Where a C or C++ library prebuilt for your platform links as-is, a compiled Rust library is not guaranteed to link across compiler versions, so Rust-to-Rust is always built from source.

Closed-source dependencies are still supported, just not as Rust binaries. The usual path is to keep the source private behind a private registry or a private Git dependency. It stays proprietary to your organization, but it is still compiled from source by whoever has access:

```toml
[dependencies]
# private Git dependency: source stays in your org, Cargo still builds it
internal-lib = { git = "ssh://git@github.com/your-org/internal-lib", branch = "main" }
```

When you genuinely cannot ship any source, you fall back to the one ABI that Rust and C++ both speak: the C ABI. You ship a precompiled native library (`.a`, `.so`, `.dll`) that exposes a C interface, plus a thin Rust wrapper crate that declares the symbols and links against it. This is exactly how you would pull a closed-source C library into a C++ project.

The wrapper crate declares the foreign symbols with `extern "C"` and tells Cargo what to link:

```rust
// thin binding layer: this is the only part that ships as source
#[link(name = "proprietary")] // links libproprietary.a / .so / .dll
extern "C" {
    fn compute_secret(input: i32) -> i32;
}

pub fn compute(input: i32) -> i32 {
    // safe wrapper around the foreign call
    unsafe { compute_secret(input) }
}
```

The proprietary logic lives in the compiled binary. Only the small `extern "C"` binding layer is source. The ecosystem also has crates like [`abi_stable`](https://crates.io/crates/abi_stable) for loading Rust libraries at runtime, but the C ABI route is the portable, language-agnostic fallback when you need to keep the real logic compiled.
