# ML

This document provides detailed informations about the ML framework, suitable for developing modding tools, adaptable to any problem that requires dynamic instrumentation.

This paper is aimed at C++ developers; basic knowledge of language is assumed.

**Summary**

- [ML](#ml)
  - [Decorators](#decorators)
    - [Tails](#tails)
    - [Chains](#chains)
    - [Optionals](#optionals)
    - [Attribute order](#attribute-order)
    - [Loading order](#loading-order)
  - [Extensions](#extensions)
    - [Inheritance and data members](#inheritance-and-data-members)
    - [Virtuals and pures](#virtuals-and-pures)
    - [Handling multiple extensions](#handling-multiple-extensions)
  - [Dynamic Linkage](#dynamic-linkage)
    - [Runtime binding](#runtime-binding)
    - [Decoration](#decoration)

**Note:** All the examples shown in this document assume that the ML runtime is fully set-up, and that features are available through the `mlrt.h` include file.

## Decorators

The **`decorator`** attribute allows programmers to mark functions as callbacks of other functions, which will be invoked before their base is executed. We call **base** the target function of the decorator.

Decorators are powerful, as they're integrated with the language, and can catch errors at compile time which would otherwise cause fatal issues later on.

Here's an example of *function decoration*:

```cpp
int add(int a, int b)
{
    return a + b;
}

[[decorator(::add)]]
int addDecorator(int a, int b)
{
    printf("\"add()\" got called!\n");
    printf("a: %d\n", a);
    printf("b: %d\n", b);
    return;
}
```

Multiple decorators for the same function are allowed:

```cpp
[[decorator(::add)]]
int add1(int a, int b)
{
    printf("Hello from add1()!\n");
}

[[decorator(::add)]]
int add2(int a, int b)
{
    printf("Hello from add2()!\n");
}
```

Calling the base is as simple as... calling the base:

```cpp
[decorator(::add)]
int deco(int a, int b)
{
    // TODO: be fancy
    ::add(a, b);
}
```

### Tails

If we must inspect the return value of an arbitrary function, we can set a tail decorator.

Tail decorators (or just "**tails**") are quite the opposite of normal decorators: once the base has been executed, the return value is propagated to all of the tails.

A quick example is shown below for the aforementioned function `add()`:

```cpp
[[tail, decorator(::add)]]
void addTail(int* ret)
{
    printf("Sum: %d\n", *ret);
}
```

Tails are void functions, as they do not return anything. The return value of the call is passed as a pointer (unless it already is a pointer). Syntax sugars are provided for C++, namely `tail_const` and `tail_mut`:

```cpp
std::string getName() { return "Peter"; }

[[tail, decorator(::getName)]]
void tailRead(mlrt::tail_const<std::string> name)
{
    printf("Old name: %s\n", name.c_str());
}

[[tail, decorator(::getName)]]
void tailWrite(mlrt::tail_mut<std::string> name)
{
    name = "Joe";
}
```

Like decorators, we can have multiple tails for the same function. One does not imply the other: for any function we could have 1 decorator and 1 tail, 2 decorators and no tails, 3 tails and no decorators, etc.

Adding a tail to an overloaded function might become problematic. In this case we can set the target function type in the tail attribute:

```cpp
bool target(int a, int b);
bool target(double a, double b);

[[tail(bool(int, int)), decorator(::target)]]
void targetIntTail(mlrt::tail_const<bool> ret) { /* ... */ }

[[tail(bool(double, double)), decorator(::target)]]
void targetDoubleTail(mlrt::tail_const<bool> ret) { /* ... */ }
```

### Chains

The most attentive readers may have noticed that [decorator](#decorators) examples lack an expression for the `return` statement, if any.

Decorators and tails both depend on a chain, distinct for every target. They can be added and/or removed from this chain, given that it's not **locked**.

Chain locks become very useful when some decorators make destructive changes to the state of the program. This is the case, for example, of a decorator freeing a buffer object, passed as an argument: 

```cpp
int* f() { return new int[3]; }

[[tail, decorator(::f)]]
void tail1(mlrt::tail_mut<int*> p)
{
    delete[] p;
}

[[tail, decorator(::f)]]
void tail2(mlrt::tail_mut<int*> p)
{
    p[0] = 0; // Crash!
}
```

Other decorators might be expecting a valid object, and this would cause undefined behaviour (and, in most cases, a crash of the whole program).

To maintain the program in a well defined state, decorators can request a chain lock, by using the `locking` attribute. Once a chain has been locked, the decorator is **always guaranteed** to be the last callback invoked; though, this only succeeds if the chain is not locked yet.

Decorators and tails have separate chains, as they work differently; locking one does not lock the other, and vice-versa.

If the decorator chain is locked, the target function is not called; instead, the return value becomes the value paired with the return keyword from the decorator. Tails are still invoked.
Locking the tail chain only prevents the addition of other tails. The target function is still called.

```cpp
void* alg(int* x);

[[decorator(::alg)]]
void* algFree(int* x)
{
    printf("Value of x: %d\n", *x);
}

[[locking, decorator(::alg)]]
void* algLocked(int* x)
{
    // Other decorators might rely on x
    // Locking is necessary
    delete x;

     // Return value needed
    return nullptr;
}

[[tail, decorator(::alg)]]
void algTailFree(mlrt::tail_const<void*> ret)
{
    // Tails are still invoked
    assert(ret == nullptr);
}

[[locking, tail, decorator(::alg)]]
void algTailLocked(mlrt::tail_mut<void*> ret) 
{
    if (ret)
    {
        free(ret);
        ret = nullptr;
    }
}
```

### Optionals

In general, when a decorator fails to load, the mod as a whole gets unloaded. Sometimes a decorator is not necessary for a mod to work (for example, decorating another mod, which [may not be installed](#dynamic-linkage)): it's possible to mark a decorator as **`optional`**, so that even if it's not loaded the mod keeps working as intended:

```cpp
void f();

// Might or might not be loaded
[[optional, decorator(::f)]]
void d() { /* ... */ }

[[optional, tail, decorator(::f)]]
void t() { /* ... */ }
```

### Attribute order

`tail`, `locking`, `optional` all go **before** `decorator`.

### Loading order

The loading order of decorators is as follows:

1. Decorators
2. Locked decorators
3. Tails
4. Locked tails

It is strongly recommended to separate decorators from own code, and to keep them in their own translation unit.

## Extensions

Decoration of record methods is possible through **extensions**. Most of the following examples have classes as targets, but structs and unions can be extended aswell.

```cpp
class Base
{
public:
    int x() const { return 0; }
};

class [[extension(::Base)]]
Extension
{
    [[decorator(x)]]
    int xDeco() const
    {
        printf("Hello from method decorator!\n"); 
    }

    [[locking, decorator(x)]]
    int xLocked() const
    {
        return super()->x() + 1;
    }

    [[locking, tail, decorator(x)]]
    void xTail(int* ret)
    {
        *ret += 5;
    }
};

void checkValue(Base* obj)
{
    assert(obj->x() == 6);
}
```

> **Note**: currently, templates are only partially supported. Trying to extend a dependant base that relies on the extension parameters wont work. This is a work in progress and will be implemented in the future.

```cpp
template <typename T>
class Math
{
    T add(T a, T b);
};

class [[extension(::Math<int>)]]
Extension {}; // works

template <typename T>
class [[extension(::Math<int>)]]
Extension2 {};

template class Extension2<int>; // also works

template <typename T>
class [[extension(::Math<T>)]]
Extension3 {};

template class Extension3<int>; // wont work
```

### Inheritance and data members

Inheritance is allowed. Extensions may declare data members, and they can access members of base classes, regardless of access specifiers.

Inside decorators, the content of the `this` pointer is **undefined**. To access the extension and/or the base, helper functions are provided:

- `self()`: to access extension related members;
- `super()`: to access base related members.

Helpers are `const` by default: the `_mut` variant can be used to write to members and call non-const methods.

As long as helpers are used, extension methods are guaranteed to receive a valid `this` pointer, which will point to the extension instance. Though, it is generally recommended to always rely on helpers.

Keep in mind that helpers have a (small) runtime overhead: it's up to the developers to save them in local, function scope, variables for more efficiency.

```cpp
class [[extension(::Base)]]
Extension
{
    int last;

    Extension(mlrt::ext_init_t)
        : last(0) {}

    [[tail, decorator(x)]]
    void xTail(mlrt::tail_const<int> n)
    {
        self_mut()->last = n;
        super()->x();
    }
};
```

A constructor can be specified to initialize base classes and members. A destructor, instead, can be specified to run code before the extension instance is destroyed.

```cpp
class Data
{
protected:
    void* data;
    Data(void* p) : data(p) {}
};

class [[extension(::Base)]]
Extension : Data
{
    Extension(mlrt::ext_init_t)
        : Data(malloc(0x1000)) {}

    ~Extension()
    {
        free(data);
    }
};
```

Extensions are lazily initialized.

- They are constructed when `self()` is first invoked from a decorator. If `self()` is never invoked, the extension is never initialized.
- They are destroyed once the instance they extend gets destroyed itself.

### Virtuals and pures

Virtual methods may be overloaded, and extension of pure records is allowed; decoration of pure functions is not, though.

```cpp
class Delegate
{
    void* data;

    virtual void update() = 0;
    virtual void setup();
};

class [[extension(::Base)]]
Extension : Delegate
{
    void update() override {}
    void setup() override {}
};
```

This does not mean that virtuals are a drop-in replacement for decoration. For instance, virtual methods from the base are **not** overloaded.

### Handling multiple extensions

As extensions are public by design, given an instance of a base we can access every member of every extension by using `extension_cast`:

> **extension_cast<** *extension type* **>(** *base pointer* **)**

It's possible to switch between extensions by casting them. This cast returns `nullptr` if `Extension` is not an extension of `Base`.

```cpp
void f(Base* b)
{
    if (auto Ext1 = extension_cast<Extension1*>(b))
    {
        (void)Ext1->memberOfExt1;
    }

    if (auto Ext2 = extension_cast<Extension2*>(b))
    {
        (void)Ext2->methodOfExt2();
    }

    // And so on...
}
```

**Note**: RTTI must be enabled for this function to be available.

## Dynamic Linkage

**Dynamic linkage** can be used to reference functions and records that may or may not be present at runtime.

```cpp
[[dynamic("module ID")]]
int f()
{
    return 0;
}

[[dynamic(ML_LOADED_MODULES)]]
void g();

int h()
{
    g();
    return f();
}
```
Dynamics are linked at runtime with the module, if present, that had the same module ID while being loaded by ML. If the `ML_LOADED_MODULES` macro is used, the runtime will lookup the linking symbols in currently loaded modules. If the lookup fails, or no module ID is specified, the dynamics are left unresolved. For more informations, read [here](MLRT.md#loadmodule).

When calling dynamic functions, either one of these things happen:

- If the dynamic has been previously resolved it will jump to the correct function;
- If the dynamic hasn't been resolved yet, but it defines a fallback body (like `f()`), that function is ran;
- If the dynamic hasn't been resolved yet and has no fallback body (like `g()`), the program will warn the user before terminating.

In the case of a dynamic record, every method is marked as dynamic.

```cpp
class [[dynamic]]
DynamicClass
{
public:
    void x();
};
```

An helper function that tells the program whether the given dynamic has been loaded or not is available:

> **has_dynamic(** *address of dynamic* **)**

> **has_dynamic<** *dynamic record type* **>()**

```cpp
void k()
{
    if (has_dynamic(&h))
    {
        //...
    }

    if (has_dynamic<DynamicClass>())
    {
        //...
    }
}
```

**Note**: RTTI must be enabled for this function to be available.

### Runtime binding

Binding dynamics to a different module is made possible by the following helper:

> **bind_dynamic(** *address of dynamic, module id* **)**

> **bind_dynamic<** *dynamic record type* **>(** *module id* **)**

```cpp
class [[dynamic]]
Object
{
    void doTask();
};

void f()
{
    if (bind_dynamic<Object>("my_module"))
    {
        Object obj;
        obj.doTask();
    }
}
```

**Note**: RTTI must be enabled for this function to be available.

### Decoration

Decoration of dynamics happens at load time, if the dynamic has been correctly linked; otherwise, it is deferred until the dynamic is binded to a module.