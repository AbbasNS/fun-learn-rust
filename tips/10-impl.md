🦀 Tip of the day 10: `impl` -- Where Your Structs Learn New Tricks

Yesterday you learned that structs are just data. No methods, no behavior, just fields. So where do the methods go?

In Rust, data and behavior are separate. You define your data in a `struct`, then attach behavior in an `impl` block.

```rust
struct Player {
    name: String,
    score: u32,
}

impl Player {
    fn increase_score(&mut self, points: u32) {
        self.score += points;
    }

    fn display(&self) {
        println!("{}: {} points", self.name, self.score);
    }
}
```

The `self` parameter:
Every method takes `self` as its first parameter, like Python's explicit `self` or the implicit `this` in Java/C++. The difference is that Rust makes you specify *how* you are using it:
- `&self` means "I just need to read the data"
- `&mut self` means "I need to modify the data"

The compiler uses this to make sure nobody else is messing with your struct at the same time. For now, just remember: read-only gets `&self`, mutation gets `&mut self`.

Associated functions and the `new` convention:

Rust has no constructors. Instead, you write a regular function inside `impl` that returns a new instance. By convention, it is called `new`:

```rust
impl Player {
    fn new(name: String) -> Player {
        Player { name, score: 0 }
    }
}

let alice = Player::new(String::from("Alice"));
```

Notice `new` does not take `self`. It is called with `Player::new(...)`, not `alice.new(...)`. These are called associated functions, similar to static methods in Java.

Why not just write `Player { name, score: 0 }` directly? For that, you need to understand visibility.

Visibility: `pub` and private by default

In Rust, struct fields are private by default. Only code in the same module can access them. `pub` makes a field public.

A module is simply a way to group related code together, like a module in Python or a package in Java. You create one with the `mod` keyword and put code inside the curly braces:

```rust
mod game {
    pub struct Player {
        name: String,   // private: only code inside `game` can see this
        pub score: u32,  // public: anyone can read and set this
    }

    impl Player {
        pub fn new(name: String) -> Player {
            Player { name, score: 0 }
        }

        pub fn name(&self) -> &str {
            &self.name  // public method that gives read access to the private field
        }
    }
}

let alice = game::Player::new(String::from("Alice"));
println!("{}", alice.score);  // Works, score is pub
println!("{}", alice.name()); // Works, going through the method
// println!("{}", alice.name);   // ERROR: field `name` is private
```

`pub` is the only keyword. There is no `private` keyword: no keyword means private. There is no `protected`, no `package-private`, not even C++ `friend` 😢. Just public or private.

This is why the `new` convention exists. If your fields are private, outside code cannot construct the struct directly. `new` becomes the only door in, and you control what comes through it.

You can have multiple `impl` blocks for the same struct. Unusual if you come from other languages, but perfectly legal and sometimes useful for organizing code.

The takeaway: In Rust, data and behavior live in separate blocks. Structs define the shape, `impl` blocks define what it can do.

🔇 Rust's approach to constructors: there are none. Just write a function called `new` and hope everyone follows the convention. It is the Python `ALL_CAPS` constant naming of object creation.
