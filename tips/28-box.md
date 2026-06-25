🦀 Tip of the day 28: Box<T>, Heap Allocation You Can See

Until now, heap allocation in your Rust code has been hidden inside types like `Vec`, `String`, and `HashMap`. Each of them owns a heap buffer behind the scenes; you never had to allocate explicitly. `Box<T>` is the simplest case where you do.

`Box<T>` owns exactly one value of type `T`, allocated on the heap, with the same ownership rules you already know:

```rust
let b = Box::new(String::from("hi"));  // String on the heap, owned by b
println!("{}", *b);                    // explicit deref: prints the String
println!("{}", b.len());               // auto-deref: String::len called through the box
// b is dropped at end of scope, the heap memory is freed
```

The dereference operator `*` gives you the `T` inside. Method calls go a step further: the `Deref` trait lets you call any `T` method directly on the `Box<T>`, no `*` needed. To Rust, `Box<T>` is just an owning pointer, the same size as a `&T` with no refcount or metadata: drop it and the heap allocation goes away, exactly like any other owned value.

Concretely, here is how `Box` behaves under borrows and moves:

```rust
fn print(s: &String)         { println!("{}", s); }
fn append(s: &mut String)    { s.push('!'); }
fn take_box(_: Box<String>)  {}  // receives the Box itself
fn take_string(_: String)    {}  // receives the inner String

let mut b = Box::new(String::from("hi"));
print(&b);          // &Box<String> auto-derefs to &String; b still owns the box
append(&mut b);     // same idea, mutably; b still owns the box
take_box(b);        // moves the Box (one-word pointer copy); b is dead

let b2 = Box::new(String::from("hi"));
take_string(*b2);   // moves the String *out*; b2 is dead, heap slot freed
```

The two move flavors look different in memory (one copies the outer pointer, the other copies the inner value and tears the heap slot down) but leave the original binding in the same state: unusable. The move-out via `*b` does not follow from the rules you've seen so far; it is a `Box`-specific compiler concession, sound only because `Box` is the unique owner. The same expression on other smart pointers is rejected:

```rust
let r = Rc::new(String::from("hi"));
let s: String = *r;   // ERROR: cannot move out of an Rc
```

`Rc<T>`, `Arc<T>`, and `&T` all refuse it, because moving out would invalidate co-owners or borrowed data.

Why would you ever want this? Three motivating cases.

Recursive types. Without `Box`, a recursive enum has no fixed size:

```rust
enum Tree {
    Leaf,
    Node(Tree, Tree),  // ERROR: recursive type `Tree` has infinite size
}
```

Rust needs to know the size of every type it stores by value at compile time, and `Tree` would contain two `Tree`s, each containing two `Tree`s, forever. There is no fixed size to settle on. The fix is to put a `Box` between them:

```rust
enum Tree {
    Leaf,
    Node(Box<Tree>, Box<Tree>),
}
```

A `Box<Tree>` is a pointer to a heap allocation, and a pointer has a known fixed size (one machine word) regardless of what it points to. The enum is now sized; the actual `Tree` lives on the heap.

Bonus: `Box<T>` is never null, so `Option<Box<T>>` is the same size as `Box<T>`. The compiler uses the would-be-null pointer to represent `None` (a niche optimization). This is why idiomatic recursive types often use `Option<Box<Node>>` for children instead of a separate `Leaf` variant.

Trait objects. When you want to store values of different types in the same collection, `Box<dyn Trait>` is how you do it. Full coverage in a later tip on `dyn Trait`. For now, just know that this use case requires `Box`.

Large values. If a struct is huge (say, a kilobyte of fields), you may want it on the heap so stack frames stay small. `Box::new(big_struct)` does that. Like any function call, the argument is evaluated before the call (typically on the stack) and then moved into the heap allocation, so this is no magic shortcut around stack temporaries. In practice this case is rare; most types are small enough that the stack handles them fine.

You almost never use `Box` for plain values like `Box::new(42)`. The motivating cases above are where it earns its keep.

Comparison:

- Java, C#, Python, JavaScript: every object is heap-allocated, accessed through a reference. No choice about where it lives.
- C: explicit `malloc` and `free`. Same idea as `Box`, but you free manually.
- C++: `std::unique_ptr<T>` is the closest analogue. RAII single ownership, moves on assignment.
- Go: the compiler decides via escape analysis whether a value lives on the stack or the heap. You do not control it directly.
- Rust: `Box<T>` lets you opt into heap allocation explicitly, with the same ownership semantics as any other value.

The takeaway: `Box<T>` is the simplest smart pointer. It owns one heap-allocated value with deterministic cleanup. Reach for it when you need recursive types, trait objects, or to move a large value off the stack.

🔇 Came to Rust to escape shared_ptr, weak_ptr, and unique_ptr. Was issued Box, Rc, Arc, RefCell, Cell, and Pin at the door.
