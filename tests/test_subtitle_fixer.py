from app.core.subtitle_fixer import process_line_logic

def test_user_example_1():
    # قبل البدء في تعلم React و Vue.js دعونا نسأل سؤالًا مهمًا
    input_text = "قبل البدء في تعلم React و Vue.js دعونا نسأل سؤالًا مهمًا"
    expected = "React و Vue.js قبل البدء في تعلم\nدعونا نسأل سؤالًا مهمًا"
    assert process_line_logic(input_text) == expected

def test_user_example_2():
    # React هو إطار عمل شهير
    input_text = "React هو إطار عمل شهير"
    expected = "React\nهو إطار عمل شهير"
    assert process_line_logic(input_text) == expected

def test_user_example_3():
    # سنتعلم HTML CSS JavaScript لبناء المواقع
    input_text = "سنتعلم HTML CSS JavaScript لبناء المواقع"
    expected = "HTML CSS JavaScript سنتعلم\nلبناء المواقع"
    assert process_line_logic(input_text) == expected

def test_user_example_4():
    # دعونا نبدأ الدرس الآن
    input_text = "دعونا نبدأ الدرس الآن"
    expected = "دعونا نبدأ الدرس الآن"
    assert process_line_logic(input_text) == expected

def test_mixed_multiple_blocks():
    # A1 E1 A2 E2 A3
    input_text = "بداية First وسط Second نهاية"
    # Line 1: First بداية
    # Remaining: وسط Second نهاية
    # Processing Remaining -> Line 2: Second وسط, Line 3: نهاية
    expected = "First بداية\nSecond وسط\nنهاية"
    assert process_line_logic(input_text) == expected

def test_english_at_end():
    # قبل الدرس React
    input_text = "قبل الدرس React"
    # Anchor: React, Before: قبل الدرس, Block: React, Remaining: None
    expected = "React قبل الدرس"
    assert process_line_logic(input_text) == expected
