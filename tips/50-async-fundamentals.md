🦀 Tip of the day 50: async/await, or Why Your Future Just Sits There

You wrote your first `async fn`. You called it. Nothing happens.

```rust
async fn fetch_thing() -> u32 {
    println!("fetching...");
    42
}

fn main() {
    fetch_thing();   // looks silent, but the compiler is not happy
}
```

Welcome to Rust async. It compiles, but the compiler already warns you: `unused implementer of Future that must be used`, with the note `futures do nothing unless you .await or poll them`. Rust is telling you exactly what went wrong. Your function did not run. It returned a *future*: a value representing "the work I will do when somebody runs me." Nothing has happened yet. To run a future, two things have to be true: somebody has to `.await` it (or otherwise drive it), and there has to be a *runtime* willing to do the driving.

The laziness is total. Not even the code before the first `.await` runs until the future is polled: calling `fetch_thing()` never prints `fetching...`, you just get a future back.

`async fn` desugars roughly into a function returning `impl Future<Output = T>`. So the example is closer to:

```rust
fn fetch_thing() -> impl Future<Output = u32> {
    /* compiler-generated state machine */
}
```

A `Future` is a value that, when *polled*, either finishes and returns `Poll::Ready(value)`, or returns `Poll::Pending` because it is not ready yet. On `Poll::Pending` the future is not re-polled in a busy loop; it arranges to be woken when it can make progress (say, when a socket becomes readable), and only then does whatever is driving it poll again. The compiler turns `async fn` bodies into a state machine that knows how to resume from each `.await` point.

You drive a future to completion by `.await`-ing it inside another `async` context:

```rust
async fn main_logic() {
    let value = fetch_thing().await;   // now fetch_thing actually runs
    println!("got {}", value);
}
```

You can also build a future inline with an `async` block, no separate function needed:

```rust
let fut = async { fetch_thing().await + 1 };   // a future; nothing runs yet

let name = String::from("data");
let fut = async move { name.len() };           // async move takes ownership of `name`
```

An `async fn` and an `async` block are the two ways to produce a future, and both are inert until polled.

But calling `main_logic()` from a regular `fn main()` gets you nowhere: it just hands back another inert future. And you cannot `.await` it there either, because `.await` only works inside `async` (writing `main_logic().await` in a sync `fn` is a compile error). Even an `async` block is still inert until something polls it. You need a runtime to set the whole machine in motion, and the standard library does not provide one.

This is the most surprising thing about Rust async coming from other languages. Almost everywhere else, async work tends to start on its own once you create it. Rust chose the opposite: futures are lazy, the language gives you the syntax, and the ecosystem provides the runtime.

The trade-off the language is making:

- No runtime in `std` keeps the standard library small and lets multiple runtimes compete. The right runtime for a server (multi-threaded, work-stealing) is wrong for an embedded device (single-threaded, no allocator).
- Lazy futures mean you only pay for work you `.await`. A future nobody polls never runs, and one you stop polling stops making progress. Cheap cancellation falls out of this, which we return to when we cover cancellation.
- The cost is real friction: you need to install a runtime crate (almost always `tokio`) to do anything useful.

Comparison:

- JavaScript: Promises are eager. The moment a Promise is constructed, the work begins. Cancellation requires extra machinery (`AbortController`).
- Python: `asyncio` futures and tasks. Tasks created with `create_task` run immediately on the event loop; coroutines are lazy until awaited or scheduled.
- C#: the `Task` from an `async` method or `Task.Run` is eager, already running. `async`/`await` is built into the language and the .NET runtime schedules them.
- Go: no async/await. Goroutines are eagerly scheduled on a built-in runtime, with channels for coordination.
- Rust: futures are lazy and inert until polled. The runtime is chosen per project, by convention `tokio`.

The takeaway: `async fn` returns a `Future`, which does nothing until polled. `.await` polls it inside another async context, but the chain must end at a runtime that drives the polling. We cover runtimes next.

🔇 Rust promises you a `Future`. It does not promise you a present.
