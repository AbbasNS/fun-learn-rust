🦀 Tip of the day 48: Build Scripts, When Cargo.toml Cannot Do Enough

Tip [45](45-compilation-pipeline.md) traced what `cargo build` does, and the tips since covered build profiles and cross-compilation; to finish that story of how Cargo builds your code, we need build scripts.

A typical Rust crate is just source code: declare your dependencies, write your `.rs` files, and let Cargo and `rustc` do the rest. Some crates need more. They might link to a C library, generate Rust source from a schema, or check the environment for a feature flag. For these, Cargo runs a *build script* before compiling the crate.

A build script is a file named `build.rs` at the package root. Cargo detects it automatically, compiles it as a small standalone Rust program, and runs it before the rest of the crate. It reads the script's standard output and treats any line starting with `cargo::` as an instruction. These instructions are a fixed set Cargo defines, one `cargo::key=value` per line: you pick from the list, you cannot invent your own, and an unknown key fails the build. The full set lives in the [Cargo book](https://doc.rust-lang.org/cargo/reference/build-scripts.html); the ones below are the common ones. (The double-colon form is the current one, from Rust 1.77 on; the single-colon `cargo:` you will see in older crates still works.) Everything else the script prints is captured to a log file and hidden unless you build with `-vv`, so a stray `println!("debugging")` will not show up where you expect.

The most common job is linking a native library. If your crate wraps a C library, you tell the linker where to find it:

```rust
// build.rs
fn main() {
    println!("cargo::rustc-link-lib=foo");         // link against libfoo
    println!("cargo::rustc-link-search=/opt/foo"); // illustrative; real crates never hardcode this
}
```

Crates ending in `-sys` (`openssl-sys`, `libsqlite3-sys`) do exactly this. Such a crate also sets `links = "foo"` in the `[package]` table of `Cargo.toml`, which tells Cargo it owns linking `libfoo`. Cargo then forbids any two crates from claiming the same library, which prevents duplicate-symbol clashes. To find the real paths, `-sys` crates lean on the `pkg-config` crate (to locate an already-installed library) or the `cc` crate (to compile a bundled C source), never a hardcoded path.

The second common job is generating Rust source. The script writes a `.rs` file into a directory Cargo hands it through the `OUT_DIR` variable, and the crate pastes it in:

```rust
// build.rs
use std::{env, fs};

fn main() {
    // OUT_DIR is the only directory a build script may write to.
    let out_dir = env::var("OUT_DIR").unwrap();
    fs::write(format!("{out_dir}/table.rs"), "pub const VALUE: u32 = 42;").unwrap();
}
```

```rust
// src/lib.rs
include!(concat!(env!("OUT_DIR"), "/table.rs"));
```

Here `include!` pastes another file's contents in as if you had typed them, `env!` reads an environment variable at compile time, and `concat!` joins the pieces into one path. This is how `prost` (Protocol Buffers) and `bindgen` (C header bindings) work. Write only into `OUT_DIR`: writing into your own `src/` tree breaks caching and can make the script re-run forever.

The third job is detecting the environment. Cargo sets variables like `TARGET` and `HOST` (compare them to spot cross-compilation), `CARGO_CFG_TARGET_OS` (platform decisions), and `PROFILE` (debug vs release). The script can then emit `cargo::rustc-cfg=NAME`, read back with `#[cfg(...)]` or `cfg!(...)` as a compile-time on/off switch, or `cargo::rustc-env=KEY=VALUE`, read back with `env!(...)` to bake a computed string such as a git hash into the binary.

Whichever of these your script does, Cargo needs to know when to re-run it:

```rust
println!("cargo::rerun-if-changed=src/schema.txt");
```

Without any `rerun-if` directive, Cargo plays it conservative: it re-runs the script whenever any file in the package changes (by file timestamp), not on every build. But emitting even one `rerun-if` line flips that off and tells Cargo to watch only what you list. Forget a file your script reads, and edits to it will not trigger a rebuild, leaving you with a silently stale binary. (There is also `cargo::rerun-if-env-changed=VAR` for scripts driven by an environment variable.)

A build script has its own dependencies, listed under `[build-dependencies]` in `Cargo.toml` (tip [42](42-dependencies.md)). These always compile for the host, regardless of `--target`, since the script runs on your machine at build time (the host-versus-target split from tip [47](47-cross-compilation.md)).

The downsides are real:

- They slow `cargo build` down: extra Rust code to compile and run.
- They make builds harder to reproduce, especially when they read the environment.
- A forgotten `rerun-if` input gives you the silently stale builds described above.
- A dependency's misbehaving build script poisons your build until the upstream fix lands.

Most projects do not need one. Reach for a build script when you have a real reason: native library linking, code generation from a schema, or environment-aware compilation. For everything else, `Cargo.toml` is enough.

Every ecosystem has its own version of this. In C and C++, build systems hook arbitrary commands through `make` or `cmake`. Maven runs plugins at lifecycle phases like `generate-sources`. Go's `go generate` is a code generator you run yourself, separate from `go build`, closer to a manual step than Rust's automatic `build.rs`. Rust's twist is one `build.rs` per package, run for you, talking to Cargo through `cargo::` lines on stdout.

The takeaway: `build.rs` is a small Rust program Cargo runs before compiling your crate to link native libraries, generate source, or read the build environment, and most crates never need one.

🔇 The first time you write a `build.rs` you feel powerful. The second time you write a `build.rs` you wonder if there is a way to avoid writing a `build.rs`. The third time you write a `build.rs` you give up and accept that this is your life now.
