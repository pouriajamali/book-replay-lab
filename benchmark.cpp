// Synthetic in-memory replay API measurement, not exchange/order latency.
#include "book.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <utility>
#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <psapi.h>
#else
#include <sys/resource.h>
#endif

std::optional<std::uint64_t> peak_resident_bytes() {
#if defined(_WIN32)
    PROCESS_MEMORY_COUNTERS info{};
    info.cb = sizeof(info);
    if (!GetProcessMemoryInfo(GetCurrentProcess(), &info, sizeof(info))) return {};
    if (!info.PeakWorkingSetSize) return {};
    return static_cast<std::uint64_t>(info.PeakWorkingSetSize);
#else
    rusage info{};
    if (getrusage(RUSAGE_SELF, &info) != 0 || info.ru_maxrss <= 0) return {};
#if defined(__APPLE__)
    return static_cast<std::uint64_t>(info.ru_maxrss);
#else
    return static_cast<std::uint64_t>(info.ru_maxrss) * 1024;
#endif
#endif
}

int main(int argc, char** argv) {
    try {
        if (argc != 4) throw std::runtime_error("usage: benchmark INPUT SAMPLES WARMUPS");
        const int samples = std::stoi(argv[2]), warmups = std::stoi(argv[3]);
        if (samples < 3 || samples > 1000 || warmups < 0 || warmups > 100)
            throw std::runtime_error("invalid measurement counts");
        std::ifstream input(argv[1]);
        if (!input) throw std::runtime_error("input unavailable");
        std::vector<std::string> records;
        for (std::string line; std::getline(input, line);) if (!line.empty()) records.push_back(line);
        if (input.bad() || records.empty()) throw std::runtime_error("invalid input");
        auto run = [&]() {
            demo::Book book;
            std::uint64_t output_chars = 0;
            std::string last;
            for (const auto& record : records) {
                last = book.process(record);
                output_chars += last.size();
            }
            return std::pair{output_chars, last};
        };
        const auto expected = run();
        for (int i = 0; i < warmups; ++i) if (run() != expected) throw std::runtime_error("unstable warmup");
        std::vector<std::int64_t> durations;
        for (int i = 0; i < samples; ++i) {
            const auto start = std::chrono::steady_clock::now();
            const auto result = run();
            const auto stop = std::chrono::steady_clock::now();
            if (result != expected) throw std::runtime_error("unstable replay output");
            const auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(stop-start).count();
            if (elapsed <= 0) throw std::runtime_error("non-positive timing");
            durations.push_back(elapsed);
        }
        const auto memory = peak_resident_bytes();
        std::cout << "{\"language\":\"C++20\",\"event_count\":" << records.size()
                  << ",\"output_chars\":" << expected.first << ",\"final_state\":\"" << expected.second
                  << "\",\"peak_resident_bytes\":";
        if (memory) std::cout << *memory; else std::cout << "null";
        std::cout << ",\"batch_ns\":[";
        for (std::size_t i=0; i<durations.size(); ++i) std::cout << (i ? "," : "") << durations[i];
        std::cout << "]}\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 2;
    }
}
