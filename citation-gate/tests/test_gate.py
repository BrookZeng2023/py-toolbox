import unittest

from citation_gate import verify_claims

RECORDS = [
    {"id": 1, "text": "明天三点开会"},
    {"id": 2, "text": "报价单已发你邮箱"},
    {"id": 3, "text": "收到，谢谢"},
]


class TestGate(unittest.TestCase):
    def test_valid_claim_survives_with_evidence(self):
        claims = [{"text": "讨论了会议时间", "ids": [1]}]
        kept, rejected = verify_claims(claims, RECORDS)
        self.assertEqual(rejected, 0)
        self.assertEqual(kept[0]["evidence"][0]["quote"], "明天三点开会")

    def test_unknown_id_is_dropped_and_counted(self):
        claims = [{"text": "编造的结论", "ids": [99]}]
        kept, rejected = verify_claims(claims, RECORDS)
        self.assertEqual((kept, rejected), ([], 1))

    def test_mixed_ids_keep_only_resolved(self):
        claims = [{"text": "部分真实", "ids": [1, 99]}]
        kept, rejected = verify_claims(claims, RECORDS)
        self.assertEqual(rejected, 0)  # claim survives: id 1 resolves
        self.assertEqual([e["id"] for e in kept[0]["evidence"]], [1])

    def test_hash_prefixed_and_single_value_ids(self):
        claims = [
            {"text": "a", "ids": "#2"},          # str with '#'
            {"text": "b", "message_ids": 3},     # bare int, alt key
            {"text": "c", "ids": ["x", 1]},      # junk entries ignored
        ]
        kept, rejected = verify_claims(claims, RECORDS)
        self.assertEqual((len(kept), rejected), (3, 0))

    def test_empty_text_or_no_ids_rejected(self):
        claims = [{"text": "  ", "ids": [1]}, {"text": "无引用"}]
        kept, rejected = verify_claims(claims, RECORDS)
        self.assertEqual((kept, rejected), ([], 2))

    def test_category_whitelist_via_predicate(self):
        ok = {"工作", "生活"}
        claims = [
            {"text": "a", "ids": [1], "category": "工作"},
            {"text": "b", "ids": [1], "category": "玄学"},
        ]
        kept, rejected = verify_claims(
            claims, RECORDS, is_valid_claim=lambda c: c.get("category") in ok
        )
        self.assertEqual((len(kept), rejected), (1, 1))

    def test_evidence_cap(self):
        claims = [{"text": "全部引用", "ids": [1, 2, 3]}]
        kept, _ = verify_claims(claims, RECORDS, evidence_cap=2)
        self.assertEqual(len(kept[0]["evidence"]), 2)


if __name__ == "__main__":
    unittest.main()
