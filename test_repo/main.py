"""Simple test application."""

def hello(name: str) -> str:
    """"Greet someone.""""
    return f"Hello, {name}!"

def main():
    """"Main entry point.""""
    print(hello("World"))

if __name__ == "__main__":
    main()
