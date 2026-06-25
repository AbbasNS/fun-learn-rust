🦀 Tip of the day 35 follow-up

Follow-up questions from the discussion on [Tip 35: Panicking, Drop Everything and Run](35-panicking.md).

## In unwind mode with `catch_unwind`, is `panic!` basically an exception, just without any data about the cause?

Half right. In unwind mode a panic does walk the stack and run destructors, and `catch_unwind` lets you intercept it at a boundary, so the mechanism rhymes with exceptions. But the "no data about the cause" part is wrong: a panic carries a payload.

When you call `panic!`, the payload is the message you passed:

```rust
panic!("file not found: {path}");        // payload is a String
std::panic::panic_any(MyError { code }); // payload is your own type
```

`panic_any` (stable since Rust 1.51) lets you panic with a value of any `'static + Any + Send` type, not just a string. That is how you attach structured data to a panic.

On the catching side, `catch_unwind` returns `std::thread::Result<R>`, which is `Result<R, Box<dyn Any + Send + 'static>>`. The `Err` holds the payload, type-erased. You recover the original type with `downcast_ref`:

```rust
use std::panic;

let result = panic::catch_unwind(|| {
    panic!("boom");
});

if let Err(payload) = result {
    if let Some(s) = payload.downcast_ref::<String>() {
        eprintln!("panicked with: {s}");
    } else if let Some(e) = payload.downcast_ref::<MyError>() {
        eprintln!("panicked with error code {}", e.code);
    }
}
```

One catch: the payload type for a plain `panic!` is not guaranteed. A formatted message like `panic!("file: {path}")` lands as a `String`, while a bare literal like `panic!("boom")` lands as a `&'static str`. The standard library documents this distinction as unspecified and free to change between versions, so do not lean on a specific type when downcasting a generic panic. If you want a payload you can reliably recover, use `panic_any` with your own type.

So yes, the payload exists, but treating it like an exception's `getCause()` is the wrong instinct. `catch_unwind` is a boundary tool: FFI edges (unwinding across the C/Rust boundary is undefined behavior), test runners that keep going after one test fails, and thread isolation. It is not a control-flow mechanism. The moment you reach for it to model expected failures, you want `Result` instead.

🔇 The payload is right there, type-erased and waiting. You just have to guess what it is before you are allowed to look at it.
