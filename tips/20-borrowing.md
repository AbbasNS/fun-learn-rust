🦀 Tip of the day 20: Borrowing, or Reading Without Owning

After tip [19](19-moves.md) you might wonder: if assigning a `Vec` moves it, how do I write a function that just reads one without taking ownership? Cloning works but copies the data. The answer is *borrowing*.

A *reference* is a non-owning pointer to a value. You write `&value` to create one and `&Type` to take one as a parameter:

```rust
fn first(v: &Vec<i32>) -> i32 {
    v[0]
}

let a = vec![1, 2, 3];
let n = first(&a);        // we lend a to the function, we do not give it
println!("{}", a.len());  // a is still valid, we still own it
```

The function signature `&Vec<i32>` says "I accept a reference; I will not take ownership." When you call `first(&a)`, you create a reference and lend it for the duration of the call. The function reads through the reference, returns, and the reference goes away. Your variable `a` was never moved.

This is the key shift: ownership and access are different things. The owner is responsible for cleanup. A borrower can read but is not responsible. Most functions in Rust do not need ownership of their arguments, just the ability to read them. So most function signatures take references.

You can have many shared references at once:

```rust
let a = vec![1, 2, 3];
let r1 = &a;
let r2 = &a;
let r3 = &a;
println!("{} {} {}", r1[0], r2[0], r3[0]);  // all valid, all reading
```

These are read-only borrows. None of them can modify the `Vec`. Multiple readers are safe because no one is changing anything underneath. And while any shared borrow is alive, even the owner cannot mutate the value, otherwise readers could see the data shift underneath them.

The compiler tracks how long each borrow is *actually used*, not just where it was declared. If a reference is created and never used past a certain line, the compiler treats the borrow as having ended at that line, even if the lexical block continues. This feature is called *non-lexical lifetimes*, and it is what makes ordinary code work without ceremony:

```rust
let mut a = vec![1, 2, 3];
let r = &a;
println!("{}", r[0]);  // last use of r, the borrow ends here
a.push(4);             // works, no borrow is alive anymore
```

The reference `r` is in lexical scope until the end of the function, but the compiler sees that `r` is never used after the `println!`. The borrow is treated as ended, and we are free to mutate `a` again.

Now the obvious question: what if the owner goes out of scope while a reference to it is still alive? In C++ that compiles and hands you a dangling pointer. In Rust the compiler refuses:

```rust
let r;
{
    let a = vec![1, 2, 3];
    r = &a;            // ERROR: `a` does not live long enough
}                      // a is dropped here
println!("{}", r[0]);  // r would point into freed memory
```

The compiler tracks how long the borrowed value is alive and how long the reference needs to be alive, and rejects any program where the reference would outlive its target. The mechanism is called *lifetimes*, and we will expand on it in a later tip. For now, trust that the compiler will not let a reference dangle.

What can you do through a `&T`?

- Read fields and call read-only methods on the value.
- Pass it to other functions that accept `&T`.
- Create more shared references from it.

What you cannot do:

- Modify the value (that needs `&mut T`, coming in tip [21](21-mutable-borrowing.md)).
- Move out of the borrow (you do not own it).

The takeaway: `&T` lets you read a value without taking ownership. You can have as many shared references as you want, the compiler tracks how long each is actually used, and it refuses any reference that would outlive its target.

🔇 Feeling overwhelmed? Tempted to crawl back to a GC language? Stop, life is too short for GC pauses. You do not have to remember any of this; the compiler is keeping the list, and will read it back to you, line by line.
