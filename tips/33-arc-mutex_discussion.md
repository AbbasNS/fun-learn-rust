🦀 Tip of the day 33 follow-up

Follow-up questions from the discussion on [Tip 33: Arc<T> and Mutex<T>, the Thread-Safe Versions](33-arc-mutex.md).

## If a Mutex must wrap the data it protects, what do you do when two separate pieces of data need to be protected together?

You package them into one struct and wrap that struct in a single `Mutex`:

```rust
struct Account {
    balance: i64,
    history: Vec<Transaction>,
}

let account = Arc::new(Mutex::new(Account { balance: 0, history: vec![] }));
```

One lock, one critical section, and both fields move together. A thread that holds the guard sees `balance` and `history` in a consistent state, and no other thread can observe a half-finished update.

This is really a design nudge. If two pieces of data must stay consistent with each other, they usually belong in the same struct anyway, and the `Mutex` just makes that grouping explicit.

If the data is genuinely independent, you are free to use separate `Mutex` values. Rust will not stop you. But now you own the classic problem of lock ordering: the moment one thread can hold lock A while waiting for lock B, and another holds B while waiting for A, you have a deadlock. Which brings us to the philosophers.

## Does Rust prevent deadlocks the way it prevents data races? How would you write the dining philosophers in Rust?

No. Rust's type system prevents data races, not deadlocks. Those are different problems.

A data race is two threads touching the same memory at the same time with at least one write and no synchronization. That is what `Arc<Mutex<T>>` and the borrow checker rule out: you cannot reach the data without going through `lock()`, so by the time you hold a `&mut T`, you provably hold the lock.

A deadlock is two or more threads each holding one resource and waiting forever for another. The borrow checker has nothing to say about two threads that each grab one fork and politely wait for the other. Both threads are perfectly synchronized. They are just stuck.

So the dining philosophers in Rust look the same as in C++ or Java, and they need the same fixes:

- Global lock ordering: every philosopher always takes the lower-numbered fork first.
- `try_lock` with backoff: if you cannot get the second fork, put the first one back and retry.
- A single coordinator (a waiter) that hands out permission to eat.
- Or just one `Mutex` over the whole table, trading concurrency for simplicity.

A sketch of the lock-ordering fix:

```rust
use std::sync::{Arc, Mutex};
use std::thread;

let forks: Vec<_> = (0..5).map(|_| Arc::new(Mutex::new(()))).collect();

let mut handles = vec![];
for i in 0..5 {
    let left = Arc::clone(&forks[i]);
    let right = Arc::clone(&forks[(i + 1) % 5]);

    // Always lock the lower-indexed fork first to avoid a cycle.
    let (first, second) = if i < (i + 1) % 5 { (left, right) } else { (right, left) };

    handles.push(thread::spawn(move || {
        let _a = first.lock().unwrap();
        let _b = second.lock().unwrap();
        // eat
    }));
}

for h in handles { h.join().unwrap(); }
```

The convention of requesting resources in a fixed order is the same one Dijkstra proposed when he first posed the problem in 1965. Tony Hoare gave it the philosophers-and-forks framing in 1978, and the deadlock it illustrates has outlived every language since.

So Dijkstra and Hoare would still need to seat their guests carefully. Rust only guarantees that once seated, nobody picks up a fork that someone else is already eating with.
