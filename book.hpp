#pragma once
// Independent synthetic portfolio example. No exchange SDK or employer source.
#include <algorithm>
#include <charconv>
#include <cstdint>
#include <functional>
#include <map>
#include <locale>
#include <sstream>
#include <string>
#include <vector>

namespace demo {
constexpr std::uint32_t maximum = 1'000'000'000;
using BidBook = std::map<std::uint32_t, std::uint32_t, std::greater<>>;
using AskBook = std::map<std::uint32_t, std::uint32_t>;

inline bool number(const std::string& token, std::uint32_t& value, bool zero = false) {
    if (token.empty() || token.size() > 64 || !std::all_of(token.begin(), token.end(), [](unsigned char c) {
            return c >= '0' && c <= '9';
        })) return false;
    const auto result = std::from_chars(token.data(), token.data() + token.size(), value);
    return result.ec == std::errc{} && result.ptr == token.data() + token.size()
        && value <= maximum && (zero || value > 0);
}

class Book {
    BidBook bids_;
    AskBook asks_;
    std::uint32_t sequence_ = 0;
    bool ready_ = false;

    std::string status(const std::string& reason) const {
        std::ostringstream out;
        out << reason << '|' << (ready_ ? 1 : 0) << '|' << sequence_;
        if (bids_.empty()) out << "|-|-";
        else out << '|' << bids_.begin()->first << '|' << bids_.begin()->second;
        if (asks_.empty()) out << "|-|-";
        else out << '|' << asks_.begin()->first << '|' << asks_.begin()->second;
        return out.str();
    }
    std::string halt(const std::string& reason) {
        ready_ = false;
        return status(reason);
    }
public:
    std::string process(const std::string& line) {
        if (std::any_of(line.begin(), line.end(), [](unsigned char c) {
            return !((c >= 32 && c <= 126) || c == '\t' || c == '\n' || c == '\r' || c == '\v' || c == '\f');
        }))
            return halt("INVALID");
        std::istringstream input(line);
        input.imbue(std::locale::classic());
        std::vector<std::string> fields;
        for (std::string field; input >> field;) fields.push_back(field);
        if (fields.empty() || fields[0].starts_with('#')) return {};
        if (fields[0] == "D" && fields.size() == 1) return halt("DISCONNECTED");
        if (fields[0] == "S" && fields.size() == 6) {
            std::uint32_t seq{}, bid{}, bid_qty{}, ask{}, ask_qty{};
            if (!number(fields[1], seq) || !number(fields[2], bid)
                || !number(fields[3], bid_qty) || !number(fields[4], ask)
                || !number(fields[5], ask_qty)) return halt("INVALID");
            if (seq < sequence_) return halt("STALE_SNAPSHOT");
            if (bid >= ask) return halt("CROSSED");
            // Snapshot replacement is atomic after all checks pass.
            bids_ = {{bid, bid_qty}};
            asks_ = {{ask, ask_qty}};
            sequence_ = seq;
            ready_ = true;
            return status("SNAPSHOT");
        }
        if (fields[0] == "U" && fields.size() == 5) {
            std::uint32_t seq{}, price{}, quantity{};
            if (!number(fields[1], seq) || !number(fields[3], price)
                || !number(fields[4], quantity, true)
                || (fields[2] != "B" && fields[2] != "A")) return halt("INVALID");
            if (!ready_) return status("NOT_READY");
            if (seq <= sequence_) return status("STALE");
            if (seq != sequence_ + 1) return halt("GAP");
            // Copy-on-update is deliberate for clarity, NOT a latency design.
            auto next_bids = bids_;
            auto next_asks = asks_;
            bool found = false;
            if (fields[2] == "B") {
                found = next_bids.contains(price);
                if (quantity) next_bids[price] = quantity;
                else next_bids.erase(price);
            } else {
                found = next_asks.contains(price);
                if (quantity) next_asks[price] = quantity;
                else next_asks.erase(price);
            }
            if (!quantity && !found) return halt("UNKNOWN_DELETE");
            if (!next_bids.empty() && !next_asks.empty()
                && next_bids.begin()->first >= next_asks.begin()->first)
                return halt("CROSSED");
            bids_ = std::move(next_bids);
            asks_ = std::move(next_asks);
            sequence_ = seq;
            return status("UPDATE");
        }
        return halt("INVALID");
    }
};
} // namespace demo

