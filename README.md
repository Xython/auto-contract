# auto-contract

Python - design by static contracts. 面向静态合同编程.

创建简便、可扩展的静态合同, 能够静态描述诸多编译期所能确定的合同关系:


项目实现了static contract generator, 使用case class合同作为案例.

满足`case class`协议的类型, 其构造方法的参数以及参数类型和类型成员声明对等.

```python
@contract.Case
class T:
    a: int
    b: int
```

在IDE中可以发现T的构造方法的signature是`(self: T, a: int, b: int)`.

