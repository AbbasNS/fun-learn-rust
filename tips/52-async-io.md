🦀 Tip of the day 52: Async I/O, or Why You Suddenly Need `tokio::fs`

Tip [43](43-stdlib.md) called `std::fs`, `std::net`, and `std::thread` the parts of the standard library that need the OS. They are all *blocking*: when you call `std::fs::read_to_string("foo")`, the calling thread parks until the read completes. That is fine on a regular thread. It is a disaster inside an async task.

The reason is how runtimes work. A tokio worker thread runs many tasks, switching between them at `.await` points. A blocking call contains no `.await`, so the worker freezes and every other task queued on it stalls too. Your "hundreds of thousands of tasks" runtime quietly becomes "one task per worker thread, the rest are waiting."

You can measure it. One worker thread, two tasks, one of them blocking:

```rust
use std::time::{Duration, Instant};

#[tokio::main(flavor = "multi_thread", worker_threads = 1)]
async fn main() {
    let t0 = Instant::now();
    let a = tokio::spawn(async { std::thread::sleep(Duration::from_millis(500)) });
    let b = tokio::spawn(async move {
        tokio::time::sleep(Duration::from_millis(50)).await;
        println!("b woke after {:?}", t0.elapsed());
    });
    let _ = tokio::join!(a, b);
}
```

Task `b` asked for 50 ms and woke after about 555 ms: it could not be polled until `a` handed the thread back. Change `a` to `tokio::time::sleep` and `b` wakes after about 51 ms, on time.

The fix is to use async-aware replacements for the blocking parts of `std`:

- `tokio::fs` for file I/O.
- `tokio::net` for TCP, UDP, and Unix sockets.
- `tokio::io` for the async `AsyncRead` and `AsyncWrite` traits.
- `tokio::time` for sleeping, timers, and timeouts.
- `tokio::process` for subprocesses.

The shape mirrors `std` closely, with one wrinkle: the read and write methods live on extension traits, so `stream.read(&mut buf).await` compiles only with `use tokio::io::AsyncReadExt;` in scope. The compiler names the missing trait in the error, which is how most people meet `AsyncReadExt`.

`tokio::fs` deserves a footnote. Most operating systems have no async file API, so tokio does not either: every `tokio::fs` call runs the ordinary blocking `std` call on a separate thread pool and awaits the result. That keeps your workers free, but it is not free itself, so prefer one large call like `fs::read_to_string` over many small reads through `File`. (Linux `io_uring` support is landing in tokio, but it is experimental and behind unstable flags.)

For blocking work with no async equivalent, use that same pool directly:

```rust
let result = tokio::task::spawn_blocking(|| expensive_synchronous_work()).await?;
```

Blocking threads start on demand up to 512 by default, and later calls queue. That limit is generous because the pool is meant for blocking I/O, not for CPU-bound parallelism; for sustained computation, cap the concurrency yourself or use something like `rayon`. One catch: a `spawn_blocking` closure cannot be cancelled once it starts, and runtime shutdown waits for it.

Now the trap. Your editor will suggest `std::sync::Mutex` long before `tokio::sync::Mutex`. Both are `Mutex<T>`, and they behave differently here:

- `std::sync::Mutex::lock()` blocks the *thread* until the lock is free.
- `tokio::sync::Mutex::lock()` is async: on contention it yields the *task*, freeing the worker.

Rust catches part of this for you. A `std::sync::MutexGuard` is not `Send` (tip [34](34-send-sync.md)), so a future holding one across an `.await` cannot go to `tokio::spawn`:

```
error: future cannot be sent between threads safely
note: future is not `Send` as this value is used across an await
```

That covers spawned tasks. It does not cover a guard held in code that is never spawned, like the body of `#[tokio::main]` itself: that compiles and stalls at runtime.

The counter-intuitive part is that tokio's own docs recommend the std `Mutex` for async code. The only thing the async mutex adds is the ability to hold the lock across an `.await`, and paying for that on every lock is a poor trade when the critical section is three lines of data mutation. Use `tokio::sync::Mutex` when you genuinely must hold the lock across an `.await`, guarding a database connection for instance, and std's otherwise.

The same split applies to `RwLock` and to channels (`std::sync::mpsc` versus `tokio::sync::mpsc`). Some tokio primitives have no std counterpart at all, like `Semaphore` and `Notify`.

Comparison:

- Node.js: async I/O is the default. The sync twins (`fs.readFileSync`) exist but are treated as an anti-pattern outside startup code, and `worker_threads` is the escape hatch for CPU work.
- Python: `asyncio` has exactly the same trap. `open` or `requests` inside async code blocks the event loop, and `asyncio.to_thread` is the `spawn_blocking` equivalent.
- Go: blocking I/O is the only API. The runtime parks the goroutine and shuffles work between OS threads invisibly, so there is no split to get wrong.
- Java: `java.io` blocks, `java.nio` does not, and picking was your problem. Virtual threads (Java 21) make ordinary blocking calls cheap again, and Java 24 removed the last big caveat, blocking inside `synchronized`.
- Rust: std blocks, tokio mirrors std asynchronously, and mixing the two compiles fine most of the time.

The takeaway: inside async code use `tokio::fs`, `tokio::net`, and `tokio::time` instead of their `std` counterparts, `spawn_blocking` for blocking work with no async version, and `std::sync::Mutex` unless you need to hold the lock across an `.await`.

🔇 Go: "All I/O is async." Node: "All I/O is async." Rust: "Most I/O is async, except the std version, which blocks, and the autocomplete offers that one first."
