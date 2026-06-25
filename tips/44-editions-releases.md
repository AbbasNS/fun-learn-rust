🦀 Tip of the day 44: Editions, Releases, and Who Keeps the Promise

Coming from most languages, you treat a version upgrade with a little suspicion: it might deprecate an API, change a behavior, or break your build. Rust splits that worry into two separate mechanisms, each with its own job and its own promise.

Releases are the frequent ones: a new stable version every six weeks, purely additive. Each release adds features, compiles faster, and improves diagnostics, but it does not break working code. That is the *stability promise*: stay on your edition, and every future stable release keeps compiling your crate unchanged. Code from Rust 1.0 in 2015 still builds today.

Editions are the rare ones: an opt-in version of the language, released about every three years (2015, 2018, 2021, 2024, with 2027 in preparation). An edition is the one place breaking changes are allowed to live: new keywords, adjusted syntax, a tightened corner case. Upgrading your compiler never moves you onto a new edition, so the stability promise still holds. You take on those breaking changes only when you choose to bump the edition yourself, one crate at a time, and crates on different editions still build together. That is the *edition promise*: the language can keep evolving without fragmenting the ecosystem.

The rest of this tip is how those two promises are kept, and who keeps them.

Three release channels:

- *Stable* is what you ship. Released every six weeks. Backward-compatible with every previous stable version.
- *Beta* is what stable will be in six weeks. Useful for testing your code against the upcoming release before it lands.
- *Nightly* is built every night and exposes unstable features marked with `#![feature(...)]`. Required for experimental APIs and a few embedded targets.

`rustup` (the toolchain installer) makes switching between channels a single command: `rustup install beta`, `rustup default nightly`, etc.

All three are built in the open from one repository, [`rust-lang/rust`](https://github.com/rust-lang/rust): nightly is its `main` branch built each night, every six weeks that branch is forked to beta, and the previous beta is promoted to stable. It is one codebase riding a release train, not three separate products.

Editions are the mechanism behind that second promise. A crate declares its edition in `Cargo.toml`:

```toml
[package]
edition = "2024"
```

The compiler keeps supporting all editions forever. Your 2015-edition crate still compiles on the latest Rust. More importantly, crates of different editions can be used together in the same build with no friction. A library written in edition 2018 can be a dependency of a binary written in edition 2024, and vice versa. The ecosystem does not fragment.

What kinds of changes happen in editions?

- Edition 2018 reserved `async` and `await` as keywords (so they could become syntax later) and reformed the module path system.
- Edition 2021 added disjoint capture in closures (capturing only the fields a closure uses, rather than the whole struct), made arrays iterate by value (`IntoIterator` for arrays), and reserved some syntax for future use.
- Edition 2024 tightened lifetime capture rules in `impl Trait` returns, made `unsafe` requirements more explicit in extern blocks, and adjusted a few stdlib defaults.

Every change is small and surgical. No edition has rewritten the language. `cargo fix --edition` walks the diff for you and rewrites the parts that need rewriting.

How do features arrive in stable Rust? Through the *RFC process*. Anyone can write an RFC, a markdown document proposing a new feature or change. The relevant team discusses it publicly on GitHub, refines or rejects it, and merges accepted ones. Implementation happens on nightly, gated behind a feature flag, where it bakes for as many releases as needed. When the feature is stabilized, it lands on the next stable release, available without any flag, with the stability promise attached.

This is unhurried by design. The async keyword was reserved in 2018, `async`/`.await` stabilized in 2019, the async ecosystem has been refining itself since. The trade-off is that some long-anticipated features (specialization, generators) have been on nightly for years. The compiler team errs on the side of "we will only stabilize this when we are sure we will not regret it."

Who actually runs all this? No single person and no single company. The language is built by the *Rust Project*, a set of teams (compiler, language, library, infrastructure, and more), each owning its area and deciding by consensus rather than by decree. The language team signs off on language changes; there is no BDFL with a final veto. Since 2023, a *Leadership Council* with one representative per top-level team handles project-wide decisions, replacing the older core team.

Money is separate from design. The *Rust Foundation*, an independent nonprofit launched in 2021, is funded by corporate members (AWS, Google, Microsoft, Huawei, Meta, and, as of 2026, OpenAI). But it does not pay most of the people who build Rust. That work comes mostly from volunteers and from engineers whose employers pay them to contribute on company time. The Foundation funds the scaffolding around them: infrastructure like CI and crates.io, the trademarks, a small staff, grants, and (since 2026) a maintainers fund that pays people to look after critical pieces like the compiler and Cargo. It supports the work but does not direct the language, and paying members do not get to design features. That split is deliberate. Rust grew up inside Mozilla, and when Mozilla's funding receded in 2020, the Foundation gave the language a vendor-neutral home so no single company owns its direction.

Comparison:

- Python: PEP process for language changes, with a similar discussion-then-implementation arc, now governed by an elected Steering Council (Guido van Rossum stepped down as BDFL in 2018). Python 2 to 3 is the famous counter-example of an edition-style transition that did not work as smoothly.
- Java: JEPs and the OpenJDK process, with Oracle as the dominant steward. Backward compatibility is a strong commitment. Six-month release cadence since Java 9.
- Go: very small language with rare changes, designed and governed largely by a team at Google. Generics took until 1.18 (over a decade after 1.0). Backward compatibility is treated as sacred.
- C++: standard library updates per ISO standard, every three years. Less of a "promise" model, more of a "do not break the world" model that mostly holds.
- Rust: six-week stable releases, edition-gated breaking changes that do not fragment the ecosystem, a public RFC process for new features, and governance by independent teams under a nonprofit foundation rather than a single vendor.

The takeaway: Rust ships every six weeks, takes backward compatibility seriously, and uses opt-in editions to introduce occasional breaking changes without splitting the ecosystem. The RFC process is how new features land, decided by the Project's teams and funded, but not steered, by an independent foundation. The promise is that today's working code will keep working, and the compiler upholds it.

🔇 Python 2 to Python 3: a decade-long migration. Rust 2018 to 2024: change one line in `Cargo.toml`, run `cargo fix --edition`, done.
