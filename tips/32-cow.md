🦀 Tip of the day 32: Cow<T>, Borrow Or Own, Decide Later

Last week we saw some std smart pointers; this week we cover another batch. Here is a high-level recap of the family, so you have the full picture of what exists in std.

Already covered:
- `Box` (tip [28](28-box.md)): heap allocation.
- `Rc` (tip [29](29-rc.md)): shared ownership, single-threaded.
- `RefCell` (tip [30](30-refcell.md)): interior mutability, single-threaded.

This week:
- `Cow` (today): borrow-or-own, no commitment upfront.
- `Arc` + `Mutex`: thread-safe versions of `Rc` and `RefCell`.

`Pin` is the last std smart pointer in the family. We cover it at some point after async/await.

Now today's. Sometimes a function does not know in advance whether it will hand back a borrow of its input or build something fresh. The usual workaround is to always allocate (clone the result on the way out) or expose two functions. Rust has a third option: `Cow<'a, T>`, the "clone on write" smart pointer.

`Cow` (in `std::borrow::Cow`) is an enum with two variants:

- `Borrowed(&'a T)`: holds a reference to someone else's data.
- `Owned(...)`: holds an owned counterpart of T (`String` for `str`, `Vec<U>` for `[U]`, and so on).

The two flavors you will use most are `Cow<'a, str>` and `Cow<'a, [T]>`.

```rust
use std::borrow::Cow;

fn normalize(s: &str) -> Cow<'_, str> {
    if s.contains('\r') {
        Cow::Owned(s.replace('\r', ""))   // had to allocate
    } else {
        Cow::Borrowed(s)                   // no work needed
    }
}

let clean = normalize("hello world");        // Borrowed: no allocation
let dirty = normalize("hello\rworld");       // Owned: a new String
```

The caller treats both the same way. `Cow<str>` derefs to `&str`, so methods like `len()` or `contains("x")` work without caring which variant is inside. You only pay an allocation when one was genuinely needed.

For the "borrow first, mutate later" pattern, `Cow` has `.to_mut()`. It returns a `&mut` to the owned value, cloning on the first call if the `Cow` was a borrow:

```rust
let mut c: Cow<str> = Cow::Borrowed("hello");
c.to_mut().push_str(" world");   // clones into String, then mutates
println!("{}", c);                // "hello world"
```

After `to_mut()`, the `Cow` is `Owned`. Subsequent calls do not clone again.

A few honest costs:

- `Cow<'_, T>` is larger than `&T`. For `Cow<str>` and `Cow<[T]>`, niche optimization tucks the discriminant inside, so the total size matches `String` or `Vec<T>` exactly.
- Every deref is a match on the variant. The compiler usually inlines it away, but not always.
- The branching does not vanish. `Cow` unifies the return type, not the work; the producer still decides whether to allocate.

The takeaway: `Cow<'a, T>` is a single type that holds either a borrowed or an owned value, so a function can return either without committing in its signature. Use it to skip allocations that were not actually needed.

🔇 Cow stands for clone-on-write. The mooing is implicit. 🐄

