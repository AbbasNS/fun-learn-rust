🦀 Tip of the day 27 follow-up

Follow-up questions from the discussion on [Tip 27: Traits, the Shape Your Types Can Promise](27-traits.md).

## The orphan rule says either the trait or the type must be local to my crate. So if a type from an external library does not implement `Display`, can I never print it the simple way?

You cannot write `impl Display for SomeForeignType` when both `Display` and the type live in other crates. The compiler stops you, and the error spells out exactly why:

```text
error[E0117]: only traits defined in the current crate can be implemented for types defined outside of the crate
  |
9 | impl Display for String {
  | ^^^^^^^^^^^^^^^^^------
  |                  |
  |                  `String` is not defined in the current crate
  |
  = note: define and implement a trait or new type instead
```

This is the orphan rule doing its job. The official definition: a trait implementation is allowed only if either the trait or at least one of the types in the implementation is defined in the current crate (see the [reference on implementations](https://doc.rust-lang.org/reference/items/implementations.html#orphan-rule)). It exists so two unrelated crates cannot ship conflicting impls for the same trait and type pair, which would make adding a dependency randomly break your build.

But you are not stuck. If a library does not tell you how to print its type, it is reasonable that you supply that decision yourself. The compiler's own hint points at the two standard ways out: define a new type, or define a new trait.

## What does the newtype wrapper pattern look like, and how does it get around the orphan rule?

You define a local struct that wraps the foreign type, then implement `Display` for the wrapper. The wrapper is yours, so the orphan rule is satisfied: the type in the impl is now local.

```rust
struct AsDisplay<'a>(&'a SomeForeignType);

impl<'a> std::fmt::Display for AsDisplay<'a> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "...") // decide here how the foreign value prints
    }
}

println!("{}", AsDisplay(&value));
```

The wrapper holds a reference rather than owning the value, so you avoid copying. The lifetime `'a` just ties the wrapper's borrow to the value it points at.

Here is a fuller version that prints a `Vec<T>` with custom braces. The proxy struct is local, so implementing `Display` on it is allowed:

```rust
use std::fmt::Display;

// A local proxy type we are allowed to implement Display for.
struct DisplayVecProxy<'a, T: Display> {
    reference: &'a Vec<T>,
}

impl<'a, T: Display> Display for DisplayVecProxy<'a, T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{{")?;
        for a in self.reference.iter() {
            write!(f, "{}, ", a)?;
        }
        write!(f, "}}")
    }
}
```

## Can I make `value.display()` produce a printable wrapper instead of constructing it by hand every time?

Yes. Define your own local trait with a method that returns the proxy, then implement that trait for the foreign type. The trait is local, so the orphan rule is happy even though `Vec<T>` is not yours.

```rust
trait Displayable<'a> {
    type Output;
    fn display(&'a self) -> Self::Output;
}

impl<'a, T: Display + 'a> Displayable<'a> for Vec<T> {
    type Output = DisplayVecProxy<'a, T>;
    fn display(&'a self) -> Self::Output {
        DisplayVecProxy { reference: self }
    }
}

fn main() {
    let v = vec![1, 2, 3];
    println!("{}", v.display()); // {1, 2, 3, }
}
```

This combines a few ideas from later tips: an associated type (`type Output`) names the proxy the trait hands back, and the lifetimes make sure the proxy never outlives the `Vec` it borrows. If the lifetimes look intimidating, that is normal; the pattern is worth recognizing even before the syntax feels comfortable.

## Is there a lighter-weight alternative if I do not want a whole proxy type?

There is. This is the extension trait pattern, and it skips the wrapper entirely. Define a local trait with a plain method and implement it directly for the foreign type. The trait is local, the type is foreign, so the orphan rule is satisfied.

```rust
trait PrettyPrint {
    fn fmt_pretty(&self) -> String;
}

impl PrettyPrint for SomeForeignType {
    fn fmt_pretty(&self) -> String {
        // build and return the string however you like
        String::from("...")
    }
}

println!("{}", value.fmt_pretty());
```

The trade-off: this does not make `println!("{}", value)` work directly, because you have not implemented `Display` for the type, only your own method. You call `value.fmt_pretty()` to get the string yourself. In exchange you write much less code, with no proxy struct and no lifetime juggling. Reach for the newtype proxy when you genuinely need `{}` to work, and for the extension trait when an explicit method call is fine.
