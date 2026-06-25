🦀 Tip of the day 34: Send and Sync, the Marker Traits Behind Thread Safety

Tip [33](33-arc-mutex.md) said `Rc<T>` is single-threaded and `Arc<T>` is multi-threaded, and the compiler enforces the difference. This tip is on how.

Two traits in the standard library do the work: `Send` and `Sync`. They are *marker traits*, meaning they have no methods. A type either implements them or it does not, and the compiler checks the implementations against operations that cross thread boundaries.

The definitions are tight:

- `Send`: a value of this type can be safely transferred to another thread.
- `Sync`: a `&T` reference can be safely shared with another thread (equivalently, `&T` is `Send`).

Saying a type is `Send` asserts that handing ownership to another thread is safe: nothing inside relies on staying on the original thread, no thread-local handles, no non-atomic counters pointing at neighbors left behind. Saying a type is `Sync` asserts that two threads can observe the same value through `&T` at the same time without racing: either there is no interior mutability, or whatever mutation happens is properly synchronized.

The sharper rule for both: `Send` fails when moving leaves shared state accessible on the old thread and that access isn't synchronized; `Sync` fails when an operation through `&T` mutates state without synchronization.

Most types you write implement both automatically. `Send` and `Sync` are *auto traits*: the compiler implements them for any type whose fields are all `Send` and `Sync`. You inherit thread safety just by being made of thread-safe parts.

The interesting cases are when one or both don't hold. All four combinations exist:

- Both: `i32`, `String`, `Vec<T>`, `Arc<T>`, `Mutex<T>`, most user types.
- `Send` only: `Cell<T>`, `RefCell<T>`. Safe to move, not safe to share by reference.
- `Sync` only: `MutexGuard<'_, T>`. Safe to share by reference, not safe to send.
- Neither: `Rc<T>`, raw pointers (`*const T`, `*mut T`).

The classic example: `Rc<T>` is not `Send`. Moving an `Rc<T>` to another thread moves one handle, not the shared allocation. Other clones may still live on the original thread, and the heap-allocated refcount they all share is a non-atomic `usize`:

```rust
use std::rc::Rc;
use std::thread;

let a = Rc::new(42);
let b = Rc::clone(&a);    // refcount = 2, both handles point to the same allocation

// If Rc were Send, this would compile and the two threads would race:
thread::spawn(move || {
    drop(b);              // thread B decrements
});
drop(a);                  // thread A decrements, racing on the same non-atomic counter
```

The move itself is fine; the race comes after, when both threads independently drop or clone their handles. `Arc<T>` makes that counter atomic, so the same operations become safe. Same shape, different bookkeeping, different trait status.

`Rc<T>` is also not `Sync`. `Rc::clone` takes `&self`, so handing `&Rc<T>` to another thread would let both threads call `.clone()` and bump the same refcount concurrently. Same race, different entry point.

`RefCell<T>` is the opposite shape: `Send` but not `Sync`. Moving the whole `RefCell<T>` to another thread is fine because the borrow tracker moves with it and only the new thread can touch it. But `&RefCell<T>` cannot be shared across threads: `borrow_mut()` takes `&self`, so two threads could call it at once, race on the non-atomic borrow tracker, and both end up with `&mut T` to the same data.

`Mutex<T>` is `Sync`, because the lock serializes concurrent access.

A small surprise: `MutexGuard<T>`, the value returned by `Mutex::lock()`, is not `Send`. The reason is that the guard releases the lock when dropped, and the lock implementation requires that release to happen on the same thread that took the lock. Sending the guard to another thread would unlock from the wrong thread, which is undefined behavior on most platforms. The compiler refuses, and you typically never notice because there is no good reason to send a guard.

You will almost never write `impl Send for MyType` or `impl Sync for MyType` yourself. Both traits are auto-implemented when applicable, and explicitly implementing them is `unsafe` because you are asserting a property the compiler cannot verify. The places it does come up are when you wrap raw pointers (which are not `Send`/`Sync` by default) and need to assert that your wrapper is safe.

The takeaway: `Send` and `Sync` are marker traits the compiler tracks to decide which types are safe to move or share across threads. Most types are automatic. The cases that surprise you (`Rc` not `Send`, `MutexGuard` not `Send`, `RefCell` not `Sync`) are exactly the cases where data races would lurk in other languages.

🔇 Send does not send. Sync does not sync. Otherwise, perfectly named.
