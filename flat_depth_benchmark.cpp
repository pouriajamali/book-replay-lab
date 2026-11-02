#include "flat_depth.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <map>
#include <new>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace allocation_probe { bool enabled = false; std::uint64_t calls = 0; }
// Counts ordinary replaceable new/new[]. Not malloc, aligned allocation or OS memory.
// This single-threaded experiment never constructs an over-aligned hot-path object.
void* operator new(std::size_t n) {
    if (allocation_probe::enabled) ++allocation_probe::calls;
    if (void* p = std::malloc(n == 0 ? 1 : n)) return p;
    throw std::bad_alloc();
}
void* operator new[](std::size_t n) { return ::operator new(n); }
void operator delete(void* p) noexcept { std::free(p); }
void operator delete[](void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }
void operator delete[](void* p, std::size_t) noexcept { std::free(p); }

using Clock = std::chrono::steady_clock;
using flat_depth::Event;
using flat_depth::Top;
std::int64_t elapsed(Clock::time_point a, Clock::time_point b) {
    auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(b-a).count();
    if (ns < 0) throw std::runtime_error("clock moved backwards");
    return ns;
}
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
void array(std::ostream& out,const std::vector<std::int64_t>& values) {
    out << '['; for (std::size_t i=0;i<values.size();++i) {if(i)out<<',';out<<values[i];}out<<']';
}
int main(int argc,char** argv) {
    try {
        if(argc!=4) throw std::runtime_error("usage: flat-benchmark workload.txt samples warmups");
        const int samples=std::stoi(argv[2]), warmups=std::stoi(argv[3]);
        require(samples>=1 && samples<=100 && warmups>=0 && warmups<=20,"invalid counts");
        std::ifstream in(argv[1]); require(bool(in),"cannot open workload");
        std::vector<Event> events; std::string line;
        while(std::getline(in,line)) {
            std::istringstream record(line); Event e; std::string extra;
            require(bool(record >> e.side >> e.tick >> e.quantity) && !(record >> extra),"invalid workload record");
            events.push_back(e);
        }
        require(in.eof() && !events.empty() && events.size()<=1000000,"invalid workload");
        test_edges();const auto expected=verify(events);
        // All dynamic storage is allocated before allocation counting and clocks.
        std::vector<std::int64_t> timings(events.size()*static_cast<std::size_t>(samples));
        std::vector<std::int64_t> empty_clock(timings.size());
        std::vector<std::int64_t> batches(static_cast<std::size_t>(samples));
        std::uint64_t result=0;
        for(int n=0;n<warmups;++n) {
            flat_depth::Book b;std::uint64_t sum=1469598103934665603ULL;
            for(const auto& event:events) {bool accepted=b.apply(event);sum=flat_depth::consume(sum,b.top(),accepted);}
            require(sum==expected,"warmup checksum mismatch");
        }
        allocation_probe::calls=0;allocation_probe::enabled=true;
        void* (*volatile allocate_control)(std::size_t)=&::operator new;
        void (*volatile free_control)(void*)=&::operator delete;
        void* control=allocate_control(1);
        allocation_probe::enabled=false;free_control(control);
        require(allocation_probe::calls==1,"allocation probe control failed");
        allocation_probe::calls=0;
        for(int n=0;n<samples;++n) {
            flat_depth::Book b; std::uint64_t sum=1469598103934665603ULL;
            allocation_probe::enabled=true;
            for(std::size_t i=0;i<events.size();++i) {
                const auto start=Clock::now();
                std::atomic_signal_fence(std::memory_order_seq_cst);
                bool accepted=b.apply(events[i]); const auto top=b.top();
                sum=flat_depth::consume(sum,top,accepted);
                std::atomic_signal_fence(std::memory_order_seq_cst);
                const auto stop=Clock::now();
                timings[static_cast<std::size_t>(n)*events.size()+i]=elapsed(start,stop);
            }
            allocation_probe::enabled=false;
            require(sum==expected,"timed checksum mismatch");result=sum;
        }
        for(auto& t:empty_clock) {auto a=Clock::now();auto z=Clock::now();t=elapsed(a,z);}
        for(int n=0;n<samples;++n) {
            flat_depth::Book b;std::uint64_t sum=1469598103934665603ULL;
            allocation_probe::enabled=true;
            auto start=Clock::now();
            std::atomic_signal_fence(std::memory_order_seq_cst);
            for(const auto& event:events) {bool accepted=b.apply(event);sum=flat_depth::consume(sum,b.top(),accepted);}
            std::atomic_signal_fence(std::memory_order_seq_cst);
            auto stop=Clock::now();
            allocation_probe::enabled=false;
            require(sum==expected,"aggregate checksum mismatch");
            batches[static_cast<std::size_t>(n)]=elapsed(start,stop);
        }
        std::cout << "{\"event_count\":"<<events.size()<<",\"samples\":"<<samples<<",\"warmups\":"<<warmups
                  <<",\"checksum\":\""<<result<<"\",\"reference_checks\":"<<events.size()
                  <<",\"ordinary_new_calls_hot_path\":"<<allocation_probe::calls
                  <<",\"allocation_probe_control_calls\":1"
                  <<",\"book_size_bytes\":"<<sizeof(flat_depth::Book)<<",\"steady_clock_period_num\":"<<Clock::period::num
                  <<",\"steady_clock_period_den\":"<<Clock::period::den<<",\"event_ns\":";
        array(std::cout,timings);std::cout<<",\"empty_clock_pair_ns\":";array(std::cout,empty_clock);
        std::cout<<",\"batch_ns\":";array(std::cout,batches);std::cout<<"}\n";
    } catch(const std::exception& ex) {allocation_probe::enabled=false;std::cerr<<ex.what()<<'\n';return 1;}
}
