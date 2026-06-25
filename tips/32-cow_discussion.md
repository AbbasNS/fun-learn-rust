🦀 Tip of the day 32 follow-up

Follow-up questions from the discussion on [Tip 32: Cow<T>, Borrow Or Own, Decide Later](32-cow.md).

## If a function returns a `Cow` that borrows from its input, does the borrow checker always treat the input as borrowed, even when the value handed back is actually owned at runtime?

Yes, exactly. The borrow checker operates on types and lifetimes, not on runtime values. It cannot peek at which variant the `Cow` actually holds, so it conservatively assumes the return borrows from the input for the full lifetime named in the signature.

Take `normalize` from the tip, whose signature ties the returned `Cow` to the lifetime of `s`:

```rust
let mut dirty = String::from("hello world");
let cleaned = normalize(&dirty);
dirty.push_str("!"); // error: dirty is still borrowed by cleaned
                     // even though cleaned is Owned at runtime
use_it(cleaned);
```

The input `"hello world"` has no `\r`, so at runtime `cleaned` is the `Owned` variant and references nothing. The compiler does not know that. The signature says the result may borrow from `s`, so the borrow holds for as long as `cleaned` is alive.

If you want to sever the link, call `.into_owned()`. It gives you the owned value directly, cloning only if the `Cow` was a borrow:

```rust
let cleaned: String = normalize(&dirty).into_owned();
dirty.push_str("!"); // fine: cleaned no longer references dirty
```

That is the genuine tax of `Cow`: you get runtime flexibility, but static analysis assumes the borrow case. The compiler does not get to be smarter than the signature.
