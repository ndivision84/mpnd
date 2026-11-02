#pragma once
// ─────────────────────────────────────────────────────────────
// scores.h — TOP-10 (saves/scores.json).
// ─────────────────────────────────────────────────────────────
#include <string>
#include <vector>
#include "app.h"

void scores_load(std::vector<ScoreEntry>& out);
void scores_save(const std::vector<ScoreEntry>& in);
bool scores_add(std::vector<ScoreEntry>& inout, const ScoreEntry& entry);
bool scores_would_qualify(const std::vector<ScoreEntry>& in, const ScoreEntry& entry);

