🦀 Tip of the day 31: Closures, the Anonymous Functions That Borrow

Smart pointers boxed you in this week, judging by the comments. There is more to come, but it is Friday, so let us close this week with closures.

You have been using closures since tip [15](15-iterators.md). Iterators take them: `nums.iter().map(|x| x * 2)`. They look like anonymous functions, and that is most of the truth. The other interesting half is what they do with their environment.

A closure is written `|args| body`:

```rust
let add_one = |x| x + 1;
println!("{}", add_one(4));   // 5
```

Types are usually inferred from the first call site. You can write them explicitly when you want to be clear:

```rust
let add_one = |x: i32| -> i32 { x + 1 };
```

The interesting part is what happens when a closure refers to a variable from the surrounding scope:

```rust
let factor = 3;
let multiply = |x| x * factor;   // closure captures `factor`
println!("{}", multiply(4));     // 12
```

The closure captures `factor` automatically. Only variables the body actually references are captured; the rest of the enclosing scope is untouched. Each captured variable is taken in the least restrictive way that compiles:

- If the body only reads it, the closure captures it by shared reference (`&factor`).
- If the body mutates it, the closure captures it by mutable reference (`&mut factor`).
- If the body moves it out (or you write `move`), the closure captures it by value.

A closure that uses several variables can mix capture modes, one per variable.

```rust
let mut count = 0;
let mut increment = || count += 1;   // captures &mut count
increment();
increment();
println!("{}", count);   // 2
```

The compiler picks the looser option that works. You can override it with the `move` keyword, which forces every captured variable to be taken by value:

```rust
let v = vec![1, 2, 3];
let owns_v = move || println!("{:?}", v);
owns_v();
// v cannot be used here, it was moved into the closure
```

You reach for `move` when the closure outlives the scope that created it, otherwise the borrow would dangle. The canonical example is handing a closure to a new thread, which we cover in tip [33](33-arc-mutex.md).

`move` is all-or-nothing: it applies to every captured variable, with no syntax for picking which ones. To keep one as a borrow inside a `move` closure, store a reference to it first and let `move` capture that reference instead (references are `Copy`, so the underlying value stays alive).

Now the trait side. Every closure implements one or more of three traits, based on what its body does with the captures:

- `FnOnce`: callable at least once, may consume its captures.
- `FnMut`: callable repeatedly, may mutate its captures but not consume them.
- `Fn`: callable repeatedly, only reads its captures.

The names look mutually exclusive, but the traits actually nest. `FnOnce` only requires that the closure can be called at least once, which every closure can. `FnMut` adds "callable repeatedly with mutation allowed". `Fn` adds "no mutation". So a read-only closure satisfies all three. A mutating closure satisfies `FnMut` and `FnOnce`. A consuming closure satisfies only `FnOnce`. When a function takes a closure parameter, it asks for the loosest trait that fits, which accepts the widest range of closures:

```rust
fn run_twice(mut f: impl FnMut() -> i32) -> i32 {
    f() + f()
}

let n = 7;
let reader = || n + 1;                            // read-only, implements Fn (and FnMut)
println!("{}", run_twice(reader));                // 16

let mut counter = 0;
let counter_fn = || { counter += 1; counter };    // mutates `counter`, implements FnMut (not Fn)
println!("{}", run_twice(counter_fn));            // 3 (1 + 2)
```

The parameter `mut f: impl FnMut() -> i32` accepts any closure that takes no arguments, returns `i32`, and can be called repeatedly. Because `FnMut` is looser than `Fn`, both `reader` (read-only) and `counter_fn` (mutating) fit. The `mut` on `mut f` is needed because calling an `FnMut` closure requires mutable access to it. (`impl Trait` was introduced in tip [27](27-traits.md).)

Comparison:

- Java: lambdas (since Java 8) require captured local variables to be effectively final, so the local binding cannot be reassigned. The captured object's state, instance fields, and statics can still be mutated freely.
- C++: lambdas (since C++11) require explicit capture syntax (`[&]`, `[=]`, `[x]`, `[&x]`). By-reference captures can mutate the original through the reference. By-value captures are copies that are const by default; the `mutable` keyword removes the const so the lambda can modify its own copies.
- Python: closures can read variables from the enclosing scope freely. Assigning to one inside the closure creates a new local by default; use `nonlocal` to make the assignment modify the outer variable instead.
- JavaScript: closures can both read and write variables from the enclosing scope. Assigning to a captured variable modifies the outer one directly, no keyword required.
- Go: function literals capture variables by reference, with no capture-mode control.
- Rust: capture is automatic and minimal by default; `move` forces by value. The `Fn` family describes how the resulting closure can be called.

The takeaway: a closure is an anonymous function plus its captured environment. Rust captures in the least restrictive way that compiles, the `move` keyword forces by-value capture, and the `Fn` / `FnMut` / `FnOnce` traits describe how the resulting closure can be called.

🔇 You have been missing a lot of tips lately. Ferris is keeping a list. You are on it.
