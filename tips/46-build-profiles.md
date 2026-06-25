🦀 Tip of the day 46: Build Profiles, or Why You Want `--release` Before Benchmarking

The first time someone benchmarks a Rust program with `cargo run` and concludes "Rust is not actually fast," they have learned something more useful than they realize. The default `cargo build` and `cargo run` use the *dev* profile: optimization level zero, full debug info, overflow checks turned on. The result builds in two seconds and runs an order of magnitude slower than it could.

`cargo build --release` switches to the *release* profile, which sets opt-level 3, drops most checks, runs LLVM's full optimization passes, and produces a binary that is often several times faster on the same code, and dramatically faster on tight numerical loops where the optimizer can erase bounds and overflow checks. This is the difference between "feels sluggish" and "competitive with C++."

Profiles are configured in `Cargo.toml`. The defaults look approximately like:

```toml
[profile.dev]
opt-level = 0
debug = true
overflow-checks = true
incremental = true

[profile.release]
opt-level = 3
debug = false
overflow-checks = false
lto = false
codegen-units = 16
```

The knobs worth knowing:

- `opt-level`: 0 (dev default, no optimization), 1, 2, 3 (release default, full optimization). `"s"` optimizes for size, `"z"` optimizes harder for size at the cost of speed. Embedded developers reach for `"s"` or `"z"` often.
- `debug`: include DWARF debug information. Disabled in release because it triples binary size and slows linking. Set it to `"line-tables-only"` if you want backtraces but not full debug symbols.
- `overflow-checks` and `debug-assertions`: both on in dev, off in release. Integer overflow panics in dev and wraps silently in release, and `debug_assert!` checks only fire in dev. Bugs to catch early while developing, measurable costs to drop when you ship.
- `lto` (Link-Time Optimization): `false` (default), `"thin"` (modest cost, modest gain), `true` or `"fat"` (slow build, more aggressive cross-crate inlining). Worth it for shipping; not worth it during development.
- `codegen-units`: how many parallel chunks LLVM splits the crate into. More units means faster compilation, less aggressive optimization. Set to `1` for max performance, leave at the default for build speed.
- `panic`: `"unwind"` (default, runs destructors during a panic, larger binary) or `"abort"` (panic kills the process immediately, smaller binary). `"abort"` is common for embedded and CLI tools.
- `incremental`: rebuilds only changed code. On by default in dev, off in release because it interferes with optimization.

For most projects, the defaults are fine. For a binary you ship, a common tuned release profile is:

```toml
[profile.release]
lto = "fat"
codegen-units = 1
panic = "abort"
strip = true
```

`strip = true` removes leftover symbols, sometimes shaving megabytes. The trade is longer build time for a smaller, cleaner, faster binary.

If you want to scrub absolute source paths out of the binary and panic messages (which helps reproducible builds and avoids leaking your home directory path to whoever runs the program), there is `trim-paths = "all"`. It is still nightly-only, gated behind `-Z trim-paths`, so reach for it only on a nightly toolchain until it stabilizes.

You can also define custom profiles. A common one is `production`, which sets `lto` explicitly rather than relying on what `release` happens to be, and keeps line-table debug info for backtraces in crash reports:

```toml
[profile.production]
inherits = "release"
lto = "fat"
debug = "line-tables-only"
strip = "debuginfo"
```

Override at the call site with `cargo build --profile production`.

Two surprises worth knowing. `cargo test` builds with the `test` profile (which inherits dev) and `cargo bench` builds with the `bench` profile (which inherits release), so anything you measure through `cargo bench` is already optimized. And when dev builds drag because of one heavy dependency, you can optimize just your dependencies while keeping your own crate fast to compile:

```toml
[profile.dev.package."*"]
opt-level = 3
```

Comparison:

- C, C++: `-O0` through `-O3`, `-Os`, plus dozens of flags. No profile abstraction; you wire them up in your build system.
- Go: `-ldflags`, build tags, sparse optimization controls. The compiler decides most things.
- Rust: profiles in `Cargo.toml`, named and inheritable, applied uniformly to every crate in the build.

The takeaway: dev builds optimize for compile speed, release builds optimize for run speed. `cargo build --release` flips the profile. Tune `lto`, `codegen-units`, and `panic` when you ship; ignore them otherwise. Always benchmark with `--release`.

🔇 Dev compiles in two seconds and runs forever; release flips it. Pick your forever. Python skips the question and runs forever anyway.
