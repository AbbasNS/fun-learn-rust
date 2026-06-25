🦀 Tip of the day 23: Strings, or Why There Are Two of Them

In most languages, a string is just a string. You create one, pass it around, and never think about who is responsible for the memory. Rust has two main string types: `String` and `&str`. Now that you have seen ownership, the reason makes sense.

`String` owns its data. It is heap-allocated and growable, and when the variable goes out of scope, the memory is freed. `&str` (pronounced "string slice") is a borrowed view into string data that someone else owns. It can borrow from any source of string bytes: a literal like `"hello"`, an owned `String`, or any other type that can hand out a `&str` view of its contents (a mechanism called `Deref<Target = str>`, covered later). You can read through it, but you cannot change the data behind it, and it cannot outlive the data it points to.

Without a garbage collector, every piece of string data needs an owner. `String` says "I own this." `&str` says "I'm just borrowing a look."

Underneath, `str` is the byte data and `&str` is a borrowed view onto it. `str` itself is unsized: the compiler does not know its length at compile time, so you can never hold a `str` directly. You always work through `&str`, a fat pointer carrying `(address, length)` into a `str` somewhere. `String`, by contrast, is an owned, growable, heap-allocated buffer that owns its bytes outright.

A string literal `"hello"` has type `&'static str`. The bytes live in your compiled binary, and the literal evaluates to a view onto them. We saw `'static` in tip [22](22-lifetimes.md): it lives for the whole program.

```rust
let greeting = "hello";              // &'static str, view onto bytes in the binary
let owned = String::from("hello");   // String, owned heap allocation
```

In practice you will mostly see a `&str` pointing into a literal, into a whole `String` (`&owned`), or into a slice of one (`&owned[..3]`). Whatever the source, the bytes must always be valid UTF-8; you cannot conjure a `&str` from arbitrary bytes.

Converting between them:

```rust
// &str -> String (allocates, copies the data)
let s1 = String::from("hello");
let s2 = "hello".to_string();  // same thing, different style

// String -> &str (free, just borrows existing data)
let s3: &str = &owned;
```

Going from `&str` to `String` copies data into a new heap allocation. Going the other way is just a borrow.

When to use which: if your function only reads a string, take `&str`. It accepts both:

```rust
fn greet(name: &str) {
    println!("Hello, {}!", name);
}

greet("world");                    // &str literal, works
greet(&String::from("Rust"));      // String borrowed as &str, works
```

If your struct needs to hold the data after the function that built it returns, store a `String`:

```rust
struct User {
    name: String,  // User owns this data
}
```

A common confusion: methods like `.replace()`, `.to_lowercase()`, and `.trim()` are callable on `&str`. Doesn't that contradict "read-only"?

No. Those methods do not modify the original. They return a *new* value:

```rust
let s = "Hello";
let lower = s.to_lowercase();    // new String, "hello"
let trimmed = "  hi  ".trim();   // new &str, borrowing into the same data
// s is unchanged
```

Methods that *actually* mutate, like `push_str`, `push`, and `clear`, only exist on `String`, and only when the binding is `mut`:

```rust
let mut s = String::from("hello");
s.push_str(", world");  // s is now "hello, world"
```

So the rule holds. Through `&str` you can read or produce new values, but never change the data behind the borrow.

Strings are UTF-8, and you cannot index them:

```rust
let s = String::from("hello");
// let c = s[0]; // ERROR: String cannot be indexed by integer
```

This surprises everyone. Rust strings are UTF-8, and characters can be 1 to 4 bytes long. `é` is 2 bytes. `🦀` is 4 bytes. If `s[0]` returned one byte, it might give you half a character. Rust refuses to pretend bytes and characters are the same thing.

Be explicit about what you want:

```rust
let s = String::from("hello");
let first_char = s.chars().nth(0);  // Option<char>, iterates characters
let first_byte = s.bytes().nth(0);  // Option<u8>, iterates raw bytes
let slice = &s[0..3];               // "hel", panics if you slice mid-character
```

How other languages handle this: Python, JavaScript, and Java hide encoding from you. You write `s[0]` and get "a character," but Java uses UTF-16 internally, Python uses a flexible encoding, and JS uses UTF-16 with surrogate pairs. C++ `std::string` is a mutable byte sequence that does not enforce UTF-8. Go strings are immutable byte slices, closer to `&str`, and Go is similarly honest about the bytes-vs-characters distinction.

The takeaway: `String` owns string data, `&str` borrows it, and methods on `&str` either read it or hand you back a new value, never mutate the original.

🔇 Good news, this is the easiest of std's half-dozen string types. Bad news, you have not met `OsString` yet.
