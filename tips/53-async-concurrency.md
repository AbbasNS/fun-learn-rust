🦀 Tip of the day 53: Spawning, Joining, Selecting, and Channels

If you have used `Promise.all` in JS, `asyncio.gather` in Python, or `Task.WhenAll` in C#, you already know the shapes in this tip. Tokio has all of them, but it puts a decision in front of you first: does this work become its own *task*, or does it stay on the task you are already running?

Spawning makes it a task, an independently scheduled unit of work that the runtime polls, like a thread but far cheaper (tip [51](51-runtimes-tokio.md)):

```rust
let handle = tokio::spawn(async { do_work().await; 42 });
// ... the caller keeps going while the task runs ...
let value = handle.await.unwrap();   // the task's 42, unwrapping the JoinError
```

`tokio::spawn` returns a `JoinHandle<T>`, and awaiting it gives you the task's return value wrapped in `Result`. The `Result` is there because a task can panic or be aborted, and a panicking task does not take the program down with it: the panic is caught at the task boundary and handed back as an `Err`, with `is_panic()` distinguishing the two cases. You still see the panic message on stderr, so it is not silent. Tasks are isolated the way threads are, and for the same reason.

The price of being a task is `Send`. The multi-threaded runtime can move a task between worker threads at any `.await`, so its future has to implement `Send`, the trait from tip [34](34-send-sync.md). Capture an `Rc` or a `RefCell` and the compiler refuses to spawn it.

Past two or three handles, awaiting them one at a time gets awkward. `JoinSet` owns a group of tasks and hands you results in completion order rather than spawn order. Dropping the set aborts whatever is still running in it, which makes it a tidy way to scope a group of tasks to a block:

```rust
let mut set = tokio::task::JoinSet::new();
for i in 0..3 {
    set.spawn(async move { fetch(i).await });
}
while let Some(res) = set.join_next().await {
    println!("finished: {}", res.unwrap());
}
```

Now the other side of the decision. `join!` waits for several futures without spawning anything:

```rust
let (a, b) = tokio::join!(fetch_a(), fetch_b());
```

These futures are polled by the *current* task, and that has two consequences. There is no `Send` requirement, so you can `join!` futures holding an `Rc`. And there is no parallelism, which is where the two words in play here come apart: *concurrency* is several futures taking turns to make progress, *parallelism* is them running in the same instant. A task is polled by one thread at a time, so `join!` buys you the first and never the second. Two CPU-bound futures of about 100 ms each finish in 217 ms under `join!`, and in 98 ms as two spawned tasks on a multi-core machine. `join!` overlaps *waiting*, not *computing*.

`try_join!` is the variant for futures returning `Result`, and it short-circuits: the first `Err` comes back immediately and the futures still in flight are dropped where they stand.

`select!` waits for whichever finishes first:

```rust
tokio::select! {
    a = fetch_a() => println!("a finished first: {:?}", a),
    b = fetch_b() => println!("b finished first: {:?}", b),
}
```

When several branches are ready in the same poll, `select!` picks among them at random, so a consistently fast branch cannot starve the others. The losing futures are *dropped*, which in Rust async is how you cancel work. We will return to this in a later tip.

Both macros take a fixed list of futures, so neither accepts a `Vec`. For a dynamic number, reach for a `JoinSet` if the work can be tasks, or `futures::future::join_all` if it cannot.

For tasks that need to coordinate, channels are the standard tool. Their `std` counterparts block the thread, as tip [52](52-async-io.md) covered, so async code wants the tokio versions:

- `tokio::sync::mpsc`: multiple-producer, single-consumer queue. The workhorse.
- `tokio::sync::oneshot`: a single value sent once. Used for "task A computes a result, task B awaits it."
- `tokio::sync::broadcast`: multiple-producer, multiple-consumer. Every receiver gets every message.
- `tokio::sync::watch`: a single value that all receivers can read; senders overwrite.

```rust
let (tx, mut rx) = tokio::sync::mpsc::channel(32);

tokio::spawn(async move {
    for i in 0..5 {
        tx.send(i).await.unwrap();
    }
});

while let Some(value) = rx.recv().await {
    println!("got {}", value);
}
```

`channel(32)` is bounded: senders await once 32 messages are buffered, which gives you back-pressure for free. The loop ends on its own when the last sender is dropped. Prefer bounded channels; an unbounded channel that fills faster than it drains is a memory leak in slow motion.

Comparison:

- Go: channels are built into the language and `select` is a keyword. Tokio reaches the same shapes through library APIs.
- C#: `Channel<T>` in `System.Threading.Channels`, with `Task.WhenAll` and `Task.WhenAny` covering join and select.
- Python: `asyncio.Queue`, `asyncio.gather`, `asyncio.wait`. Same shapes, different names, and `TaskGroup` (3.11+) is the closest thing to a `JoinSet`.
- Rust: the split between "spawn a task" and "poll it right here" is explicit, and it decides both whether you need `Send` and whether your concurrency can become parallelism.

The takeaway: `tokio::spawn` turns work into an independent task that needs `Send` and can run in parallel, while `join!` and `select!` keep the work on the current task, concurrent but never parallel and with no `Send` requirement. `JoinSet` manages a group of tasks, and channels (`mpsc`, `oneshot`, `broadcast`, `watch`) are how they talk to each other.

🔇 Go: `select` is a keyword. Rust: `select!` is a macro because the language does not believe in keywords for things it can build with macros.
