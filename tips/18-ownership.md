🦀 Tip of the day 18: Ownership, the Rule That Replaces the Garbage Collector

If you are coming from Java, Python, C#, JS, or Go, you barely think about memory. You create something, use it, and a garbage collector frees it later. From C, every `malloc` needs a `free`. Forget once and you leak. Do it twice and you crash.

Rust takes a third path. There is no garbage collector, and you almost never write `free`. The compiler tracks who is responsible for each value and runs cleanup automatically when that party goes away. The system is called *ownership*, the most distinctive feature in Rust. We will spread it across five tips. This first one is the basic rule and the precise definition of *scope* it depends on.

Two definitions first.

A *value* is whatever a variable holds. It might live on the stack (an integer), partly on the stack and partly on the heap (a `Vec`, where the pointer, length, and capacity sit on the stack while the buffer of elements sits on the heap), or in static memory (constants baked into the binary). Ownership does not care where the bytes physically sit. It cares about who is responsible for cleaning them up.

What "cleanup" actually does depends on the *type*, not on where the value lives. An `i32` has no destructor, so dropping it is a no-op. A `Vec` has a destructor that frees its heap buffer. A `File` has one that closes the underlying descriptor. Ownership runs the same rule on all of them: drop at end of scope, and the type decides what work that drop actually does.

A *scope* is the region of code in which a variable name is valid. The simplest scope is a block, `{ ... }`. A variable declared inside a block is invisible outside it.

```rust
fn main() {
    let v = vec![1, 2, 3];           // v comes into scope here
    println!("length: {}", v.len());
}                                     // v goes out of scope here, value is dropped
```

That closing brace is a real moment. When control reaches it, Rust runs the cleanup code for `v` and frees the heap buffer. The cleanup point is determined statically by where the brace is, not by a collector that wakes up later. No `free`, no `delete`, no GC pause.

Now the rule, in its simplest form: every value has exactly one owner, and when the owner goes out of scope, the value is dropped.

The "owner" is the variable. "Goes out of scope" means control crosses the closing brace of its declaring block. "Dropped" means the cleanup code for that type runs. The mechanism behind this is a trait called `Drop`. Library types like `Vec` already implement `Drop` for you; you only write your own when a type has custom cleanup, like releasing a non-Rust resource.

This single rule prevents three classes of bug at once: leaks (cleanup always happens), double-frees (it happens exactly once), and use-after-free (the value is gone after drop). [Microsoft reported in 2019](https://www.microsoft.com/en-us/msrc/blog/2019/07/a-proactive-approach-to-more-secure-code) that roughly 70% of the CVEs they assign each year are memory safety bugs, and the figure has held for over a decade. Chrome, Firefox, and the Linux kernel tell the same story. GC languages avoid these bugs by taking deallocation away from the programmer, and the convenience is real. The costs are also real, and not just timing: the collector spends CPU on bookkeeping, the heap typically holds well more memory than the live set so the collector has room to work, write barriers slow pointer assignments, and it only manages memory (files, locks, and sockets still need explicit cleanup). Pause times vary widely. Go's collector is engineered for sub-millisecond pauses by default; Java's default G1GC trades pause time for throughput and runs in the tens to hundreds of milliseconds, while opt-in collectors bring it down further: ZGC reaches sub-millisecond pauses regardless of heap size, and Shenandoah typically stays in the low single-digit milliseconds. Short is not zero in any of them. Rust avoids the bugs at compile time and pays nothing at runtime for any of this, asking you to think about ownership upfront in exchange.

C++ programmers will recognize the cleanup-at-scope-end behavior as RAII, the pattern smart pointers like `unique_ptr` use. Rust takes the same idea and applies it to every value as a language rule, not as a library convention you have to remember to follow.

One scope subtlety the compiler treats carefully: values not bound to a variable, called *temporaries*, are dropped at the end of the *statement* that produced them, not the end of the block.

```rust
fn main() {
    let len = vec![1, 2, 3].len();  // the temporary Vec is dropped at the ';'
    println!("{}", len);            // Vec is gone, len lives on
}
```

The `vec![1, 2, 3]` here exists just long enough for `.len()` to read it, then is dropped at the semicolon. The integer `len` lives until the end of `main`. You do not usually have to think about this, but it is the first hint that the compiler's view of scope is more refined than the lexical block. More on that later this week.

Brief comparison:

- Java, Python, C#, JS: garbage collection. Reliable for memory, with CPU and memory overhead. Pause times depend heavily on the collector chosen. Non-memory resources (files, locks, sockets) need explicit cleanup.
- C: manual `malloc`/`free`. Deterministic, easy to forget.
- C++11 smart pointers (`unique_ptr`, `shared_ptr`): RAII as a library convention. `unique_ptr` models single ownership, but raw pointers, manual `new`/`delete`, and aliasing references still compile alongside, and use-after-move is uncaught.
- Go: tracing GC tuned for low latency, with typical pauses well under a millisecond, plus `defer` for non-memory cleanup. No ownership tracking, no compile-time aliasing rules. Data races are possible at runtime; the race detector catches some on tested paths.
- Rust: ownership as a language rule, enforced at compile time, with zero runtime cost.

The takeaway: every value has exactly one owner, and when the owner goes out of scope the value is dropped. One rule replaces both garbage collection and manual `free`, with cleanup at compile-time-known points.

🔇 Other languages let you forget about memory, performance, and eventually what a fast program even feels like. C++ lets you remember and shoot yourself in the foot, free of charge, and sometimes twice. Rust insists you remember, then handles it for you anyway.
