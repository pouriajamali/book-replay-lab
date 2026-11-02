#pragma once
#include <array>
#include <cstdint>

// Independent normalized-data experiment: two disjoint, fixed tick bands.
// The legacy book.hpp replay contract is deliberately unchanged.
namespace flat_depth {
struct Event { int side; int tick; std::int64_t quantity; };
struct Top {
    int bid{-1}; std::int64_t bid_quantity{0};
    int ask{-1}; std::int64_t ask_quantity{0};
    bool operator==(const Top&) const = default;
};
class Book {
public:
    static constexpr int capacity = 64;
    static constexpr std::int64_t max_quantity = 1000000000;
    bool apply(const Event& e) noexcept {
        if (e.side < 0 || e.side > 1 || e.tick < 0 || e.tick >= capacity ||
            e.quantity < 0 || e.quantity > max_quantity) return false;
        auto& levels = e.side == 0 ? bids_ : asks_;
        int& best = e.side == 0 ? best_bid_ : best_ask_;
        levels[static_cast<std::size_t>(e.tick)] = e.quantity;
        if (e.quantity != 0) {
            if (best == -1 || (e.side == 0 ? e.tick > best : e.tick < best)) best = e.tick;
        } else if (e.tick == best) {
            best = -1;
            if (e.side == 0) {
                for (int i = capacity - 1; i >= 0; --i) if (levels[static_cast<std::size_t>(i)] != 0) { best = i; break; }
            } else {
                for (int i = 0; i < capacity; ++i) if (levels[static_cast<std::size_t>(i)] != 0) { best = i; break; }
            }
        }
        return true;
    }
    Top top() const noexcept {
        return {best_bid_, best_bid_ == -1 ? 0 : bids_[static_cast<std::size_t>(best_bid_)],
                best_ask_, best_ask_ == -1 ? 0 : asks_[static_cast<std::size_t>(best_ask_)]};
    }
    std::int64_t quantity(int side, int tick) const noexcept {
        if (side < 0 || side > 1 || tick < 0 || tick >= capacity) return 0;
        return (side == 0 ? bids_ : asks_)[static_cast<std::size_t>(tick)];
    }
private:
    std::array<std::int64_t, capacity> bids_{};
    std::array<std::int64_t, capacity> asks_{};
    int best_bid_{-1}, best_ask_{-1};
};
inline std::uint64_t consume(std::uint64_t checksum, const Top& top, bool accepted) noexcept {
    // Unsigned wraparound is intentional and defined by C++.
    for (auto value : {static_cast<std::uint64_t>(top.bid + 1), static_cast<std::uint64_t>(top.bid_quantity),
                       static_cast<std::uint64_t>(top.ask + 1), static_cast<std::uint64_t>(top.ask_quantity),
                       static_cast<std::uint64_t>(accepted)}) checksum = (checksum ^ value) * 1099511628211ULL;
    return checksum;
}
}
