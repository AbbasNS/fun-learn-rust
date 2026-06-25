🦀 Tip of the day 28 follow-up

Follow-up questions from the discussion on [Tip 28: Box<T>, Heap Allocation You Can See](28-box.md).

## Why does `let s = *b` move the value out of a `Box`? It does not seem to follow from the deref and ownership rules covered so far.

You are right to be suspicious: it does not follow. Nothing you have seen so far derives it.

Here is the tempting line of reasoning. `*b` gives you the `T` inside (that is `Deref`), and owned values can be moved around, so `let s = *b` should move the inner value out and consume `b`. The premise is correct: `*b` does expose the `T` through `Deref`. The conclusion is wrong: `Deref` does not hand you ownership, only a view.

For most types that implement `Deref`, `*p` produces a place you can read or borrow, but not move out of. The borrow checker treats it like data you do not own outright. Even when the surrounding `p` is owned, what `Deref` produces is shaped like `&T` or `&mut T`, not a transfer of ownership. So this is rejected:

```rust
let r = Rc::new(String::from("hi"));
let s: String = *r;   // ERROR: cannot move out of an Rc
```

The same answer holds for `Arc<T>`, for the guards you get from `RefCell`, and for anything reached through a `&T`. Moving out would either invalidate co-owners (`Rc`, `Arc`) or move out of borrowed data (`&T`), so the compiler refuses.

`Box<T>` is the one exception. `let s = *b;` compiles. This is not part of the `Deref` story at all; it is a `Box`-specific rule baked into the compiler, sometimes called `DerefMove`. It is sound only because `Box` is the unique owner of its heap slot: take the value out, free the slot, and there are no co-owners left dangling.

It is worth flagging this explicitly as an exception, because it cannot be reproduced for your own types. There is no stable `DerefMove` trait you can implement to get the same behavior. A trait by that name has been [proposed](https://github.com/rust-lang/rfcs/pull/2439) but never stabilized, in part because moving a value off the heap without an extra copy needs compiler support that ordinary types do not have. `Box` gets that support because the compiler treats it as a special primitive rather than as a plain struct.

## Smart pointers like `shared_ptr` and `unique_ptr` are useful. What did Rust actually replace, and what did it leave alone?

It is less about replacing smart pointers and more about resetting expectations.

The common assumption when moving from C++ to Rust goes like this: smart pointers existed to express ownership, the borrow checker now expresses ownership, therefore smart pointers are no longer needed.

The reality is narrower. Only unique ownership got absorbed into the language. The borrow checker mostly displaced `unique_ptr`: single ownership with deterministic cleanup is now the default for every value, so you do not reach for a special type to get it.

Everything else is still here, just rearranged.

`Rc<T>` and `Arc<T>` do the same shared-ownership job that `shared_ptr` does. The borrow checker does not track shared ownership for you, so when you genuinely need it, you still ask for it explicitly.

`Box<T>` took on a different role than `unique_ptr`. Since unique ownership is now free for plain values, `Box` is no longer about expressing ownership at all; it is about heap indirection: recursive types, trait objects, and moving large values off the stack.

And `RefCell` and `Cell` are a category C++ does not really have: interior mutability. They exist only because the borrow checker enforces "many readers or one writer" at compile time, and sometimes you need to defer that check to runtime instead.

So the borrow checker did not abolish smart pointers. It mostly displaced `unique_ptr`, kept shared ownership as an opt-in, repurposed `Box`, and invented a new pointer category along the way.
