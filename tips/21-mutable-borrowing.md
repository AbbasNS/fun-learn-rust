🦀 Tip of the day 21: Mutable Borrowing and the XOR Rule

Shared references (`&T`, tip [20](20-borrowing.md)) are read-only. To modify a value through a reference, you need a *mutable* reference, written `&mut T`. That comes with the strictest rule in the language.

Here is mutable borrowing:

```rust
fn append_zero(v: &mut Vec<i32>) {
    v.push(0);
}

let mut a = vec![1, 2, 3];
append_zero(&mut a);
println!("{:?}", a);   // [1, 2, 3, 0]
```

Three things are required, all visible. The variable `a` is `mut`. The call site uses `&mut a`. The function signature accepts `&mut Vec<i32>`. Rust never lets mutation sneak in through one of these alone.

Now the rule: at any given time, you can have either *one* mutable reference, or *any number* of shared references, but never both. Many readers OR one writer. Never two writers, never a writer alongside readers. This is sometimes called the *XOR rule* of borrowing.

```rust
let mut a = vec![1, 2, 3];

let r1 = &a;
let r2 = &a;
// let m = &mut a;  // ERROR: cannot borrow as mutable, already borrowed as immutable
println!("{} {}", r1[0], r2[0]);

let m = &mut a;     // OK now: r1 and r2 are no longer used
m.push(4);
// let r3 = &a;     // ERROR: cannot borrow as immutable, already borrowed as mutable
// a.push(99);      // ERROR: even a itself cannot access while m is alive
m.push(5);
```

Worth pausing on that last error: the "one writer" in the XOR rule includes the owner. While `&mut a` exists, even `a` itself cannot read or mutate the value. Exclusive access is fully transferred to the borrower until the borrow ends, so there are never two parties writing at once, just one party at a time holding the right to write.

Why this rule? It eliminates two huge categories of bugs at compile time, and as a bonus unlocks optimizations.

First, *data races*. A data race happens when two threads access the same memory and at least one is writing, with no synchronisation. The XOR rule, applied across thread boundaries, makes data races impossible in safe Rust. There is no way to share a writable pointer with multiple threads without going through synchronisation primitives that respect the rule.

Second, *iterator invalidation*. Modify a collection while iterating it, and other languages give you a range of bad outcomes. C++ treats it as undefined behavior. Python silently skips or repeats elements in a list. Java throws `ConcurrentModificationException` at runtime, only on tested paths. Rust forbids it at compile time: the iterator holds a borrow of the collection, and the compiler refuses to let you mutate the collection while that borrow is alive.

```rust
let mut a = vec![1, 2, 3];
for x in &a {              // borrow of a starts
    if *x == 1 {
        // a.push(99);     // ERROR: cannot mutate a while borrowed
    }
}                          // borrow of a ends
a.push(99);                // OK now
```

Third, *better optimizations*. Because `&mut T` is guaranteed not to alias any other access to the same value, the compiler can keep data in registers across writes, skip reloads, and reorder operations more aggressively. C and C++ compilers cannot do this in general because pointers may alias; the `restrict` keyword exists in C to opt in, and most code does not bother. The XOR rule is not just a safety constraint, it is information the optimizer would otherwise have to assume away.

Now the tradeoff, which is mostly about this rule. The XOR rule is the source of most "fighting the borrow checker" stories, especially when learning. Some patterns natural in other languages become genuinely awkward to express in safe Rust:

- Doubly-linked lists, where each node would need mutable pointers to its neighbours.
- Graphs with shared mutable nodes.
- Observer patterns where many objects hold mutable references to one shared subject.
- Self-referential structs.

In practice the impact is smaller than internet discussion suggests. Doubly-linked lists are in the standard library (`std::collections::LinkedList`), implemented once with `unsafe` so application code never has to. They are also rarely the right structure: `Vec<T>` beats them on most workloads thanks to cache locality. Graphs and self-referential structs do come up, and for those the standard library provides escape valves like `Rc` and `Arc` (covered in later tips) at a small runtime cost. For most code you will not reach for them. For graph-like code you sometimes have to, and that is the friction Rust costs you.

In return, the compiler eliminates an entire class of concurrency bugs that other languages catch with luck, race detectors, or production incidents.

The takeaway: `&mut T` is an exclusive reference, and the XOR rule (many readers OR one writer) is what eliminates data races and iterator invalidation at compile time. The cost is friction with patterns that depend on shared mutable state, which Rust pushes you to express through explicit synchronisation.

🔇 Want to mutate? Sign here, here, and here.
