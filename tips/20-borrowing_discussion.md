🦀 Tip of the day 20 follow-up

Follow-up questions from the discussion on [Tip 20: Borrowing, or Reading Without Owning](20-borrowing.md).

## Does a value's `Drop` cleanup run at the end of the lexical scope, or at the end of the non-lexical lifetime the borrow checker computes?

The tip mentioned two separate behaviors. Non-lexical lifetimes (NLL) let the compiler treat a borrow as ended at its last use, even when the lexical block continues. And types can implement `Drop`, a cleanup function the runtime calls automatically when a value goes away. So which clock does `Drop` run on, the lexical one or the non-lexical one?

`Drop` runs at the end of the lexical scope. NLL has no effect on it.

The two features are decoupled because they answer different questions:

- NLL is a compile-time question: "is this reference still observed past this point?" The borrow checker uses the answer to decide whether a conflicting operation, like a mutation, is allowed.
- `Drop` is a runtime event tied to ownership: "who owns this value, and when does that ownership end?"

A reference going dead does not mean the referent disappears. The owner still owns it. The value is only destroyed when the owner's storage goes away, which happens at one of these points:

- the end of the enclosing block,
- a move out of the binding,
- a reassignment (the old value is dropped on the assignment line),
- an explicit `drop(x)` call.

NLL is not on that list, because it is about reference liveness, not ownership.

There is also a design reason to keep `Drop` lexical. Destructors can have observable side effects: closing files, releasing locks, freeing memory. If they fired at points the borrow checker chose, the exact line a destructor ran on would depend on a subtle compile-time dataflow analysis that can shift as you edit unrelated code. Lexical scope is something you can see by looking at the braces.

It is easy to convince yourself of the wrong answer with an experiment, so watch the setup. Here is the canonical NLL example from [RFC 2094](https://rust-lang.github.io/rfcs/2094-nll.html), the proposal that introduced non-lexical lifetimes:

```rust
fn bar() {
    let mut data = vec!['a', 'b', 'c'];
    let slice = &mut data[..]; // <-+ borrow starts
    capitalize(slice);         //   | last use of slice
    data.push('d');            //   | OK under NLL
    data.push('e');            //   |
    data.push('f');            //   |
}
```

Before NLL this did not compile: the borrow `slice` was considered alive until the closing brace, so the `push` calls conflicted with it. NLL ends the borrow at the call to `capitalize`, and the code compiles. But notice what ended early: the lifetime of the `&mut` reference, not the lifetime of any owned value. Nothing was dropped here, because `slice` is just a reference.

Now suppose you wrap that reference in a struct with a `Drop` impl to watch when cleanup fires:

```rust
struct MutReference<'a, T> {
    inner: &'a mut [T],
}

impl<'a, T> Drop for MutReference<'a, T> {
    fn drop(&mut self) {
        println!("dropped");
    }
}

fn capitalize(data: MutReference<char>) {
    for c in data.inner.iter_mut() {
        *c = c.to_ascii_uppercase();
    }
    println!("end of capitalize");
}

fn main() {
    let mut data = vec!['a', 'b', 'c'];
    let slice = MutReference { inner: &mut data[..] };
    capitalize(slice);
    println!("after capitalize");
    data.push('d');
    data.push('e');
    data.push('f');
    println!("{:?}", data);
}
```

This prints:

```text
end of capitalize
dropped
after capitalize
['A', 'B', 'C', 'd', 'e', 'f']
```

It looks like the drop happened "early," before `after capitalize`, which might suggest NLL drove it. It did not. By passing `slice` by value into `capitalize`, you moved ownership of the `MutReference` into the function. The value's lexical scope is now the body of `capitalize`, so it is dropped at the end of that body. That is the move rule from the list above, not NLL. The experiment changed where the value lives; it did not change the rule for when `Drop` runs.

The takeaway: borrows end at their last use, but owned values are destroyed at the end of their lexical scope (or when moved, reassigned, or explicitly dropped). NLL makes the borrow checker smarter about references; it never moves a destructor.
