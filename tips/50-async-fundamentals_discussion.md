🦀 Tip of the day 50 follow-up

Follow-up questions from the discussion on [Tip 50: async/await, or Why Your Future Just Sits There](50-async-fundamentals.md).

## Can you write an `async` block in a sync function?

Yes. An `async {}` block is an expression that evaluates to a future, and building a value never requires you to be in an async context. So you can write one inside an ordinary sync `fn`:

```rust
async fn fetch() -> u32 { 42 }

fn main() {                                 // ordinary sync fn
    let fut = async { fetch().await + 1 };  // async block built right here
    // fut is a future; nothing has run yet
}
```

The part that trips people up is where `.await` is allowed. `.await` only works inside an async context, but the body of the block *is* an async context, so the `fetch().await` above is fine even though `main` is sync. What you cannot do is `.await` the block's result back out in the sync function:

```rust
let fut = async { fetch().await + 1 };  // OK: .await is inside the block
let x = fut.await;                      // error[E0728]: `await` only allowed inside async
```

So the rule is narrower than "no async in sync functions." You can build futures anywhere; you can only `.await` them from inside `async`. Building a future in sync code and then handing it to a runtime is the normal thing to do, that is exactly what `block_on` receives.

This also gives you a common pattern: a sync function that returns a future by ending in an `async` block.

```rust
fn load(id: u32) -> impl Future<Output = u32> {  // sync fn, no async keyword
    async move { fetch().await + id }            // returns a future
}
```

`load` runs no async code itself. It just constructs the future and hands it back for someone else to drive.

## When we talk about polling a future, is there a simple function call that does just that?

Not in the standard library. The low-level primitive is the [`Future::poll`](https://doc.rust-lang.org/std/future/trait.Future.html#tymethod.poll) method, but you rarely call it by hand: it takes a `Pin<&mut Self>` and a `&mut Context`, and the `Context` has to carry a `Waker` so the future can signal when it is ready to make progress again. One call is not enough either, a future that returns `Poll::Pending` has to be polled again after each wake. That bookkeeping loop is what an executor is.

There is no `std::future::block_on`. The standard library gives you the `Future` trait plus `Poll`, `Context`, and `Waker`, and stops there.

In day-to-day code the two simple calls are:

- `.await`, inside an async context. It desugars into the poll-and-wait loop for you.
- a runtime's `block_on(...)`, to drive a future to completion from sync code. It does not come from std, it comes from a crate:

```rust
let v = pollster::block_on(fetch());                        // tiny, executor only
let v = futures::executor::block_on(fetch());               // from the futures crate
let v = tokio::runtime::Runtime::new().unwrap().block_on(fetch()); // full runtime
```

[`#[tokio::main]`](https://docs.rs/tokio/latest/tokio/attr.main.html) is just sugar for that last one. All of them do the same job: poll the future in a loop, parking the thread between wakeups, until it returns `Poll::Ready`.

If you want to see how little it takes, a complete `block_on` for futures that never truly block is about fifteen lines built on [`std::task::Wake`](https://doc.rust-lang.org/std/task/trait.Wake.html) (stable since 1.51). The hard part of a real runtime is not the polling loop, it is the reactor that knows when to call `wake()` for actual I/O.
