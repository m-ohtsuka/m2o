import re
from bs4 import BeautifulSoup

def html_to_org(html_content: str) -> str:
    """
    MastodonのHTML形式のToot本文を、EmacsのOrg-mode形式に変換する。
    - <a>タグ -> [[href][表示テキスト]]
    - <br>タグ -> 改行
    - <p>タグ -> パラグラフ間の改行
    - その他不要なタグ（spanなど） -> 除去してテキストを維持
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. <a> タグを Org-mode のリンク形式に変換
    for a in soup.find_all('a'):
        href = a.get('href', '')
        # メンション内の invisible な要素などを考慮し、get_text() でテキストを取得
        text = a.get_text()
        
        if href:
            # Org-modeのリンク内で [ や ] はエラーの原因になるため置換
            text = text.replace('[', '{').replace(']', '}')
            org_link = f"[[{href}][{text}]]"
            a.replace_with(org_link)
            
    # 2. <br> タグを改行に変換
    for br in soup.find_all('br'):
        br.replace_with('\n')
        
    # 3. <p> タグの後ろに改行を挿入し、タグ自体をアンラップ（解除）
    for p in soup.find_all('p'):
        p.insert_after('\n')
        p.unwrap()
        
    # 4. 残ったすべてのタグ（spanなど）を解除しテキストだけを取得
    text = soup.get_text()
    
    # 5. 不要な複数空行を整理（3つ以上の連続改行を2つに）
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()
