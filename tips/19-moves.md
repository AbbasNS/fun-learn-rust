🦀 Tip of the day 19: Move Semantics, or Why Assignment Looks Different in Rust

In tip [18](18-ownership.md) we said every value has exactly one owner. That sentence has consequences the moment you assign one variable to another.

In Python or Java, `b = a` makes `b` point to the same object as `a`. They are aliases for one piece of data, and either name can mutate it. In C++, `b = a` calls the copy constructor or copy assignment operator, and the convention is a deep copy: two independent objects. In Go, the answer depends on the type. None of these languages can stop you from writing through one alias while iterating through another.

In Rust, `let b = a` *moves* the value from `a` to `b`. After the move, `a` is no longer valid. The compiler refuses to let you use it.

```rust
let a = vec![1, 2, 3];
let b = a;             // ownership moves from a to b
println!("{}", a[0]);  // ERROR: borrow of moved value: `a`
```

The error is unmissable: `error[E0382]: borrow of moved value`, with help text pointing to the line where the move happened. Rust does not silently alias, and it does not silently copy. Every assignment is one or the other, and the compiler tells you which.

Why move? It is the consequence of the one-owner rule. If `a` and `b` both owned the `Vec`, there would be two owners, and cleanup would run twice (a double free). Rust's solution is the simplest possible: ownership is transferred, the source variable becomes invalid, and exactly one cleanup happens.

Function arguments behave the same way. Passing a value into a function moves it:

```rust
fn consume(v: Vec<i32>) {
    println!("{}", v.len());
}

let a = vec![1, 2, 3];
consume(a);
println!("{}", a.len());  // ERROR: a was moved into consume
```

The function now owns the value, so the caller cannot use `a` after the call. This may feel restrictive, but it makes ownership transfer visible at every call site. Most functions you write will not want ownership; next tip covers how to read a value without taking it.

The exception: types that implement the `Copy` trait. Small, fixed-size, plain types like `i32`, `bool`, `char`, `f64`, and tuples of `Copy` types are copied on assignment instead of moved.

```rust
let x = 42;
let y = x;          // x is copied, not moved
println!("{}", x);  // works, x is still valid
```

Why are these special? Copying a stack value like an `i32` is cheap (just bit duplication) and there is no heap allocation to worry about. Move semantics would buy you nothing and add friction. Owned heap-managing types (`Vec`, `Box`, `HashMap`) are not `Copy`. Move is the default, and it is the safer default.

When you actually want a duplicate of an owning value, you ask explicitly:

```rust
let a = vec![1, 2, 3];
let b = a.clone();   // explicit deep copy, both a and b are now valid
```

`clone()` is always explicit. The cost of a deep copy is visible in the source, not hidden behind an `=`.

Comparison with other languages:

- Python, Java, JS, C#: assignment creates an alias. No copy, no move, just two names for one object. Cheap, but two writers can race or invalidate iterators.
- Go: assignment copies for value types, aliases for slices, maps, and pointers. Implicit, depends on the type.
- C++: assignment copies by default. Move only happens when you write `std::move(x)` and the type has a move constructor. After a move, the source is in a "valid but unspecified state," and reading it is allowed. The compiler does not stop you, and what you get back is whatever the type's move chose to leave behind, usually an empty husk.
- Rust: assignment moves owning types, copies `Copy` types. The compiler tracks moved values and refuses any further use.

The one-owner rule plus move semantics is what makes deterministic cleanup possible. You always know who owns each value, because moves explicitly transfer ownership at every assignment.

The takeaway: assignment in Rust is either a move (ownership transfers, source invalidated) or a copy (cheap stack duplicate). There are no implicit aliases, and the compiler tells you which one happened on every line.

🔇 In Java, mutating a list mid-iteration throws ConcurrentModificationException. In Rust it does not compile. Somehow Java is still the mature, "enterprise" language. That is what marketing, comfort zones, and "nobody got fired for picking Java" will buy you. The compiler had no input.
