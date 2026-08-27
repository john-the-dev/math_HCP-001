#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using Clock = std::chrono::steady_clock;

constexpr int N = 43;
constexpr int M = N * (N - 1) / 2;

struct Five {
  std::array<uint16_t, 10> edges{};
  uint8_t count = 0;
  uint32_t weight = 1;
};

class Search {
 public:
  Search(uint64_t seed, double seconds, int noise_percent, int tenure,
         int restart_after, const std::string& output)
      : rng_(seed), seconds_(seconds), noise_percent_(noise_percent),
        tenure_(tenure), restart_after_(restart_after), output_(output) {
    build_edges();
    build_fives();
    build_seed();
    reset(seed_bits_, false);
    best_bits_ = bits_;
    best_f_ = conflicts_.size();
  }

  int run() {
    const auto start = Clock::now();
    uint64_t next_report = 10000;
    while (elapsed(start) < seconds_ && best_f_ != 0) {
      ++steps_;
      const int selected = choose_edge();
      flip(selected);
      tabu_until_[selected] = steps_ + tenure_ + static_cast<int>(rng_() % 5);

      if (conflicts_.size() < best_f_) {
        best_f_ = conflicts_.size();
        best_bits_ = bits_;
        best_step_ = steps_;
        last_improvement_ = steps_;
        std::cout << "improvement step=" << steps_ << " F=" << best_f_
                  << " elapsed_seconds=" << elapsed(start) << '\n';
        if (best_f_ == 0) write_solution();
      }

      if (steps_ - last_improvement_ > static_cast<uint64_t>(restart_after_)) {
        ++restarts_;
        reset(best_bits_, true);
        last_improvement_ = steps_;
      }
      if (steps_ >= next_report) {
        std::cout << "progress steps=" << steps_ << " F=" << conflicts_.size()
                  << " best_F=" << best_f_ << " restarts=" << restarts_
                  << " elapsed_seconds=" << elapsed(start) << '\n';
        next_report += 10000;
      }
    }
    write_solution();
    std::cout << "summary steps=" << steps_ << " best_step=" << best_step_
              << " best_F=" << best_f_ << " final_F=" << conflicts_.size()
              << " restarts=" << restarts_ << " seed_F=" << seed_f_
              << " five_sets=" << fives_.size()
              << " incidence_entries=" << incidence_entries_
              << " elapsed_seconds=" << elapsed(start) << '\n';
    return best_f_ == 0 ? 0 : 2;
  }

 private:
  std::mt19937_64 rng_;
  double seconds_;
  int noise_percent_;
  int tenure_;
  int restart_after_;
  std::string output_;
  std::array<std::array<int, N>, N> edge_id_{};
  std::array<std::pair<int, int>, M> endpoints_{};
  std::array<uint8_t, M> bits_{};
  std::array<uint8_t, M> seed_bits_{};
  std::array<uint8_t, M> best_bits_{};
  std::array<uint64_t, M> tabu_until_{};
  std::vector<Five> fives_;
  std::array<std::vector<uint32_t>, M> incident_;
  std::vector<uint32_t> conflicts_;
  std::vector<int32_t> conflict_pos_;
  uint64_t incidence_entries_ = 0;
  uint64_t steps_ = 0;
  uint64_t best_step_ = 0;
  uint64_t last_improvement_ = 0;
  uint64_t restarts_ = 0;
  size_t best_f_ = std::numeric_limits<size_t>::max();
  size_t seed_f_ = 0;

  static double elapsed(Clock::time_point start) {
    return std::chrono::duration<double>(Clock::now() - start).count();
  }

  void build_edges() {
    int id = 0;
    for (int u = 0; u < N; ++u) {
      for (int v = u + 1; v < N; ++v) {
        edge_id_[u][v] = edge_id_[v][u] = id;
        endpoints_[id++] = {u, v};
      }
    }
  }

