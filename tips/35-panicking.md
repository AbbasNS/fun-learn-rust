🦀 Tip of the day 35: Panicking, Drop Everything and Run

If you come from Java, Python, or C#, exceptions are the normal way to signal something went wrong. Throw, catch, recover, continue. Rust deliberately does not work this way. Expected failures use `Result` (tip [16](16-error-handling.md)). `panic!` is for *bugs* and impossible states, the kind of error the program cannot meaningfully recover from.

When you call `panic!`, the current thread starts *unwinding*: it walks up the stack and drops every local on the way. Files close, locks release, allocations free. RAII still holds. Then, depending on the build configuration, the thread either dies cleanly or the entire process aborts.

You will rarely write `panic!("...")` yourself. Most panics in real code come from `unwrap()`, `expect()`, indexing out of bounds, or integer overflow in dev builds (release builds wrap silently by default).

A panic kills only the panicking thread, not the process:

```rust
use std::thread;

let h = thread::spawn(|| {
    panic!("oh no");
});
let result = h.join();      // Err(...) carrying the panic payload
println!("main thread still running");
```

If the panicking thread is `main`, the process exits. If it is a spawned thread, only that thread ends; the main thread sees `Err` from `join()`. This is also why `Mutex::lock()` returns a `Result`: a thread that panics while holding the lock leaves it *poisoned*, and the next acquirer inherits the error (tip [33](33-arc-mutex.md)).

You can catch a panic with `std::panic::catch_unwind`:

```rust
use std::panic;

let result = panic::catch_unwind(|| {
    panic!("boom");
});
assert!(result.is_err());
```

Useful at FFI boundaries (unwinding across the C/Rust boundary is undefined behavior) and in test runners that want to keep going after one test panics. Not a control-flow tool. The closure must be `UnwindSafe`, and `catch_unwind` is useless when the binary is built with abort-on-panic.

Which brings us to the build-time knob. How a panic actually behaves is partly set in `Cargo.toml`:

```toml
[profile.release]
panic = "abort"
```

`"unwind"` (the default) does what we just described: walk the stack, run every destructor, optionally catch. The per-thread containment from earlier is a consequence of unwinding. `"abort"` skips all of it: any panic, on any thread, terminates the entire process immediately. No Drop, no `catch_unwind`, no thread-level isolation.

The library angle: if you spawn a worker thread and want to recover from its panic (a job runner re-queuing a task, a server isolating one request, a thread pool surviving a worker crash), that recovery only works under `"unwind"`. Under `"abort"` the worker's panic terminates the whole process. Libraries cannot pick the profile; they can only document that they require unwind.

Why opt out? Smaller binary (no unwind tables), simpler runtime, and a "restart the process" recovery model that fits some domains. It is the only option on bare-metal embedded targets (e.g. `thumbv7em-none-eabihf` for Cortex-M microcontrollers, `riscv32imac-unknown-none-elf` for RISC-V) and historically on WebAssembly (`wasm32-unknown-unknown`). A common choice for CLI tools shipped to end users. Rare in long-running servers and libraries.

When should you panic versus return `Err`? Panic for *programmer* errors: an invariant you swore was true, an index you swore was valid. Return `Result` for *environment* errors: missing files, bad JSON, network failures. Rough rule: if the user could fix the situation without touching your code, it should be `Result`.

Comparison:

- Java, Python, C#: exceptions for everything. Catch blocks are normal control flow.
- Go: `panic`/`recover`. The idiom is the same as Rust's: do not use them for ordinary errors.
- C++: several paths. Exceptions are the only standard way to unwind, with destructors. `std::abort()` and `std::terminate()` end immediately, no destructors. `std::exit()` runs `atexit` handlers and destroys statics but skips local destructors. Codebases that ban exceptions (`-fno-exceptions`) use error codes or `std::expected`.

The takeaway: `panic!` is "this should not happen" for the current thread. It unwinds (or aborts) the thread, runs destructors on the way, and is meant for bugs, not for expected failures.

🔇 `panic!` does not panic. It cleans up before slamming the door. You do.
