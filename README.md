# MIPS32-compiler
MIPS32 Compiler for Computer Architecture.

## Installation

The simplest option is just to use the provided docker. Bear in mind that $PORT is a environment variable that is set by heroku, but it is not for local development. In this case, we assume that $PORT is set to 80.

```
docker build -t mips32-compiler .
docker run --rm --name=mips32-compiler -p=80:80 -t mips32-compiler
```

## API REST

For the sake of scripting, a convenient REST API is exposed.

```
curl -XPOST -F file=@example.asm --silent https://mips32-compiler.herokuapp.com/api/compile_zip | tar xvz
```

This should generate:
- datos (.data memory)
- instrucciones (.text memory)
- programa.lst (.text disassembled version with source code)

## Contact

For any bug report, suggestion or issue, you can contact me (daniel.perdices at uam.es), post here your issue or even fix it yourself and make a pull request.
