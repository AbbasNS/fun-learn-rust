🦀 Tip of the day 51: Runtimes and Tokio

Tip [50](50-async-fundamentals.md) left you with a future that does not run. To drive futures to completion, you need a runtime. The standard library does not include one.

A *runtime* is a library that:

- Schedules futures (tasks) onto threads.
- Polls them when they have work to do, and parks them when they are waiting on I/O or timers.
- Drives I/O through a component called the *reactor* (or I/O driver): it integrates with the OS event API (epoll on Linux, kqueue on BSD/macOS, IOCP on Windows) and wakes tasks when their sockets are ready.
- Provides async-aware versions of operations that would otherwise block: timers, locks, channels.

The standard library deliberately stops at `async`/`.await` syntax and the `Future` trait. Everything else is on `crates.io`. Several runtimes exist, but the de facto choice for almost any Rust project doing async I/O is `tokio`.

First, add tokio to your project. Unlike most crates, tokio ships with no features enabled by default, so a bare `tokio = "1"` gives you almost nothing: `#[tokio::main]`, timers, and `spawn` are all gated behind feature flags and will not compile. You get errors saying the item cannot be found in `tokio`, each with a note that it is gated behind a feature. In `Cargo.toml`:

```toml
[dependencies]
tokio = { version = "1", features = ["full"] }
```

`"full"` turns everything on, which is the right default while you are learning. Later you can trim to the features you use to cut compile time. For the programs below, `["rt-multi-thread", "macros", "time"]` is enough.

A minimal tokio program:

```rust
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() {
    println!("starting");
    sleep(Duration::from_secs(1)).await;
    println!("done");
}
```

`#[tokio::main]` is an attribute macro that rewrites `async fn main` into a regular `fn main` that sets up a tokio runtime, runs the async body to completion, and shuts the runtime down. Without it, you would write:

```rust
fn main() {
    tokio::runtime::Runtime::new().unwrap().block_on(async {
        // ... the async body ...
    });
}
```

`block_on` is the bridge between sync and async: it blocks the calling thread and drives the future to completion on that thread, parking only while the future is waiting. `Runtime::new()` builds the same multi-threaded runtime that `#[tokio::main]` gives you by default, which is the flavor described next. In this manual form the runtime is an ordinary value that stays alive only as long as you hold it: while it lives it keeps its worker threads and drives spawned tasks, and if you drop it those threads shut down, so any task still running stops. `#[tokio::main]` sidesteps this by keeping the runtime alive for the whole `block_on`. One rule goes with the bridge: `block_on` is for the outermost sync entry point. Calling it from inside async code panics with "Cannot start a runtime from within a runtime", because the calling thread is already busy driving tasks. Once you are inside `async`, you use `.await`.

Tokio offers two runtime flavors:

- *Multi-threaded* (the default): a pool of worker threads with work-stealing, one per CPU core by default. Override the count with `#[tokio::main(worker_threads = 4)]` or the `Builder::new_multi_thread().worker_threads(n)` API. Tasks can move between threads, so a future you `spawn` onto the runtime must be `Send`. Best for I/O servers and CPU-throughput work.
- *Current-thread*: a single thread runs the runtime. Tasks stay on it. Best for scripts, GUIs, and code that uses non-`Send` types. Activated with `#[tokio::main(flavor = "current_thread")]`. Note that `tokio::spawn` still requires `Send` even here; to spawn a non-`Send` task (one capturing an `Rc`, say) you use `tokio::task::spawn_local` inside a `LocalSet`.

A *task* is what you spawn onto the runtime, similar to a thread but far cheaper. A task is the compiler-generated state machine from tip [50](50-async-fundamentals.md), holding only the data live across its `.await` points, often bytes or a few kilobytes. An OS thread instead reserves a dedicated stack, commonly multiple megabytes, whether or not it uses it. That is why you can have hundreds of thousands of tasks at once while OS threads max out in the tens of thousands: the ceiling is mostly stack memory. The runtime then multiplexes all those tasks onto a small pool of threads.

```rust
use tokio::task;

#[tokio::main]
async fn main() {
    let handle = task::spawn(async {
        println!("running on a task");
        7
    });
    let value = handle.await.unwrap();   // join the task, get its result
    println!("{}", value);
}
```

Because tasks are so cheap, spawning a hundred thousand of them is routine, something you would never attempt with OS threads:

```rust
#[tokio::main]
async fn main() {
    let handles: Vec<_> = (0u64..100_000)
        .map(|i| tokio::spawn(async move { i * 2 }))
        .collect();
    let mut sum = 0u64;
    for h in handles {
        sum += h.await.unwrap();
    }
    println!("sum = {}", sum);
}
```

Tokio schedules tasks cooperatively, not preemptively: a task yields only at an `.await`. A tight async loop that never awaits can monopolize its worker thread, even without doing anything blocking. To keep tasks fair, tokio gives each one a budget: its I/O and channel operations count down that budget and yield once it runs out, even when data is ready, so an always-ready task still hands control back instead of starving its neighbors.

Other runtimes exist:

- `async-std`: an older runtime that mirrored the `std` API surface in async form. It was discontinued in 2025 (RUSTSEC-2025-0052), and its maintainers now point users to `smol`. Do not start new projects on it.
- `smol`: small, modular, and actively maintained. It is the general-purpose runtime the async-std maintainers now point users to.
- `embassy`: the embedded async runtime, for microcontrollers without `std`.
- `monoio`/`glommio`/`compio`: thread-per-core runtimes built on `io_uring`. They can outscale tokio on high-throughput Linux servers, but they are niche, mostly Linux-only, and several are still pre-1.0, so none is a general-purpose default.

Mixing runtimes in one program is hard. Most crates assume tokio. If you pick a different runtime, expect more friction with the ecosystem.

Comparison:

- Node.js: ships its own event loop (libuv-based), baked into the runtime. No separate async crate to choose.
- Python: `asyncio` is in the standard library. `uvloop` is a faster drop-in. The default works for almost everything.
- C#: the .NET runtime schedules tasks. One runtime, baked in.
- Go: built-in runtime, scheduled by the Go runtime onto OS threads. Goroutines are the only "task" abstraction.
- Java: the JVM is the runtime, baked in. Since Java 21, virtual threads (Project Loom) multiplex many lightweight threads onto a few OS threads, like tokio tasks or goroutines, but without `async`/`.await` coloring.
- Rust: no runtime in std. Tokio is the de facto choice, and the rest of the ecosystem is built around it. The decoupling is a feature when you need a different runtime (embedded, kernels) and a tax when you do not.

The takeaway: a runtime polls futures, drives I/O, and schedules tasks. Rust does not ship one. Use `tokio` with `#[tokio::main]` for almost everything. Other runtimes exist for specific niches (embedded, minimal binaries).

🔇 Rust has many async runtimes, the way there are many messaging apps: you end up on whichever one the people you need already use.
