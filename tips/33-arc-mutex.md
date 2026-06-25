🦀 Tip of the day 33: Arc<T> and Mutex<T>, the Thread-Safe Versions

Tip [29](29-rc.md) introduced `Rc<T>` and tip [30](30-refcell.md) introduced `RefCell<T>`, both for single-threaded code. The compiler refuses to share either across threads, because the bookkeeping inside them (refcount for `Rc`, borrow tracker for `RefCell`) would race.

For multi-threaded shared ownership and mutation, the standard library provides `Arc<T>` and `Mutex<T>`, the atomic counterparts.

First, threading basics. `std::thread::spawn` takes a closure and runs it on a new thread:

```rust
use std::thread;

let handle = thread::spawn(move || {
    println!("hello from a thread");
});
handle.join().unwrap();   // wait for the thread to finish
```

The `move` keyword on the closure (tip [31](31-closures.md)) forces it to take ownership of any variables it captures from the enclosing scope. Without `move`, the closure would borrow them, and the borrow checker would refuse because the thread might outlive those borrows.

Now, sharing data with the spawned thread. `Arc<T>` is the atomic version of `Rc<T>`:

```rust
use std::sync::Arc;
use std::thread;

let shared = Arc::new(vec![1, 2, 3]);

let copy = Arc::clone(&shared);
let handle = thread::spawn(move || {
    println!("thread sees: {:?}", copy);
});
handle.join().unwrap();
```

`Arc::clone` does the same thing as `Rc::clone` (bumps a refcount, hands you another pointer) except the count is updated atomically, which is what makes it thread-safe.

That gets you shared *reads*. For shared *writes* across threads, wrap the data in `Mutex<T>`. A `Mutex` is a lock; calling `.lock()` gives you exclusive access until the returned guard is dropped.

```rust
use std::sync::{Arc, Mutex};
use std::thread;

let counter = Arc::new(Mutex::new(0));
let mut handles = vec![];

for _ in 0..4 {
    let c = Arc::clone(&counter);
    handles.push(thread::spawn(move || {
        let mut num = c.lock().unwrap();
        *num += 1;
    }));
}

for h in handles { h.join().unwrap(); }

println!("final: {}", counter.lock().unwrap());  // 4
```

`Arc<Mutex<T>>` is the standard pattern for shared mutable state across threads. The `Arc` lets every thread own a reference to the lock; the `Mutex` ensures only one thread is inside the critical section at a time.

When does the lock release? When the `MutexGuard` returned by `.lock()` is dropped. In the loop above that is the closing `}` of the closure body, right after `*num += 1`. There is no `unlock` to call and nothing to forget. To release earlier, scope the guard with a `{ }` block or call `drop(num)` explicitly:

```rust
{
    let mut num = c.lock().unwrap();
    *num += 1;
}  // lock released here, other threads can take it now
do_expensive_work_without_the_lock();
```

Same RAII pattern as C++'s `std::lock_guard`, and the opposite of C-style `lock()`/`unlock()` pairs where forgetting the unlock is a classic bug.

A few honest costs:

- `Arc` clones do an atomic increment. Atomics are slower than non-atomic operations but cheap on a per-operation basis.
- `Mutex::lock()` blocks if another thread holds the lock. Lock contention is real and can dominate performance.
- `lock()` returns `Result<MutexGuard, _>` because the lock can be "poisoned" if a thread panicked while holding it. `.unwrap()` is fine for most code.

Comparison:

- Java: `synchronized` blocks and methods, plus `java.util.concurrent.locks.ReentrantLock`. Same model, no compile-time check that you actually held the lock when accessing the data.
- Go: channels are the preferred primitive, but `sync.Mutex` exists. Either way, no compile-time guarantee that shared data is locked before access.
- C++: `std::mutex` plus `std::shared_ptr<T>` for shared ownership. Nothing forces you to lock before access, and the resulting data race is undefined behavior.
- Rust: the type system enforces lock-before-access. You cannot get a `&mut T` to data inside a `Mutex` without going through `lock()`, which guarantees you hold the lock.

The takeaway: `Arc<T>` is the thread-safe `Rc`, `Mutex<T>` is thread-safe interior mutability, and `Arc<Mutex<T>>` is the standard pattern for shared mutable state across threads. The atomic bookkeeping is real cost; pay it only when threads are involved.

🔇 Data races, deadlocks, poisoned locks. The compiler caught one. The other two are character-building.
