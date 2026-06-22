from app.services.embeddings import cosine_similarity, should_mark_possible_paraphrase


def test_cosine_similarity_identical_vectors():
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_semantic_paraphrase_rule_accepts_synonym_like_signal():
    assert should_mark_possible_paraphrase(cosine_score=0.9, fuzzy_score=60, target_word_count=80)


def test_semantic_paraphrase_rule_rejects_short_text():
    assert not should_mark_possible_paraphrase(cosine_score=0.91, fuzzy_score=60, target_word_count=20)


def test_semantic_paraphrase_rule_rejects_unrelated_text():
    assert not should_mark_possible_paraphrase(cosine_score=0.4, fuzzy_score=40, target_word_count=100)
