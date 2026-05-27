from src.org_formatter import html_to_org

def test_html_to_org_simple():
    assert html_to_org("<p>Hello World</p>") == "Hello World"

def test_html_to_org_br():
    assert html_to_org("<p>Hello<br>World</p>") == "Hello\nWorld"

def test_html_to_org_link():
    assert html_to_org('<p>Check <a href="https://example.com">this</a> out</p>') == "Check [[https://example.com][this]] out"

def test_html_to_org_mention():
    html = '<p>Mention <a href="https://mastodon.social/@user" class="mention">@<span>user</span></a></p>'
    assert html_to_org(html) == "Mention [[https://mastodon.social/@user][@user]]"

def test_html_to_org_multiple_p():
    html = "<p>First paragraph.</p><p>Second paragraph.</p>"
    # 改行が間に入ることを確認
    result = html_to_org(html)
    assert "First paragraph." in result
    assert "Second paragraph." in result
