🦀 Tip of the day 47: Cross-Compilation and Targets

`rustc` is a cross-compiler by design. The compiler that builds your code on a Linux laptop can produce a binary for a Windows desktop, a macOS server, an ARM phone, an embedded microcontroller, or a WebAssembly runtime, all from the same install. The mechanism is called a *target*.

A target is described by a triple: architecture, vendor, OS, and ABI, hyphen-separated. Some you will see often:

- `x86_64-unknown-linux-gnu`: 64-bit Intel/AMD Linux with the GNU toolchain.
- `aarch64-unknown-linux-gnu`: 64-bit ARM Linux. What you build for an ARM server or a Raspberry Pi.
- `x86_64-apple-darwin`: macOS on Intel.
- `aarch64-apple-darwin`: macOS on Apple Silicon.
- `x86_64-pc-windows-msvc`: 64-bit Windows with the MSVC toolchain.
- `x86_64-pc-windows-gnu`: 64-bit Windows with the MinGW toolchain, the easier target to build from Linux.
- `wasm32-unknown-unknown`: WebAssembly for browsers and minimal runtimes.
- `wasm32-wasip1`: WebAssembly with the WASI 0.1 system interface (file I/O, environment). Renamed from the old `wasm32-wasi`, which was removed from stable in Rust 1.84 (early 2025); `wasm32-wasip2` targets the newer WASI 0.2.
- `thumbv7em-none-eabihf`: a common ARM Cortex-M microcontroller target.

Adding a target to your toolchain:

```
rustup target add aarch64-unknown-linux-gnu
```

That downloads the precompiled `std` (or `core`/`alloc` for `no_std` targets) for the target. Then build for it:

```
cargo build --target=aarch64-unknown-linux-gnu --release
```

The output goes into `target/aarch64-unknown-linux-gnu/release/`.

Compiling is only half the job. `rustup target add` gives you the target's precompiled `std`, but turning that into a runnable binary needs a *linker* for the target plus that platform's system libraries. For a different architecture of the same OS (x86_64 Linux to aarch64 Linux), you just install the matching linker (`gcc-aarch64-linux-gnu`) or let `cross` supply one. Crossing to a different OS is where it gets real:

- To Windows, use the GNU target `x86_64-pc-windows-gnu` with the MinGW-w64 linker (`apt install mingw-w64`); it produces a working `.exe` and MinGW is free and open. Both Windows targets are tier 1, and `-msvc` is the default, most native one on Windows itself. The only reason to prefer `-gnu` when crossing from Linux is that its linker is freely available there, whereas `-msvc` wants Microsoft's linker and the Windows SDK (`cargo-xwin` downloads them for you).
- To macOS, `rustup target add aarch64-apple-darwin` installs `std`, but linking a Mach-O binary needs Apple's SDK (its frameworks and `libSystem`). Tools like `osxcross` or `cargo-zigbuild` can do it. The obstacle here is legal, not technical: Apple's SDK license permits use only on Apple hardware, which is why almost everyone builds macOS binaries on an actual Mac (CI services rent them for exactly this).

That licensing point generalizes, mostly. `rustc` and `std` are MIT/Apache-2.0, so Rust itself never restricts where you build; the limits come from what you link against. The Windows SDK carries its own terms, and the macOS SDK is Apple-hardware-only. The Linux C library is the exception that is more technical than legal: `glibc` is not built for static linking (a statically linked `glibc` still loads NSS modules at runtime, so DNS and user lookups can break), so fully static Linux binaries target `x86_64-unknown-linux-musl` instead. `musl` is designed for static linking, and as a bonus it is MIT-licensed rather than LGPL.

What about C libraries that your crate (or its dependencies) link to? Pure-Rust crates cross-compile out of the box. Crates with native dependencies (`openssl-sys`, `libsqlite3-sys`) need the C toolchain for the target as well, which is a separate problem. The community solution is `cross`, a wrapper that runs the build inside a Docker container with the right toolchain pre-installed:

```
cargo install cross
cross build --target=aarch64-unknown-linux-gnu
```

For pure Rust, you do not need `cross`. For native dependencies, you almost always do.

Rust ranks targets in three tiers by how thoroughly the Rust project itself builds and tests them (its own compiler and standard library, not your code):

- Tier 1: guaranteed to work. Rust ships official builds and runs its own compiler and `std` test suite on the target after every change; if the build or those tests fail, that release does not ship. The major desktop and server platforms.
- Tier 2: guaranteed to build. It ships a prebuilt `std` and keeps the target compiling, but does not always run those tests on it, so a successful build is not guaranteed to actually work. Most other common targets sit here.
- Tier 3: best-effort. The compiler supports the target, but the project neither builds nor tests it automatically and ships no prebuilt `std`. Niche or experimental.

The full list of targets and their tiers lives in the [Rust platform support](https://doc.rust-lang.org/rustc/platform-support.html) documentation.

A subtle point about builds. Build scripts (`build.rs`, covered later) and procedural macros run during compilation, not in the final binary, so they always build for the host (your laptop's target) regardless of `--target`. Cargo handles this automatically: build dependencies from tip [42](42-dependencies.md) are compiled for the host, while normal dependencies are compiled for the target.

Comparison:

- C, C++: cross-compilation is possible but a project of its own. You assemble a cross-toolchain, set up sysroots, and point the build system at it. Days of work for a new target.
- Go: native cross-compilation since 1.5. `GOOS=linux GOARCH=arm64 go build` works for pure Go, similar story to Rust for cgo dependencies.
- Java: bytecode is target-independent. The JVM does the cross-target work at runtime.
- JavaScript, Python: interpreted, target-independent. The runtime handles platform differences.
- Rust: `rustup target add` plus `--target`, with `cross` for native dependencies. Closer to Go than to C++.

The takeaway: `rustc` is a cross-compiler. `rustup target add <triple>` installs the target's standard library and `cargo build --target=<triple>` produces a binary, as long as you also have a linker and system libraries for that target. Pure-Rust crates cross-compile cleanly; native dependencies usually need the `cross` tool; and a foreign-OS target can run into licensing limits, most notably macOS, whose SDK is licensed for Apple hardware only. Tier 1 targets are guaranteed to keep working; tier 3 are best-effort.

🔇 C++ cross-compilation: a weeklong yak shave. Rust cross-compilation: `rustup target add` plus `cargo build --target=`. Done, unless you depend on `openssl`, in which case see also: weeklong yak shave.
