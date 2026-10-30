// Independent synthetic command-line adapter.
#include "book.hpp"
#include <iostream>
#include <cstdio>
#if defined(_WIN32)
#include <fcntl.h>
#include <io.h>
#endif

int main() {
#if defined(_WIN32)
    if (_setmode(_fileno(stdin), _O_BINARY) == -1) return 2;
#endif
    demo::Book book;
    for (std::string line; std::getline(std::cin, line);) {
        const auto output = book.process(line);
        if (!output.empty()) std::cout << output << '\n';
    }
    return std::cin.bad() ? 1 : 0;
}
