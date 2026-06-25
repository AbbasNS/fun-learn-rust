🦀 Tip of the day 42: Dependencies, Cargo.toml, and the Crates Ecosystem

Tip [41](41-cargo.md) covered Cargo's local commands. The other half of Cargo's job is pulling in code other people wrote. The mechanism is straightforward: list the crates you want in `Cargo.toml`, run any Cargo command, and they appear in your project.

The basic shape:

```toml
[package]
name = "mypkg"
version = "0.1.0"
edition = "2024" # Rust edition, covered in a later tip

[dependencies]
serde = "1.0"
tokio = { version = "1.40", features = ["macros", "rt"] }
anyhow = "1"
```

The first time you build, Cargo resolves the version graph, downloads the crates from [crates.io](https://crates.io) (the default registry), compiles them, and writes the resolved versions to `Cargo.lock`. From then on, `Cargo.lock` pins the exact versions every contributor and CI run will use, until someone runs `cargo update`.

Now the version specifiers, because they are the most-misread part of Cargo. The default form is `^`, the caret:

- `serde = "1.0"` is shorthand for `^1.0`. Allows `>=1.0.0, <2.0.0`. The rule is "the leftmost non-zero digit is the compatibility anchor." Most crates land here.
- `serde = "1.2.3"` is shorthand for `^1.2.3`. Allows `>=1.2.3, <2.0.0`.
- For `0.x.y` versions, the caret behaves differently: `^0.2.3` allows `>=0.2.3, <0.3.0`. This is intentional, because crates pre-1.0 are expected to break minor-version boundaries.

Other specifiers:

- `~1.2.3`: tilde. Allows `>=1.2.3, <1.3.0`. Patch-level updates only.
- `=1.2.3`: exact match. Use sparingly; it makes upgrading fragile.
- `>=1.2, <2.0`: ranges, useful when you need to express compatibility precisely.
- `*`: any version. Almost always the wrong answer.

The combination of `^` semver in `Cargo.toml` and exact pinning in `Cargo.lock` gives you the best of both worlds: room for compatible upgrades, plus reproducible builds.

Then there are *features*. A feature is an opt-in compile flag that crates expose to their users. The crate author defines them in their own `Cargo.toml`:

```toml
[features]
default = ["std"]
std = []
extra-utils = []
```

Users opt in or out:

```toml
[dependencies]
mycrate = { version = "1.0", features = ["extra-utils"] }
otherdep = { version = "1.0", default-features = false }
```

Features control which code compiles. They let one crate serve both a full async runtime and a tiny embedded build without bloating either case. `tokio` is the textbook example: features like `rt`, `macros`, and `net` pull in only the parts you use, and `serde` keeps its derive macros behind an opt-in `derive` feature for the same reason.

Two cousin sections to `[dependencies]`:

- `[dev-dependencies]`: included only when running tests, examples, or benchmarks. Crates like `criterion` or `mockall` go here so your library users do not have to download them.
- `[build-dependencies]`: included only when running a `build.rs` build script (a Rust file that runs at build time, used for code generation, linking native libraries, etc.). Most projects do not need this.

You can also depend on a path or a Git repository directly, useful for local development and for crates not (yet) on crates.io:

```toml
[dependencies]
neighbor = { path = "../neighbor" }
unreleased = { git = "https://github.com/example/unreleased", branch = "main" }
```

How the resolver handles overlaps:

Cargo's resolver walks your whole dependency graph, picks the highest versions that satisfy every requirement (backtracking when they conflict), and writes the result to `Cargo.lock`, so you rarely choose versions by hand. When two dependencies want the same crate, semver decides the outcome. Compatible requirements (`1.2` and `1.5` both mean `<2.0.0`) unify to a single shared copy, which is what lets a type from one dependency pass cleanly into another. Incompatible ones (`1.x` and `2.x`, or `0.6` and `0.7`) are kept side by side rather than rejected, which can surprise you with an `expected X (v1), found X (v2)` error where the two meet; `cargo tree --duplicates` shows what got doubled. The error only shows up at the specific point where a value has to cross from one version's world into the other's.

Features are merged, not duplicated. If two dependencies pull the same shared crate with different features, the resolver builds one copy with the union of those features. That is exactly why features must be additive: everyone shares that single build, so enabling a feature must never break a dependent that did not ask for it. The lone exception is a crate with a `links` key to a native library, which may appear only once, so two incompatible `-sys` versions are a hard error rather than a duplicate.

The resolver itself is versioned, set by the `resolver` field and defaulted by your edition. Resolver 2 (the 2021 edition default) stopped merging features across normal, build, and dev dependencies, so a build script's heavy features no longer leak into your library. Resolver 3 (the 2024 edition default used above) adds MSRV (minimum supported Rust version, covered in a later tip) awareness: it prefers dependency versions compatible with your declared `rust-version` rather than always taking the newest.

Finding a crate:

crates.io uses one flat namespace, so names are first-come, first-served with no `@org/` scoping. That makes browsing easy and typosquatting easy too, so copy a crate's name from a source you trust rather than typing it from memory. The usual places to look: [crates.io](https://crates.io) itself (sort by recent downloads), [lib.rs](https://lib.rs) (an alternative index with sharper categories and maintenance signals), [blessed.rs](https://blessed.rs/crates) (a hand-curated list of the go-to crate per job), and [docs.rs](https://docs.rs) (auto-built docs for every release, and good docs are a quality signal in themselves). Before adding one, glance at its download count, last release date, and how many transitive dependencies it drags in.

Why Cargo is considered safer than npm:

- No install-time code execution. `npm install` automatically runs each package's `postinstall` and similar hooks, which is how one compromised package can run malware the moment you add it. Cargo runs nothing on `cargo add` or fetch. A crate's code runs only when you build it (through a `build.rs` script or a proc macro) or when you actually call it.
- Immutable releases. Once a version is published to crates.io it cannot be overwritten or deleted, only *yanked* (hidden from new version resolution). The bytes you locked yesterday are the bytes you get today.
- Fewer, larger dependencies by culture. The ecosystem leans away from hundreds of one-line packages, so there are fewer authors to trust. This is a tendency, not a guarantee; plenty of crates still pull in dozens of transitive dependencies.

None of this makes Rust immune. A malicious `build.rs` or proc macro still runs arbitrary code at compile time, and the borrow checker does nothing about that. npm has also closed many gaps (lockfile integrity hashes, restricted unpublish, `npm audit`). The honest version is that Cargo's defaults expose a smaller attack surface, not zero. To check what you already depend on, run `cargo audit`, which compares `Cargo.lock` against the [RustSec advisory database](https://rustsec.org); larger teams add [`cargo vet`](https://mozilla.github.io/cargo-vet/) to share human review of each crate.

A few crates are effectively standard and safe to reach for first: `serde`, `tokio`, `anyhow` and `thiserror`, `clap`, `regex`, `rayon`.

The takeaway: declare crates in `[dependencies]`, let caret semver allow compatible upgrades while `Cargo.lock` pins exact versions, and use features to compile only what you need. Find crates through crates.io, lib.rs, and blessed.rs, and lean on Cargo's safer defaults (no install-time code, immutable releases, `cargo audit`) without ever assuming a dependency is free to trust.

🔇 One flat namespace, first come first served. The perfect name for your crate was claimed in 2015 by a project with three downloads and no commits since.
