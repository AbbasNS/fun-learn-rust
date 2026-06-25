🦀 Tip of the day 36 follow-up

Follow-up questions from the discussion on [Tip 36: Generics and Trait Bounds, Writing Code for All Types](36-generics.md).

## Can a single type parameter require two traits at once, like "must be both `Display` and `Copy`"?

Yes. That is conjunction, and you write it with `+`:

```rust
use std::fmt::Display;

fn print<T: Display + Copy>(x: T) {
    let copy = x; // Copy lets us duplicate it
    println!("{} {}", x, copy);
}
```

The bound `T: Display + Copy` reads as "`T` must implement `Display` and `Copy`." You can chain as many as you need.

Watch the syntax, though. This is a common trap:

```rust
fn print<T: Display, Copy>(x: T) // not what you meant
```

Rust reads the comma as a separator between type parameters, so it parses this as "a type parameter `T` bounded by `Display`, plus a second type parameter named `Copy`." `Copy` here is just a name, not the trait. The compiler will not stop you from naming a type parameter `Copy`, which is exactly why this mistake is quiet. Use `+` to combine bounds on one parameter; use `,` only to separate distinct parameters.

## Can I combine bounds disjunctively, so the function accepts a type that implements `Display` or `Debug`, and picks behavior based on which one it has?

Not directly. Generics in Rust are monomorphized: the compiler stamps out one compiled body per concrete `T`, and that body has to type-check against the bounds you declared, ahead of time. There is no "if `T` happens to implement `Display`, call this, otherwise call that" at the signature level. Rust asks you to commit to a fixed set of capabilities up front.

The usual way around it is a macro, because macros operate on syntax before type checking and can branch on a tag you pass in:

```rust
macro_rules! show {
    ($x:expr; display) => { format!("{}", $x) };
    ($x:expr; debug)   => { format!("{:?}", $x) };
}

let a = show!(42; display);     // "42"
let b = show!(vec![1, 2]; debug); // "[1, 2]"
```

This is exactly how `println!`, `dbg!`, and friends in the standard library handle formatting: the format string is parsed at compile time, and the macro expands to the right calls.

## Is there any real "use `Display` if the type has it, otherwise fall back to `Debug`" mechanism, rather than a macro trick?

There is, but it is unstable and you cannot use it on stable Rust. The feature is called specialization, and it lets a more specific trait implementation override a more general one:

```rust
#![feature(specialization)] // nightly only

use std::fmt::{Debug, Display};

trait Pretty {
    fn pretty(&self) -> String;
}

// Fallback for any Debug type.
impl<T: Debug> Pretty for T {
    default fn pretty(&self) -> String {
        format!("{:?}", self)
    }
}

// Override for types that ALSO implement Display.
impl<T: Debug + Display> Pretty for T {
    fn pretty(&self) -> String {
        format!("{}", self)
    }
}

42_i32.pretty();     // Display impl  -> "42"
vec![1, 2].pretty(); // Vec is Debug only -> "[1, 2]"
```

That is the "use `Display` if available, fall back to `Debug`" pattern you were after.

The catch is that specialization has been unstable for years and is still unstable as of 2026, because the general form is unsound. The standard library uses a restricted, sound subset internally (gated behind `min_specialization`), but neither is available to you on stable.

The core blocker is lifetime-driven specialization. Rust erases lifetimes before code generation: lifetimes are a type-checking artifact and are simply not present in the compiled binary. An implementation chosen based on a lifetime bound would force the compiler to know lifetime information at codegen time, which directly contradicts that erasure. So choosing an implementation by lifetime is the case that breaks soundness, and pinning down a fully sound rule for it is the open problem. The details are tracked in [RFC 1210's tracking issue](https://github.com/rust-lang/rust/issues/31844).

## If I want to temporarily add a bound, say to print something while debugging, do I really have to thread that requirement through every caller?

Often, yes, and it is a real friction point with the monomorphized approach. If a deep function suddenly needs `T: Debug`, that bound has to be satisfiable at every call site, which means it propagates up the call stack: each generic caller that forwards the `T` now has to declare the bound too.

Library authors work around this by pre-declaring common bounds defensively. You will see signatures carrying `T: Clone + Debug + Send + Sync` even when not every method needs all of them, precisely to spare future-them the propagation churn when one of those capabilities later becomes necessary.

A `where` clause keeps that manageable to read, even when several parameters each carry several bounds:

```rust
use std::fmt::Display;

fn process<T, U>(t: T, u: U) -> String
where
    T: Display + Clone,
    U: Display + Default,
{
    format!("{} {}", t, u)
}
```

There is also a design lever. Generic functions tend to drift toward one of two shapes: tightly bounded, which risks rejecting caller types for capabilities they did not actually need, or structured so the deep function never takes `T` directly. A common version of the second shape is to take a closure that the caller produces, which pushes the bound onto the closure and out of your signature. The temporary-debug case is usually not worth restructuring for, but it is worth knowing the bound does not have to live on the generic function forever.

## Can I constrain a trait implementation to a specific const generic value, so a method exists only for, say, 3D vectors?

Yes. Const generics let a type be parameterized by a constant, and you can write implementations for one specific value of that constant. A cross product, for example, is only defined in three dimensions, so you can offer it for `Vector<3>` and nothing else:

```rust
#[derive(Debug)]
struct Vector<const N: usize> {
    coords: [f32; N],
}

impl<const N: usize> Default for Vector<N> {
    fn default() -> Self {
        Self { coords: [0.0; N] }
    }
}

trait CrossProduct {
    fn cross(&self, rhs: &Self) -> Self;
}

trait Absolute {
    fn abs(&self) -> f32;
}

// Cross product exists only for 3D.
impl CrossProduct for Vector<3> {
    fn cross(&self, rhs: &Self) -> Self {
        Self {
            coords: [
                self.coords[1] * rhs.coords[2] - rhs.coords[1] * self.coords[2],
                self.coords[2] * rhs.coords[0] - rhs.coords[2] * self.coords[0],
                self.coords[0] * rhs.coords[1] - rhs.coords[0] * self.coords[1],
            ],
        }
    }
}

// Magnitude exists for every dimension.
impl<const N: usize> Absolute for Vector<N> {
    fn abs(&self) -> f32 {
        self.coords.iter().map(|x| x * x).sum::<f32>().sqrt()
    }
}
```

Now the dimension is part of the type, and the compiler enforces the distinction:

```rust
let x: Vector<3> = Vector { coords: [1.0, 0.0, 0.0] };
let y: Vector<3> = Vector { coords: [0.0, 1.0, 0.0] };
let z = x.cross(&y); // fine, both are 3D

let p: Vector<2> = Vector { coords: [1.0, 0.0] };
println!("{}", p.abs()); // fine, abs works for any N
// p.cross(&p);          // error: cross is not defined for Vector<2>
```

`cross` is reachable only on `Vector<3>`, while `abs` is generic over every `N`. The wrong-dimension call is a compile error, not a runtime check. Const generics have been stable since Rust 1.51 (2021), so none of this needs nightly.
