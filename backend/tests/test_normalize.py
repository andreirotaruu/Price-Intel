import unittest

from backend.services.normalize import (
    build_product_profile,
    products_are_comparable,
    profile_similarity_score,
)


class ProductProfileTests(unittest.TestCase):
    def assert_comparison_matrix(self, target_title, accepted, rejected):
        target = build_product_profile(target_title)
        for title in accepted:
            with self.subTest(target=target_title, title=title, expected="accepted"):
                self.assertTrue(
                    products_are_comparable(target, build_product_profile(title))
                )
        for title in rejected:
            with self.subTest(target=target_title, title=title, expected="rejected"):
                self.assertFalse(
                    products_are_comparable(target, build_product_profile(title))
                )

    def test_phone_profile_extracts_identity(self):
        profile = build_product_profile(
            "Apple iPhone 16 Pro 256GB Natural Titanium Unlocked"
        )

        self.assertEqual(profile["category"], "phone")
        self.assertEqual(profile["brand"], "apple")
        self.assertEqual(profile["model"], "iphone 16 pro")
        self.assertEqual(profile["storage"], "256gb")
        self.assertIsNone(profile["variant"])
        self.assertEqual(profile["model_variant"], "pro")
        self.assertEqual(profile["match_key"], "apple iphone 16 pro 256gb")

    def test_phone_model_storage_and_accessories_are_hard_mismatches(self):
        target = build_product_profile("Apple iPhone 16 Pro 256GB Unlocked")

        rejected = (
            "Apple iPhone 16 Pro Max 256GB Unlocked",
            "Apple iPhone 15 Pro 256GB Unlocked",
            "Apple iPhone 16 Pro 128GB Unlocked",
            "Apple iPhone 16 Pro 256GB Case Only",
        )
        for title in rejected:
            with self.subTest(title=title):
                self.assertFalse(
                    products_are_comparable(target, build_product_profile(title))
                )

    def test_console_profile_distinguishes_variants(self):
        target = build_product_profile("Sony PlayStation 5 PS5 Slim Disc Console 1TB")

        self.assertEqual(target["model"], "playstation 5")
        self.assertEqual(target["variant"], "slim")
        self.assertEqual(target["edition"], "disc")
        self.assertEqual(target["storage"], "1tb")
        self.assertEqual(
            target["match_key"], "sony playstation 5 slim disc 1tb"
        )
        self.assertFalse(
            products_are_comparable(
                target,
                build_product_profile("Sony PS5 Slim Digital Edition Console 1TB"),
            )
        )
        self.assertFalse(
            products_are_comparable(target, build_product_profile("Sony PS5 Pro 2TB"))
        )

    def test_sony_headphone_model_numbers_are_canonical(self):
        target = build_product_profile(
            "Sony WH-1000XM5 Wireless Noise Canceling Headphones Black"
        )
        same_model = build_product_profile("Sony WH1000XM5 Bluetooth Headset")
        older_model = build_product_profile("Sony WH-1000XM4 Wireless Headphones")
        earbuds = build_product_profile("Sony WF-1000XM5 Noise Canceling Earbuds")

        self.assertEqual(target["model_number"], "wh-1000xm5")
        self.assertEqual(target["generation"], "5")
        self.assertTrue(products_are_comparable(target, same_model))
        self.assertFalse(products_are_comparable(target, older_model))
        self.assertFalse(products_are_comparable(target, earbuds))

    def test_gpu_profile_still_works(self):
        profile = build_product_profile("NVIDIA RTX 4070 Super 12GB")

        self.assertEqual(profile["category"], "gpu")
        self.assertEqual(profile["model"], "4070")
        self.assertEqual(profile["variant"], "super")
        self.assertEqual(profile["memory"], "12gb")

    def test_similarity_uses_structured_identity_and_generic_fallback(self):
        phone = build_product_profile("Apple iPhone 16 Pro 256GB Unlocked")
        same_phone = build_product_profile("iPhone 16 Pro 256GB Natural Titanium")
        other_phone = build_product_profile("Apple iPhone 15 Pro 256GB")
        generic = build_product_profile("Acme Model 42 blue widget")
        similar_generic = build_product_profile("Acme Model 42 widget used")

        self.assertGreater(
            profile_similarity_score(phone, same_phone),
            profile_similarity_score(phone, other_phone),
        )
        self.assertGreaterEqual(
            profile_similarity_score(generic, similar_generic), 0.62
        )

    def test_phone_listing_matrix(self):
        self.assert_comparison_matrix(
            "Apple iPhone 16 Pro 256GB Unlocked",
            accepted=(
                "iPhone 16 Pro 256GB Natural Titanium",
                "Apple iPhone16 Pro 256 GB Black Titanium Used",
                "Apple iPhone 16 Pro 8GB RAM 256GB Unlocked",
            ),
            rejected=(
                "Apple iPhone 16 Pro Max 256GB Unlocked",
                "Apple iPhone 16 256GB Unlocked",
                "Apple iPhone 15 Pro 256GB Unlocked",
                "Apple iPhone 16 Pro 128GB Unlocked",
                "Case for Apple iPhone 16 Pro 256GB",
                "Apple iPhone 16 Pro 256GB for Parts Only",
                "Apple iPhone 16 Plus 256GB Unlocked",
            ),
        )

    def test_console_listing_matrix(self):
        self.assert_comparison_matrix(
            "Sony PlayStation 5 PS5 Slim Disc Console 1TB",
            accepted=(
                "Sony PS5 Slim Disc Edition 1TB Console",
                "PlayStation5 Slim 1TB Disk Console",
                "Sony PS 5 Slim Console 1TB",
            ),
            rejected=(
                "Sony PS5 Slim Digital Edition 1TB",
                "Sony PlayStation 5 Pro Console 2TB",
                "Sony PS5 Disc Edition 825GB Console",
                "Sony PlayStation 4 Slim 1TB Console",
                "Cooling Stand for PS5 Slim Console",
                "Controller for Sony PlayStation 5",
                "Sony PS5 Slim Disc Console 1TB for Parts",
            ),
        )

    def test_headphone_listing_matrix(self):
        self.assert_comparison_matrix(
            "Sony WH-1000XM5 Wireless Noise Canceling Headphones",
            accepted=(
                "Sony WH1000XM5 Bluetooth Headset Silver",
                "Sony WH 1000XM5 Over Ear Headphones Black",
                "Sony WH-1000XM5 Wireless Headphones with Cable",
            ),
            rejected=(
                "Sony WH-1000XM4 Wireless Headphones",
                "Sony WF-1000XM5 Noise Canceling Earbuds",
                "Sony WH-CH720N Wireless Headphones",
                "Sony WH-1000XM5 Replacement Ear Pads",
                "Carrying Case Only for Sony WH-1000XM5",
                "Replacement Cable for Sony WH1000XM5",
                "Sony WH-1000XM5 Headphones for Parts Only",
            ),
        )


if __name__ == "__main__":
    unittest.main()