  void build_fives() {
    fives_.reserve(962598);
    for (int a = 0; a < N; ++a)
      for (int b = a + 1; b < N; ++b)
        for (int c = b + 1; c < N; ++c)
          for (int d = c + 1; d < N; ++d)
            for (int e = d + 1; e < N; ++e) {
              Five q;
              const int vs[5] = {a, b, c, d, e};
              int k = 0;
              for (int i = 0; i < 5; ++i)
                for (int j = i + 1; j < 5; ++j)
                  q.edges[k++] = edge_id_[vs[i]][vs[j]];
              const uint32_t qid = fives_.size();
              fives_.push_back(q);
              for (int edge : q.edges) incident_[edge].push_back(qid);
            }
    for (const auto& list : incident_) incidence_entries_ += list.size();
  }

  void build_seed() {
    constexpr std::array<int, 11> s = {1, 2, 7, 10, 12, 13,
                                        14, 16, 18, 20, 21};
    constexpr std::array<int, 19> deleted = {3, 4, 5, 6, 11, 12, 13,
        14, 20, 21, 22, 23, 29, 30, 31, 37, 38, 39, 40};
    for (int id = 0; id < M; ++id) {
      const auto [u, v] = endpoints_[id];
      const int diff = (v - u + N) % N;
      bool value = std::find(s.begin(), s.end(), diff) != s.end() ||
                   std::find(s.begin(), s.end(), (N - diff) % N) != s.end();
      int cycle = -1;
      if (diff == 1) cycle = u;
      if (diff == N - 1) cycle = v;
      if (cycle >= 0 && std::find(deleted.begin(), deleted.end(), cycle) !=
                            deleted.end()) value = false;
      seed_bits_[id] = value;
    }
  }

  static bool violation(uint8_t count) { return count == 0 || count == 10; }

  void add_conflict(uint32_t qid) {
    conflict_pos_[qid] = conflicts_.size();
    conflicts_.push_back(qid);
  }

  void remove_conflict(uint32_t qid) {
    const int pos = conflict_pos_[qid];
    const uint32_t tail = conflicts_.back();
    conflicts_[pos] = tail;
    conflict_pos_[tail] = pos;
    conflicts_.pop_back();
    conflict_pos_[qid] = -1;
  }

  void reset(const std::array<uint8_t, M>& source, bool kick) {
    bits_ = source;
    conflicts_.clear();
    conflict_pos_.assign(fives_.size(), -1);
    tabu_until_.fill(0);
    for (uint32_t qid = 0; qid < fives_.size(); ++qid) {
      auto& q = fives_[qid];
      q.weight = 1;
      q.count = 0;
      for (int edge : q.edges) q.count += bits_[edge];
      if (violation(q.count)) add_conflict(qid);
    }
    if (!kick) {
      seed_f_ = conflicts_.size();
      return;
    }
    const int kick_moves = 8 + static_cast<int>(rng_() % 17);
    for (int i = 0; i < kick_moves && !conflicts_.empty(); ++i) {
      const auto& q = fives_[conflicts_[rng_() % conflicts_.size()]];
      flip(q.edges[rng_() % 10]);
    }
  }

  std::pair<int64_t, int> delta(int edge) const {
    int64_t weighted = 0;
    int raw = 0;
    const int change = bits_[edge] ? -1 : 1;
    for (uint32_t qid : incident_[edge]) {
      const auto& q = fives_[qid];
      const bool before = violation(q.count);
      const bool after = violation(static_cast<uint8_t>(q.count + change));
      if (before != after) {
        const int sign = after ? 1 : -1;
        weighted += sign * static_cast<int64_t>(q.weight);
        raw += sign;
      }
    }
    return {weighted, raw};
  }

