🦀 Tip of the day 24: Method Receivers, or Why Your Methods Have Three Different `self`s

Tip [10](10-impl.md) introduced `impl` blocks and mentioned that methods take `self` as their first parameter. It said `&self` is for reading and `&mut self` is for mutating, and promised "more later." This is later.

There are three forms a method receiver can take, and now that you have seen ownership and borrowing, they map cleanly:

- `&self`: borrow the value (shared, read-only).
- `&mut self`: borrow the value mutably (exclusive, can modify).
- `self`: take ownership of the value (the caller's variable becomes invalid).

Same rules as tips [19](19-moves.md), [20](20-borrowing.md), and 21, applied to the implicit first argument of every method.

```rust
struct Counter {
    count: u32,
}

impl Counter {
    fn new() -> Counter { Counter { count: 0 } }   // no receiver: associated function

    fn get(&self) -> u32 {            // borrow, read
        self.count
    }

    fn increment(&mut self) {         // borrow mutably, modify
        self.count += 1;
    }

    fn into_value(self) -> u32 {      // take ownership, consume
        self.count
    }
}

let mut c = Counter::new();
c.increment();               // &mut c happens automatically
println!("{}", c.get());     // &c happens automatically
let total = c.into_value();  // c is moved, can't be used after this
// c.get();                  // ERROR: value used after move
```

The three forms are sugar. `&self` is short for `self: &Self`, `&mut self` for `self: &mut Self`, and plain `self` for `self: Self`. The lowercase `self` is the value; uppercase `Self` is the type being implemented (here, `Counter`). Functions inside `impl` that skip the receiver entirely are *associated functions* (aka static functions), called with `::` instead of `.` because there is nothing to bind. `Counter::new()` is the classic example.

The call site does work for you. When you write `c.increment()`, the compiler matches the receiver shape and inserts `&`, `&mut`, or a move as needed. So `c.increment()`, `(&mut c).increment()`, and `Counter::increment(&mut c)` all compile to the same thing. You almost always write the first.

This auto-adjustment also reaches through wrappers. If you have a `Box<Counter>` and call `.get()` on it, the compiler unwraps the `Box` to find a `Counter` and borrows that. You will see more of this once references and smart pointers are familiar; for now, just know that the dot operator is doing more than it looks.

When to use which receiver:

- `&self` for anything that just reads. Most of your methods.
- `&mut self` for setters, `push`, `sort`, anything that modifies the value.
- `self` for methods that consume or transform the value into something else. `into_iter()` consumes a collection; builder-style chains return a new builder at each step. The naming convention is `into_*` for "consumes self and produces something else."

Most other languages give you a single implicit `this` and trust you not to mutate when you shouldn't. C++ comes closest with trailing `const` for read-only methods, and gets even more ergonomic than Rust with C++23 deducing this. Rust's twist is making all three choices explicit and part of the method's signature, so the compiler can enforce them.

The takeaway: every method takes a receiver, and the three choices (`self`, `&self`, `&mut self`) are just ownership applied to the implicit first parameter. Pick whichever access the method needs, no more.

🔇 If `tip_of_the_day::drop(self)` runs two hours late in an empty office and no one observes, is it still `tip_of_the_day`, or just `Some(tip)`?
