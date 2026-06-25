🦀 Tip of the day 30: RefCell<T>, Borrowing at Runtime

Tip [29](29-rc.md) left you with a problem. `Rc<T>` lets multiple owners share a value, but only hands out `&T`. If you need to mutate that shared value, the compile-time XOR rule blocks you, because the compiler cannot prove no other `Rc` is reading right now.

The rule is not wrong, just conservative. Plenty of real programs respect XOR in ways the static checker cannot see: a graph where you mutate one node while traversing another, a callback that briefly re-enters the subject, a tree that rewires itself. The borrows really are disjoint in time, but proving that requires understanding the program's dynamics, not just its types.

`RefCell<T>` is the opt-out. It hides the value behind a runtime borrow counter:

```rust
use std::cell::RefCell;

let cell = RefCell::new(vec![1, 2, 3]);

let r1 = cell.borrow();           // Ref<T>, behaves like &T
let r2 = cell.borrow();           // another shared borrow, fine
println!("{} {}", r1[0], r2[0]);
drop(r1); drop(r2);

let mut m = cell.borrow_mut();    // RefMut<T>, behaves like &mut T
m.push(4);
cell.borrow();                    // PANIC: m is still alive
```

`borrow()` and `borrow_mut()` return guards that bump an internal counter on creation and decrement it on drop. The check happens inside those calls themselves: if a conflicting guard is currently alive, the call panics, before you ever touch the result. You do not need to actually use the new borrow for the panic to fire. Asking for it is the violation.

"But `m.push(4)` is the last line that uses `m`, isn't `m` already gone?" No, and this trips people up. `m` is an owning value with a `Drop` impl, not a reference. Owning values live until the end of their lexical scope, regardless of last use. To release the mutable borrow earlier, call `drop(m)` or wrap it in a smaller `{ ... }` block.

"So I just moved the bug from compile time to runtime?" Sort of, but only for code the compiler would have rejected outright. You assert that this access pattern is actually safe, and pay for the assertion with a cheap runtime check. If you are right, nothing happens, and you get to write a program the static checker would not accept. If you are wrong, you find out immediately and loudly, instead of silently corrupting aliased state.

The most common shape is `Rc<RefCell<T>>`: shared ownership plus shared mutability.

```rust
use std::rc::Rc;
use std::cell::RefCell;

let shared = Rc::new(RefCell::new(vec![1, 2, 3]));
let copy = Rc::clone(&shared);

shared.borrow_mut().push(4);
println!("{:?}", copy.borrow());  // [1, 2, 3, 4]
```

One thing to clear up before the smaller cousin. For ordinary types, `&self` forbids mutation, and that is a real guarantee, not a polite suggestion. `Cell<T>` and `RefCell<T>` are deliberate exceptions, with a name for the pattern: *interior mutability*. From the outside the value still only exposes `&T`; the contents change *inside*. They are not regular types getting away with something. They are built on a language primitive called `UnsafeCell<T>`, the one hole Rust leaves for mutation through `&`. What keeps the exception sound is API discipline.

`Cell` (for `Copy` types) never lends a reference into the cell at all, so nobody can observe a partial swap. `RefCell` does lend references, but tracks them at runtime to enforce XOR.

The use case is when the value is shared through `&T` (often via `Rc`) and you still need to bump something inside it:

```rust
use std::cell::Cell;
use std::rc::Rc;

struct Logger { hits: Cell<u32> }

impl Logger {
    fn log(&self, msg: &str) {                 // forced to be &self
        self.hits.set(self.hits.get() + 1);
        println!("[{}] {}", self.hits.get(), msg);
    }
}

let logger = Rc::new(Logger { hits: Cell::new(0) });
let a = Rc::clone(&logger);
let b = Rc::clone(&logger);
a.log("from a");
b.log("from b");
println!("{}", logger.hits.get());             // 2
```

`log` cannot take `&mut self` because `Rc<Logger>` will never hand one out. Without `Cell`, this design does not type-check. `RefCell<u32>` would also work, but it tracks borrows at runtime for what is just a `u32` swap. `Cell` is the right tool when the field is `Copy` and you only ever replace the value wholesale.

When should you reach for either? As a last resort. The compile-time checker catches mistakes earlier, costs nothing at runtime, and never panics on you in production. Use interior mutability only when you genuinely cannot express the pattern statically.

The takeaway: `RefCell<T>` moves the XOR rule from compile time to runtime so you can write patterns the borrow checker rejects but are still safe, at the cost of a panic if you turn out to be wrong. `Cell<T>` is the lighter sibling for `Copy` fields you want to mutate through `&self`.

🔇 The borrow checker stops you at compile time. RefCell hands the gun back at runtime, in case you came from C and miss it.
