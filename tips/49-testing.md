🦀 Tip of the day 49: Testing, the Topic We Postponed for 48 Tips

You have written a lot of Rust by now. None of it has been tested, at least not in this series. Time to fix that. Rust ships testing as a first-class feature: no test framework crate to install, no convention to debate, no separate binary to build. You write `#[test]` and `cargo test` does the rest.

The simplest test is a function with the `#[test]` attribute:

```rust
#[test]
fn it_adds() {
    assert_eq!(2 + 2, 4);
}
```

`cargo test` discovers every `#[test]` function in the package, compiles a test binary, and runs them in parallel. The output reports passes, failures, and ignored tests in the familiar `running 5 tests / test it_adds ... ok` format.

The standard assertion macros:

- `assert!(cond)`: panic if `cond` is false. Pass a custom message as a second argument.
- `assert_eq!(a, b)`: panic if `a != b`. The failure message shows both values, labeled `left` and `right` rather than `expected` and `actual`, so there is no argument order to memorize. Easier to debug than a bare `assert!(a == b)`.
- `assert_ne!(a, b)`: the inverse.

`assert_eq!` and `assert_ne!` print both values on failure, so your types need `#[derive(PartialEq, Debug)]` (the comparison uses `PartialEq`, printing uses `Debug`; see derive macros in tip [26](26-derive-macros.md)). The built-in numeric types already have them.

A few attributes for shaping tests:

- `#[should_panic]`: the test passes only if the body panics. Add `expected = "..."` to require a specific message.
- `#[ignore]`: skip the test by default. Run only the ignored tests with `cargo test -- --ignored`, or the whole suite including them with `cargo test -- --include-ignored`.

Rust has three places tests can live, with different scopes:

1. Unit tests live right next to the code they test. Here is the surprise: in most languages tests sit in a separate file, often a separate directory or project. Rust usually keeps them in the same file as the code, at the bottom, inside a `#[cfg(test)]` module. The tests are part of the module, so they reach its private items directly:

```rust
fn add(a: i32, b: i32) -> i32 { a + b }

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_adds() {
        assert_eq!(add(2, 2), 4);
    }
}
```

`#[cfg(test)]` ensures the test code is compiled only during `cargo test`, never in your release binary. No runtime cost, no stripping needed.

You can leave them there, and plenty of projects do. If you would rather not mix tests into the source file, move the module to its own: declare `#[cfg(test)] mod tests;` and put the tests in a sibling `tests.rs` (or any file via `#[path = "..."]`). It is still a submodule, so it still reaches the private items and still compiles out of release builds.

2. Integration tests live in `tests/` next to `src/`, one file per test crate. They can only reach your code through a library target (`src/lib.rs`); a binary-only crate exposes nothing to `tests/`, which is why binaries keep `main.rs` thin and put the logic in a lib. They see only your public API, simulating how real users would call it:

```
tests/
└── integration.rs
```

Each file in `tests/` becomes its own test binary, with `cargo test` running them all.

3. Doc tests live inside `///` comments and are extracted from the documentation:

```rust
/// Adds two numbers.
///
/// # Examples
///
/// ```
/// assert_eq!(mycrate::add(2, 2), 4);
/// ```
pub fn add(a: i32, b: i32) -> i32 { a + b }
```

`cargo test` runs each example, ensuring the docs stay correct as the code evolves. Python's `doctest` and Go's `Example` functions do something similar (Python's version predates and inspired Rust's), but Rust wires it into the default `cargo test` run with no setup. It is one of the more under-appreciated features.

A few flags worth knowing:

- `cargo test name_substring` runs only tests whose names contain the substring.
- `cargo test -- --nocapture` shows `println!` output even for passing tests (cargo hides it by default to keep the output clean).
- `cargo test -- --test-threads=1` runs tests sequentially. By default the harness runs tests as threads in one process, so parallel tests share process-wide state (current directory, environment variables, global singletons); drop to a single thread when that shared state makes them flaky.
- `cargo test --release` runs tests with the release profile. Slower to compile, faster to run; useful for tests that are themselves performance-sensitive.

Alternative test runners exist. `nextest` is popular for being faster, presenting nicer output, and running each test in its own process rather than a shared-process thread, so process-wide state or even a crash in one test cannot corrupt another: `cargo nextest run`. One catch: it does not run doc tests, so you still need `cargo test --doc` alongside it.

Coming from JUnit or pytest, you will look for fixtures and parameterized tests. The built-in harness has neither: setup is a plain helper you call in each test, and cleanup rides on RAII, a guard value whose destructor runs when the test ends. The `rstest` crate adds both, where `#[case]` turns one function into many named test cases. Each case is an ordinary `#[test]`, so it runs in parallel and reports like the rest.

Comparison:

- Java, C#: testing means picking a framework (JUnit, xUnit/NUnit), each with its own conventions. Python and JS ship options in the box (Python's stdlib `unittest` and `doctest`, recent Node's built-in `node:test`), though many still reach for pytest or jest.
- Go: `testing` is a standard library package; `*_test.go` files run with `go test`. Same one-tool philosophy as Cargo.
- C, C++: no built-in testing. Pick from a long list of frameworks (Google Test, Catch2, doctest) or roll your own.
- Rust: `#[test]` and `cargo test`. No framework to choose, no convention to debate.

The takeaway: write `#[test] fn whatever() { assert_eq!(...) }`, run `cargo test`. Unit tests live in `#[cfg(test)]` modules, integration tests in `tests/`, doc tests in `///` examples. The test runner is built in.

🔇 No framework to argue over, just `#[test]`. If you came from a more opinionated ecosystem and you miss proving a colleague wrong, relax: you can still debate whether the tests belong in the same file or their own.
