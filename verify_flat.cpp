#include "flat_depth.hpp"
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <vector>
using flat_depth::Event;
using flat_depth::Top;
class Reference {
    std::map<int, std::int64_t> bid, ask;
public:
    bool apply(const Event& e) {
        if (e.side < 0 || e.side > 1 || e.tick < 0 || e.tick >= flat_depth::Book::capacity ||
            e.quantity < 0 || e.quantity > flat_depth::Book::max_quantity) return false;
        auto& levels = e.side == 0 ? bid : ask;
        if (e.quantity == 0) levels.erase(e.tick); else levels[e.tick] = e.quantity;
        return true;
    }
    Top top() const {
        return {bid.empty() ? -1 : bid.rbegin()->first, bid.empty() ? 0 : bid.rbegin()->second,
                ask.empty() ? -1 : ask.begin()->first, ask.empty() ? 0 : ask.begin()->second};
    }
    std::int64_t quantity(int side, int tick) const {
        const auto& levels=side==0 ? bid : ask;
        const auto found=levels.find(tick);
        return found==levels.end() ? 0 : found->second;
    }
};
void require(bool ok, const char* why) { if (!ok) throw std::runtime_error(why); }
void test_edges() {
    flat_depth::Book b;
    require(b.top() == Top{}, "empty book");
    for (auto e : {Event{0,0,1}, {0,63,2}, {1,63,3}, {1,0,4}}) require(b.apply(e), "boundary insert");
    require(b.top() == Top{63,2,0,4}, "best boundaries");
    require(b.apply({0,63,0}) && b.top() == Top{0,1,0,4}, "delete best bid scans downward");
    require(b.apply({1,0,0}) && b.top() == Top{0,1,63,3}, "delete best ask scans upward");
    require(b.apply({0,1,0}), "delete absent is idempotent");
    auto prior=b.top();
    for (auto e : {Event{-1,0,1}, {2,0,1}, {0,-1,1}, {0,64,1}, {1,0,-1}, {1,0,1000000001}}) {
        require(!b.apply(e) && b.top()==prior, "rejection must preserve state");
    }
    require(b.apply({0,0,1000000000}), "max quantity accepted");
    require(b.apply({0,0,0}) && b.apply({1,63,0}) && b.top()==Top{}, "delete to empty");
    for (int s=0;s<2;++s) for (int i=0;i<64;++i) require(b.apply({s,i,i+1}), "fill complete capacity");
    require(b.top()==Top{63,64,0,1}, "full capacity best");
    prior=b.top(); require(!b.apply({0,64,1}) && b.top()==prior, "capacity overflow rejected");
}
std::uint64_t verify(const std::vector<Event>& events) {
    flat_depth::Book b; Reference ref; std::uint64_t sum=1469598103934665603ULL;
    for (const auto& e:events) {
        bool a=b.apply(e), r=ref.apply(e);
        require(a==r && b.top()==ref.top(), "reference state mismatch");
        for(int side=0;side<2;++side) for(int tick=0;tick<64;++tick)
            require(b.quantity(side,tick)==ref.quantity(side,tick),"reference depth mismatch");
        sum=flat_depth::consume(sum,b.top(),a);
    }
    return sum;
}

// Verification only: no clock, allocation probe or benchmark entry point.
int main(int argc, char** argv) {
    try {
        require(argc == 2, "one synthetic correctness fixture required");
        std::ifstream input(argv[1]); require(bool(input), "fixture unavailable");
        std::vector<Event> events; Event event;
        while (input >> event.side >> event.tick >> event.quantity) {
            require(events.size() < 1006, "fixture too large");
            events.push_back(event);
        }
        require(input.eof() && events.size() == 1006, "fixture count mismatch");
        test_edges();
        const auto checksum = verify(events);
        std::cout << "{\"events\":" << events.size()
                  << ",\"depth_slots_per_event\":128,\"edge_checks_passed\":true,\"checksum\":\""
                  << checksum << "\"}\n";
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
