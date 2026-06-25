🦀 Tip of the day 25: Slices, or Borrowing Just Part of Something

Borrowing (tips [20](20-borrowing.md) and [21](21-mutable-borrowing.md)) lets you pass a reference to a whole value. *Slices* let you pass a reference to a range inside a value.

A slice is a borrowed view into a contiguous chunk of elements. The two you will use most:

- `&[T]`: a borrowed sequence of `T`. Backed by a `Vec`, an array, or another slice.
- `&str`: a borrowed UTF-8 string. You met this in tip [23](23-strings.md).

Both are non-owning views: a pointer plus a length. The slice type `[T]` is *unsized*: it has no length at compile time, so it cannot exist on its own and always sits behind a pointer like `&[T]`.

In contrast, an *array* `[T; N]` bakes the length into the type. `[i32; 3]` and `[i32; 4]` are different types, and the value lives inline (on the stack for local variables). That is what makes `&[T]` so flexible as a parameter: one type borrows from arrays of any size, `Vec`s, or other slices.

Mutable forms `&mut [T]` and `&mut str` also exist, though `&mut str` is rarely used: a `str` is UTF-8 bytes underneath, and editing those bytes can easily break the UTF-8 invariant, so the standard library only exposes a few byte-safe operations like ASCII case conversion.

Indexing returns one element by reference; slicing returns a range:

```rust
let v = vec![10, 20, 30, 40, 50];
let one: &i32 = &v[0];          // index: borrow one element
let some: &[i32] = &v[1..4];    // slice: borrow elements 1, 2, 3
```

The range `1..4` is half-open: "from 1, up to but not including 4." Shorthand forms: `&v[..3]` (first three: 0, 1, 2), `&v[2..]` (from 2 to the end), `&v[..]` (the whole thing). The inclusive form is `..=`, so `&v[..=3]` would include index 3.

If the bounds are out of range, or fall mid-character for strings, the program *panics* at runtime:

```rust
let v = vec![1, 2, 3];
let bad = &v[0..10];            // panics: index 10 out of bounds

let s = String::from("héllo");
let half = &s[0..2];            // panics: 'é' is two bytes
```

A panic is a controlled crash, not undefined behavior. You will never read half a character or walk off the end of a buffer. The trade-off is that bad bounds become runtime failures rather than compile errors. To handle the failure instead of panicking, use `v.get(0..10)`, which returns `Option<&[T]>`.

When you write a function that reads a sequence, take `&[T]` rather than `&Vec<T>`. Slice parameters accept more callers at zero cost:

```rust
fn sum(values: &[i32]) -> i32 {
    values.iter().sum()
}

let v = vec![1, 2, 3];
let arr = [10, 20, 30];
sum(&v);             // Vec borrowed as a slice
sum(&arr);           // array borrowed as a slice
sum(&v[1..]);        // sub-slice of the Vec
```

A `&Vec<T>` parameter only accepts `Vec`s. `&[T]` accepts every contiguous sequence, and there is no performance penalty: `&Vec<T>` already dereferences to `&[T]` to do its work. Same logic for `&str` over `&String`.

Rules of thumb for picking a parameter type:

- Reading only? Take `&[T]` or `&str`.
- Modifying elements in place (length stays the same)? Take `&mut [T]`.
- Growing or shrinking the collection? Take `&mut Vec<T>` or `&mut String`.
- Need to consume, store, or return the data? Take `Vec<T>` or `String` by value.

Slices follow the borrow rules from tip [21](21-mutable-borrowing.md). A slice is a borrow, so the XOR rule applies: many shared slices are fine, but you cannot mutate the underlying value while a slice is alive. This is the mechanism that catches iterator invalidation at compile time.

The takeaway: a slice (`&[T]` or `&str`) borrows a contiguous range. Prefer slice parameters for read-only access, and reach for owned `Vec` or `String` only when you actually need ownership.

🔇 A slice is a pointer that knows when to stop.
