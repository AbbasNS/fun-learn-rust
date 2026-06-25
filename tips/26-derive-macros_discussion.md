🦀 Tip of the day 26 follow-up

Follow-up questions from the discussion on [Tip 26: Derive Macros, or How to Make the Compiler Write Your Boilerplate](26-derive-macros.md).

## `Ord` is required for sorting, but `f64` only implements `PartialOrd`. Does that mean you cannot sort a `Vec<f64>`, even when the data contains no `NaN`?

You can sort it, just not through the `Ord`-based API. The standard `.sort()` method requires `Ord`, and `f64` cannot implement `Ord` because the trait demands a total order over every possible value, and `NaN` breaks that promise: it compares as incomparable with everything, including itself. The type system has no way to know your particular vector happens to be `NaN`-free, so it refuses `Ord` for the type as a whole.

Instead, reach for `sort_by` and supply a comparator. The standard library gives you [`f64::total_cmp`](https://doc.rust-lang.org/std/primitive.f64.html#method.total_cmp), stable since Rust 1.62, which defines a total order over all floats by placing `NaN` at one end rather than panicking:

```rust
let mut data = vec![3.0_f64, 1.0, 2.0];
data.sort_by(f64::total_cmp);
// or, equivalently:
data.sort_by(|a, b| a.total_cmp(b));
```

If `NaN` truly cannot occur in your domain, the other option is a wrapper type that excludes it. A newtype around `f64` whose constructor rejects `NaN` can soundly implement `Ord`, and then sorting and `BTreeMap` keys work normally. Crates like `ordered-float` provide exactly that. Either way, the burden is on you to prove `NaN` is handled; the language will not assume it.

## In C++, the declaration order of struct fields drives three unrelated things at once: initialization order, memory layout, and the meaning of a defaulted comparison. Designing the order for one use can hurt the others. Does Rust have the same coupling?

Rust decouples all three, so the conflict mostly disappears.

Initialization order is not tied to declaration order at all. A struct literal evaluates its field expressions in the order you write them at the call site, not the order the fields were declared. You can write the fields in any order:

```rust
struct Player { score: u32, name: String }

let p = Player {
    name: get_name(),       // this expression runs first
    score: calculate_score(),
};
```

Memory layout is also decoupled. Under the default representation (`repr(Rust)`), the compiler is free to reorder fields to minimize padding, and it does. The layout is deliberately unspecified, so declaration order tells you nothing about the bytes. If you need a fixed layout, for example to pass a struct across an FFI boundary to C, you opt in with `#[repr(C)]`, which pins the fields to declaration order:

```rust
#[repr(C)]
struct Header {
    version: u8,
    flags: u16,
    length: u32,
}
```

That leaves the third use, comparison. The derived `PartialOrd` and `Ord` do read declaration order: the comparison is lexicographic, top field first. So this is the one place where field order carries semantic weight, and it is the one you noticed in the tip.

The key difference from C++ is that this coupling is shallow and escapable. `#[derive(...)]` only writes a standard implementation; if the lexicographic order it picks is wrong for you, write your own `Ord` by hand and order the fields however you like for layout or readability:

```rust
impl Ord for Player {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        // compare by score regardless of field position
        self.score.cmp(&other.score)
            .then_with(|| self.name.cmp(&other.name))
    }
}
```

So where C++ forces declaration order to serve initialization, layout, and comparison simultaneously, Rust ties initialization to the literal, leaves default layout to the optimizer, and only lets declaration order influence the *derived* comparison, which you are free to override.
