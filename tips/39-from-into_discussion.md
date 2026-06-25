🦀 Tip of the day 39 follow-up

Follow-up questions from the discussion on [Tip 39: From and Into, the Conversion Pair](39-from-into.md).

## If I implement `From<A> for B` and `From<B> for C`, can the compiler chain those conversions and turn an `A` straight into a `C`?

No. The compiler will not chain conversions, and there are two separate reasons your `A` does not reach `C`.

First, plain assignment never converts at all. This fails:

```rust
struct A;
struct B;

impl From<A> for B {
    fn from(_: A) -> Self { B }
}

let a = A;
let b: B = a; // error: expected `B`, found `A`
```

Rust does zero implicit conversion on `let` or assignment. Even with `From<A> for B` in scope, you always have to ask for the conversion explicitly with `.into()` or `B::from(a)`. The compiler will helpfully suggest adding `.into()`, but it will not insert it for you.

Second, even once you do ask, `From` and `Into` are not transitive. Add the conversions and try to hop two links at once:

```rust
struct A;
struct B;
struct C;

impl From<A> for B {
    fn from(_: A) -> Self { B }
}
impl From<B> for C {
    fn from(_: B) -> Self { C }
}

let a = A;
let c: C = a.into(); // error: the trait `From<A>` is not implemented for `C`
```

The blanket `Into` impl derives exactly one `Into` from one `From`. It is a single hop: `A: Into<B>` and `B: Into<C>` exist, but `A: Into<C>` does not. The compiler can even see the adjacent `From<B> for C` link and tells you about it in the error, yet it still refuses to bridge `A` to `C`.

That refusal is deliberate. Transitive conversion would make conversion paths ambiguous: if two different routes from `A` to `C` existed, the compiler would have to pick a winner, and silent multi-step coercions are exactly the kind of magic Rust avoids. If you want the two-step conversion, write it out: `let c: C = B::from(a).into();`.

The same one-hop rule applies to the `?` operator. The error conversion that `?` performs calls `From::from` exactly once on the error value, it does not search for a chain. So if a function returns `Result<_, ErrA>` and the enclosing function returns `Result<_, ErrC>`, `?` needs `ErrC: From<ErrA>` directly. Having `From<ErrA> for ErrB` and `From<ErrB> for ErrC` will not satisfy it:

```rust
struct ErrA;
struct ErrB;
struct ErrC;

impl From<ErrA> for ErrB { fn from(_: ErrA) -> Self { ErrB } }
impl From<ErrB> for ErrC { fn from(_: ErrB) -> Self { ErrC } }

fn inner() -> Result<(), ErrA> { Err(ErrA) }

fn outer() -> Result<(), ErrC> {
    inner()?; // error: `?` couldn't convert the error: `From<ErrA>` is not implemented for `ErrC`
    Ok(())
}
```

One `From`, one hop, no exceptions.
