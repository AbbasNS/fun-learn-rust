🦀 Tip of the day 41 follow-up

Follow-up questions from the discussion on [Tip 41: Cargo, Crates, and Packages](41-cargo.md).

## What is the typical granularity of a crate? A single class, a few related types, or a whole library?

Start with the terminology, because in practice the two terms line up almost every time. A crate is what the compiler builds, a package is what one `Cargo.toml` versions and publishes, and since a library package normally wraps exactly one library crate, everyone (crates.io included) just says "crate" for both.

At that level a crate is a library in the C++ sense. Think `libfoo` covering one coherent topic: serialization, regular expressions, an HTTP client. It is not a single class, and it is not one translation unit. The convention is one package per piece of functionality, the same way you would ship one library per capability.

That single published crate can itself be several crates linked together. A common shape is a thin facade crate that re-exports a few internal sub-crates, much like a C++ library assembled from multiple static archives presented as one. The user depends on one name, the implementation is split underneath:

```toml
# Cargo.toml of the facade crate
[dependencies]
foo-core = { version = "1.0", path = "../foo-core" }
foo-derive = { version = "1.0", path = "../foo-derive" }
```

```rust
// src/lib.rs of the facade crate: present one surface, hide the split
pub use foo_core::{Engine, Config};
pub use foo_derive::Build;
```

Rust steers away from the one-function package, so the floor stays at "a real library" rather than "a couple of loose helpers." If you are tempted to publish a single utility function, that is usually a sign it belongs inside a larger, topic-shaped crate instead.
