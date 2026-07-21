from assets.contrast_checker import ContrastChecker


def test_contrast_checker_black_and_white():
    ratio = ContrastChecker.get_contrast_ratio("#000000", "#FFFFFF")
    assert ratio == 21.0
    eval_res = ContrastChecker.evaluate_wcag("#000000", "#FFFFFF")
    assert eval_res["aaa_normal"] is True


def test_contrast_checker_low_contrast():
    eval_res = ContrastChecker.evaluate_wcag("#777777", "#888888")
    assert eval_res["aa_normal"] is False
    assert eval_res["ratio"] < 3.0
