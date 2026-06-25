🦀 Tip of the day 43: The Standard Library, and What Is Not In It

Most languages either ship a huge standard library that tries to cover everything (Python, Java) or a tiny one that leaves the rest to package managers (C, JavaScript). Rust takes the middle path with a deliberate twist: the standard library is small, the package ecosystem is large, and the boundary is drawn for a specific reason.

Rust's standard library is actually three nested layers, each adding something the previous one cannot do.

`core` is the innermost layer. It has no dependency on an allocator and no dependency on an operating system. You get the primitive types (`i32`, `bool`, `&str`, slices), the foundational traits (`Iterator`, `Default`, `Clone`, `Drop`, `From`), and most of the language's built-in operations. What you do not get is anything that needs to call `malloc` or read a file. `core` is what works on a microcontroller with no heap.

`alloc` adds heap-allocating types: `Box`, `Vec`, `String`, `Rc`, `Arc`, `BTreeMap`, the basic collections. It requires an allocator but still does not touch the operating system. This is the layer that lets embedded code with a heap (a board with some RAM but no OS) use the familiar containers.

`std` is the full standard library. It pulls in `core` and `alloc`, and adds everything that requires the OS: file I/O (`std::fs`), threads (`std::thread`), time (`std::time`), networking (`std::net`), environment variables, processes, and the synchronization primitives from tip [33](33-arc-mutex.md). This is what you use on Linux, macOS, Windows, and other hosted targets.

When you write a regular Rust program, `std` is loaded for you. A small set of items is also auto-imported into every module so you never have to write `use` for them. This set is called the *prelude*: `Option`, `Result`, `String`, `Vec`, `Box`, the iterator traits, the conversion traits from tip [39](39-from-into.md) (`From`, `Into`), the common derivable traits (`Clone`, `Copy`, `Default`, `PartialEq`), and everyday macros like `println!` and `vec!`. The exact list depends on the edition (more on editions later): the 2021 edition added `TryFrom` and `TryInto`, and the 2024 edition added `Future` and `IntoFuture`. The prelude stays small; everything else needs an explicit `use`.

To opt out of `std`, you write `#![no_std]` at the crate root. This is how kernels, bootloaders, embedded firmware, and certain WebAssembly modules are written in Rust. Many crates pull off the trick of supporting both worlds with a `std` feature flag (tip [42](42-dependencies.md)).

Now the deliberate small-stdlib part. The following are *not* in the standard library:

- `serde` for serialization, with format crates like `serde_json` and `toml` built on top of it.
- `tokio`, `smol`, or any other async runtime. The language has `async`/`.await` syntax, but no built-in executor.
- `reqwest` or any HTTP client.
- `regex`.
- `rand` for random number generation. The standard library does not ship an RNG.
- Any GUI framework, image format support, audio, or graphics.

These live on `crates.io`, maintained by individuals and teams across the ecosystem. The reasoning is twofold. First, the standard library follows Rust's backwards-compatibility promise: once an item is stabilized, it can be added to or deprecated, but never removed or changed in a breaking way. A design mistake in `std` is permanent. A crate, by contrast, can ship a breaking `2.0` and start over. Second, the leading solutions in domains like async runtimes are still actively iterating. Putting one in `std` would freeze a particular winner, current flaws and all, before the field is settled.

Comparison:

- Python: famously batteries-included. The standard library has HTTP, JSON, regex, threading, multiprocessing, sockets, dates, and more. Trade-off: large surface area, slower evolution, occasional cruft (recent versions have started pruning long-dead modules).
- Java: large standard library (`java.util`, `java.io`, `java.nio`, `java.net`, `java.time`). Similar trade-offs.
- C: standard library is tiny. Strings, basic I/O, math. Every project reimplement basic functionalities, or pulls in third-party libraries for anything substantial.
- C++: a substantial standard library: containers and algorithms, strings, iostreams, threads and mutexes (since C++11), `<filesystem>` (since C++17), plus `<regex>`, `<random>`, and `<chrono>`. Notably it bundles a regex engine and a random number generator, both of which Rust pushes out to crates. It still has no networking, JSON, or HTTP client; the long-proposed networking addition never landed.
- Go: medium-sized, with an HTTP server, JSON, and crypto built in. Aggressive about adding what most projects need, and still growing (recent releases added structured logging and generic `slices`/`maps` helpers), so external packages stay rare.
- JavaScript: the language itself has a small standard library with no file or network access; those come from the host. Browsers expose large Web APIs, and Node.js, Deno, and Bun each ship a sizable runtime stdlib.
- Rust: small, stable `std` plus a healthy crates ecosystem for everything else. The trade-off is that you reach for `Cargo.toml` more often than in Python or Go.

The takeaway: `core` for no-allocator targets, `alloc` adds heap collections, `std` adds OS access. The prelude auto-imports the most-used types. The standard library is intentionally small; serialization, HTTP, async runtimes, and most other domains live on `crates.io`.

🔇 Rust: a small standard library and a great package manager to fill the gaps. Python: a huge standard library, and a couple of package managers for the gaps it left anyway. C++: gaps.