  int choose_edge() {
    if (conflicts_.empty()) return 0;
    std::array<bool, M> seen{};
    std::vector<int> candidates;
    const size_t sample = std::min<size_t>(conflicts_.size(), 8);
    for (size_t i = 0; i < sample; ++i) {
      const uint32_t qid = conflicts_[(rng_() + i) % conflicts_.size()];
      for (int edge : fives_[qid].edges) {
        if (!seen[edge]) candidates.push_back(edge);
        seen[edge] = true;
      }
    }
    struct Move { int edge; int64_t weighted; int raw; };
    std::vector<Move> feasible;
    const int ceiling = static_cast<int>(best_f_) + 8;
    for (int edge : candidates) {
      const auto [weighted, raw] = delta(edge);
      const bool aspiration = static_cast<int64_t>(conflicts_.size()) + raw <
                              static_cast<int64_t>(best_f_);
      if (tabu_until_[edge] > steps_ && !aspiration) continue;
      if (static_cast<int>(conflicts_.size()) + raw <= ceiling)
        feasible.push_back({edge, weighted, raw});
    }
    if (feasible.empty()) {
      for (int edge : candidates) {
        const auto [weighted, raw] = delta(edge);
        if (static_cast<int>(conflicts_.size()) + raw <= ceiling)
          feasible.push_back({edge, weighted, raw});
      }
    }
    if (feasible.empty()) {
      int selected = candidates[0];
      int best_raw = std::numeric_limits<int>::max();
      for (int edge : candidates) {
        const auto [weighted, raw] = delta(edge);
        if (raw < best_raw) selected = edge, best_raw = raw;
      }
      return selected;
    }
    if (static_cast<int>(rng_() % 100) < noise_percent_) {
      int min_raw = std::numeric_limits<int>::max();
      for (const auto& move : feasible) min_raw = std::min(min_raw, move.raw);
      std::vector<int> near_best;
      for (const auto& move : feasible)
        if (move.raw <= min_raw + 1) near_best.push_back(move.edge);
      return near_best[rng_() % near_best.size()];
    }

    int selected = feasible[0].edge;
    int64_t best_delta = std::numeric_limits<int64_t>::max();
    int best_raw = std::numeric_limits<int>::max();
    for (const auto& move : feasible) {
      if (move.weighted < best_delta ||
          (move.weighted == best_delta && (move.raw < best_raw ||
           (move.raw == best_raw && (rng_() & 1))))) {
        selected = move.edge;
        best_delta = move.weighted;
        best_raw = move.raw;
      }
    }
    if (best_delta >= 0) {
      for (uint32_t qid : conflicts_) ++fives_[qid].weight;
    }
    return selected;
  }

  void flip(int edge) {
    const int change = bits_[edge] ? -1 : 1;
    bits_[edge] ^= 1;
    for (uint32_t qid : incident_[edge]) {
      auto& q = fives_[qid];
      const bool before = violation(q.count);
      q.count = static_cast<uint8_t>(q.count + change);
      const bool after = violation(q.count);
      if (before && !after) remove_conflict(qid);
      if (!before && after) add_conflict(qid);
    }
  }

  void write_solution() const {
    std::ofstream out(output_);
    if (!out) throw std::runtime_error("cannot write output: " + output_);
    out << "n 43\n";
    for (int edge = 0; edge < M; ++edge) {
      const auto [u, v] = endpoints_[edge];
      if (best_bits_[edge]) out << "e " << u << ' ' << v << '\n';
    }
  }
};

int main(int argc, char** argv) {
  uint64_t seed = 1;
  double seconds = 60;
  int noise = 18;
  int tenure = 7;
  int restart_after = 20000;
  std::string output = "z43_solution.txt";
  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    auto next = [&]() -> std::string {
      if (++i >= argc) throw std::runtime_error("missing value for " + arg);
      return argv[i];
    };
    if (arg == "--seed") seed = std::stoull(next());
    else if (arg == "--seconds") seconds = std::stod(next());
    else if (arg == "--noise") noise = std::stoi(next());
    else if (arg == "--tenure") tenure = std::stoi(next());
    else if (arg == "--restart-after") restart_after = std::stoi(next());
    else if (arg == "--output") output = next();
    else throw std::runtime_error("unknown argument: " + arg);
  }
  Search search(seed, seconds, noise, tenure, restart_after, output);
  return search.run();
}
