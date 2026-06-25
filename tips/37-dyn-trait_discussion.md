🦀 Tip of the day 37 follow-up

Follow-up questions from the discussion on [Tip 37: dyn Trait, Runtime Polymorphism](37-dyn-trait.md).

## If every call on a `dyn Trait` is virtual, is there any way to get a non-virtual call, for example to implement something like the non-virtual interface (NVI) pattern?

Not every call involving a `dyn` is virtual, and NVI maps onto Rust cleanly.

A call is virtual when the function to run is chosen at runtime by looking it up in the vtable. In Rust that happens in exactly one situation: you call a method on a `dyn Trait` value, and that method has a slot in the vtable. So the real question is "what ends up in the vtable?", and the answer is less than you might expect.

These are never virtual:

- Inherent methods (`impl Cat { fn purr(&self) {} }`): they belong to no trait, so they never appear in any vtable. Always static.
- Methods marked `where Self: Sized`: deliberately excluded from the vtable. They can only be called on a concrete type, never through `&dyn`. This is the explicit "this method is not part of the dynamic interface" knob.
- Methods from a different trait supplied by a blanket impl: resolved at compile time.
- Calls a default method makes to `self`'s other trait methods. This is the subtle one, covered below.

Only the trait's own dispatchable methods, invoked through the `&dyn`, go through the vtable.

The subtle case is worth seeing directly:

```rust
trait Animal {
    fn sound(&self) -> &'static str;   // required
    fn announce(&self) {               // provided (default)
        println!("{}", self.sound());
    }
}
```

The `(Cat, Animal)` vtable is built per concrete type. Its `announce` slot points at the default body instantiated for `Cat`. Inside that instantiation `self` has type `&Cat`, so `self.sound()` resolves to `Cat::sound` at compile time: static, and inlinable. So `some_dyn.announce()` is one virtual hop to enter `announce`, and the `sound()` inside it is static. Default methods never cause double dispatch. Called on a concrete `Cat`, even entering `announce` is static.

You can confirm this in the generated code. Calling `announce` on a `&dyn Animal` loads one slot from the vtable and makes a single indirect call. The `Cat` instantiation of the default `announce` body, by contrast, inlines and constant-folds `self.sound()` away entirely, even with `sound` marked `#[inline(never)]`. The inner call is not a second vtable lookup.

That is exactly the template-method shape: fixed logic in `announce`, the variable part isolated in `sound`.

## How do I translate C++'s non-virtual interface (NVI) pattern, a public non-virtual method wrapping a private virtual hook, into Rust?

C++ NVI is a public non-virtual method that does the fixed pre/post work and calls a virtual hook:

```cpp
void process() { log("start"); do_process(); log("done"); }  // non-virtual, fixed
virtual void do_process() = 0;                                // the hook
```

Two ingredients: a fixed, non-overridable public method, and a virtual customization point. Rust gives you both. There are two ways, depending on how strict you need the "non-overridable" guarantee to be.

Version A, a default method. Lightweight and idiomatic:

```rust
trait Widget {
    fn do_process(&self);              // the hook, virtual through &dyn
    fn process(&self) {                // the wrapper
        println!("start");
        self.do_process();             // static inside this instantiation
        println!("done");
    }
}
```

This is how `Iterator` is built: you write `next`, and the dozens of adapters are the fixed interface layered on top. It is clean and common. The one gap versus strict NVI is that an `impl Widget for Foo` may override `process`. Rust has no `final`, so the default-method wrapper is not guaranteed non-overridable.

Version B, a sealed extension trait. This is the faithful, non-overridable form. Put the wrapper on a separate trait, supplied once via a blanket impl:

```rust
trait Widget {                         // the hooks only
    fn do_process(&self);
}

trait WidgetApi {                      // the fixed public interface
    fn process(&self);
}

impl<T: Widget + ?Sized> WidgetApi for T {
    fn process(&self) {
        println!("start");
        self.do_process();             // virtual when T = dyn Widget, static when T = Cat
        println!("done");
    }
}

fn run(w: &dyn Widget) {
    w.process();   // process(): static, resolved to the blanket impl
                   // do_process(): virtual, the single vtable lookup
}
```

The `?Sized` bound on the blanket impl is what lets `T` be `dyn Widget` itself, so the wrapper applies to trait objects as well as concrete types.

You can argue this is a stronger form of NVI than C++ offers. The non-virtuality of the public interface is guaranteed by coherence, no other impl can provide `process`, rather than by you remembering not to mark it `virtual`. The virtual surface is exactly whatever you put in the core trait, and everything built on top of it is static.

You can keep loving the pattern.
