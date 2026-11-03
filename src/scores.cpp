// ─────────────────────────────────────────────────────────────
// scores.cpp — заглушки (patch_39). Реальная логика в patch_44.
// ─────────────────────────────────────────────────────────────
#include "scores.h"

void scores_load(std::vector<ScoreEntry>& out) {
    out.clear();
}

void scores_save(const std::vector<ScoreEntry>& /*in*/) {
}

bool scores_add(std::vector<ScoreEntry>& /*inout*/, const ScoreEntry& /*entry*/) {
    return false;
}

bool scores_would_qualify(const std::vector<ScoreEntry>& in, const ScoreEntry& /*entry*/) {
    return in.size() < 10;
}
